from __future__ import annotations

import asyncio

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context
from astrbot.core.utils.active_event_registry import active_event_registry

try:  # 4.30 的会话 override；更早的宿主没有这个模块
    from astrbot.core.session_overrides import update_overrides
except ImportError:  # pragma: no cover - 仅老版本宿主会走到
    update_overrides = None

from .user_persona_store import GroupPersonaStore, PendingHistoryResetStore

DEFAULT_PERSONA_ID = "晓山瑞希"


def mark_session_cleanup_extras(event: AstrMessageEvent | None) -> None:
    """标记当前事件需要清理 LTM 与内置群聊上下文，不直接跨插件导入。"""
    if event is None:
        return
    setter = getattr(event, "set_extra", None)
    if callable(setter):
        setter("_clean_ltm_session", True)
        setter("_clean_group_context_session", True)


async def clear_session_conversation_history(
    context: Context,
    umo: str,
    persona_id: str,
) -> bool:
    """只针对单个 UMO 清空当前对话历史，避免全库读取引发内存暴涨。"""
    try:
        conv_mgr = context.conversation_manager
        cid = await conv_mgr.get_curr_conversation_id(umo)
        if cid:
            await conv_mgr.update_conversation(
                unified_msg_origin=umo,
                conversation_id=cid,
                persona_id=persona_id,
                history=[],
            )
        return True
    except Exception:  # noqa: BLE001
        logger.warning("Persona+ 清空会话 %s 对话历史失败", umo, exc_info=True)
        return False


async def switch_persona(
    *,
    context: Context,
    persona_mgr,
    user_store: GroupPersonaStore,
    event: AstrMessageEvent,
    persona_id: str,
    announce: str | None = None,
    pending_reset_store: PendingHistoryResetStore | None = None,
) -> MessageEventResult | None:
    """切换人格：写入持久化存储，并清空当前对话的历史与人格绑定。

    采用与内置 /reset 一致的做法：先终止该会话正在进行的事件与
    Agent 生成，再把当前对话的历史清空并绑定新人格。若不先终止，
    生成中的请求结束时会把旧人格的历史原样写回，导致"前缀是新
    人格、内容还是旧人格"的错位。
    """
    await persona_mgr.get_persona(persona_id)

    umo = event.unified_msg_origin
    user_store.set(umo, persona_id)

    active_event_registry.stop_all(umo, exclude=event)

    conv_mgr = context.conversation_manager
    cid = await conv_mgr.get_curr_conversation_id(umo)
    if cid:
        await conv_mgr.update_conversation(
            unified_msg_origin=umo,
            conversation_id=cid,
            persona_id=persona_id,
            history=[],
        )
        logger.info(
            "Persona+ %s 已切换至人格 %s（清空当前对话 %s）", umo, persona_id, cid
        )
    else:
        new_cid = await conv_mgr.new_conversation(
            unified_msg_origin=umo,
            persona_id=persona_id,
        )
        # 4.30 生成 prompt 读的是会话 override（runtime=astrbot 时
        # agent.config.persona.persona_id，其他 runtime 为
        # agent.config.persona_id），而 new_conversation 只写对话行、
        # 不写 override。这里复用 update_conversation：源码里
        # persona_id 非空即调用 update_overrides，使新建与已有对话
        # 两条路径口径一致，避免正文/TTS 仍是默认人格。
        try:
            await conv_mgr.update_conversation(
                unified_msg_origin=umo,
                conversation_id=new_cid,
                persona_id=persona_id,
            )
        except Exception:  # noqa: BLE001
            logger.warning(
                "Persona+ %s 新建对话后写入人格 override 失败", umo, exc_info=True
            )
        logger.info("Persona+ %s 已切换至人格 %s（新建对话）", umo, persona_id)

    if pending_reset_store is not None:
        pending_reset_store.discard(umo)
    mark_session_cleanup_extras(event)

    if announce:
        return event.plain_result(announce)
    return None


def _persona_override_target(context: Context, umo: str) -> tuple[str, str | None]:
    """返回 (会话 override 中人格键的路径, 该会话当前实际生效的人格)。

    路径与 ConversationManager.update_conversation 同口径：runtime=astrbot
    用 agent.config.persona.persona_id，其它 runtime 用 agent.config.persona_id。
    生效人格取自已应用 override 的会话配置，与 resolve_selected_persona 一致。
    """
    try:
        conf = context.get_config(umo)
        agent = conf.get("agent", {}) or {}
        agent_cfg = agent.get("config", {}) or {}
        if (agent.get("runtime") or "astrbot") == "astrbot":
            return (
                "agent.config.persona.persona_id",
                (agent_cfg.get("persona") or {}).get("persona_id"),
            )
        return "agent.config.persona_id", agent_cfg.get("persona_id")
    except Exception:  # noqa: BLE001
        return "agent.config.persona.persona_id", None


async def _reset_session_persona(
    context: Context, umo: str, persona_id: str
) -> None:
    """把单个会话的人格重置为 persona_id，不碰对话历史。

    4.30 生效的人格来自会话 override，这里只写 override。对话行的
    persona_id 只是历史快照（构建 prompt 不读它），若为它调用
    update_conversation，宿主会经 conversation_store.read 读出整段
    历史（默认 include_history=True），代价远高于收益，故不处理；
    该会话下次真正切换人格时会一并改写。
    """
    if update_overrides is not None:
        path, effective_persona_id = _persona_override_target(context, umo)
        if effective_persona_id == persona_id:
            return
        await update_overrides(umo, {path: persona_id})
        return
    # 老版本没有会话 override：只能改当前对话的 persona_id（不传 history）
    await context.conversation_manager.update_conversation(
        unified_msg_origin=umo,
        persona_id=persona_id,
    )


async def reset_all_personas(
    *,
    context: Context,
    persona_mgr,
    user_store: GroupPersonaStore,
    exclude_event: AstrMessageEvent | None = None,
    pending_reset_store: PendingHistoryResetStore | None = None,
) -> int:
    """把本插件管理过的人格重置为"晓山瑞希"，并清空持久化存储。

    只重置 user_store 里登记过的会话。不能用
    conversation_manager.get_conversations() 全量枚举：4.30 的实现默认
    include_history=True，会把全库对话历史一次读进内存（生产约 1.2GB），
    还会把 dashboard/webchat 等与人格切换无关的会话一起改掉。

    历史清空策略：
    - 发起重置的当前会话（若原先不在默认人格）立即清空当前对话历史并标记清理 extra；
    - 其余曾切换过人格的会话登记到 pending_reset_store，在其下一条消息进入前懒清理。

    exclude_event：发起重置的事件本身（不终止它，否则它的回复会被吞掉）。
    """
    target_persona_id = DEFAULT_PERSONA_ID

    # 1. 记下本插件管理过的会话，再清空持久化存储。之后每条消息都以
    #    "空存储 + 默认人格" 为目标；个别会话若在中断前没来得及重置，
    #    on_llm_request 的运行时人格对比会在下次请求时补齐。
    managed_items = user_store.get_all()
    managed_umos = sorted(managed_items)
    changed_umos = [
        umo for umo, pid in managed_items.items() if pid and pid != target_persona_id
    ]
    count = user_store.reset_all()

    # 2. 逐个会话重置人格 override；分批让出事件循环，避免长时间独占。
    cleared = 0
    failed = 0
    for index, umo in enumerate(managed_umos, start=1):
        # 终止进行中的生成，避免其结束时把旧人格历史写回；
        # 发起重置的那个事件排除在外，否则它的回复会被一并终止
        active_event_registry.stop_all(umo, exclude=exclude_event)
        try:
            await _reset_session_persona(context, umo, target_persona_id)
            cleared += 1
        except Exception:  # noqa: BLE001
            failed += 1
            logger.error("Persona+ 重置会话 %s 的人格失败", umo, exc_info=True)
        if index % 50 == 0:
            await asyncio.sleep(0)

    # 3. 发起会话立即清历史并标记扩展记忆清理；其余变更会话登记待下次进入时懒清理。
    exclude_umo = getattr(exclude_event, "unified_msg_origin", None)
    pending_umos: list[str] = []
    for umo in changed_umos:
        if exclude_umo and umo == exclude_umo:
            ok = await clear_session_conversation_history(
                context, umo, target_persona_id
            )
            mark_session_cleanup_extras(exclude_event)
            if not ok:
                pending_umos.append(umo)
        else:
            pending_umos.append(umo)
    if pending_reset_store is not None and pending_umos:
        pending_reset_store.add_many(pending_umos)

    logger.info(
        "Persona+ 已重置 %d 个会话存储 → 晓山瑞希（处理 %d 个会话，失败 %d，待懒清历史 %d）",
        count,
        cleared,
        failed,
        len(pending_umos),
    )
    return count
