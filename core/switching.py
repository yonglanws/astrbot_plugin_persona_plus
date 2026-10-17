from __future__ import annotations

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context
from astrbot.core.utils.active_event_registry import active_event_registry

from .user_persona_store import GroupPersonaStore

DEFAULT_PERSONA_ID = "晓山瑞希"


async def switch_persona(
    *,
    context: Context,
    persona_mgr,
    user_store: GroupPersonaStore,
    event: AstrMessageEvent,
    persona_id: str,
    announce: str | None = None,
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
        await conv_mgr.new_conversation(
            unified_msg_origin=umo,
            persona_id=persona_id,
        )
        logger.info("Persona+ %s 已切换至人格 %s（新建对话）", umo, persona_id)

    if announce:
        return event.plain_result(announce)
    return None


async def reset_all_personas(
    *,
    context: Context,
    persona_mgr,
    user_store: GroupPersonaStore,
) -> int:
    """重置所有群聊的人格为"晓山瑞希"，并清空持久化存储。"""

    target_persona_id = DEFAULT_PERSONA_ID

    # 1. 清空持久化存储
    count = user_store.reset_all()

    # 2. 逐个umo遍历，强制更新所有对话的persona_id为"晓山瑞希"
    cleared = 0
    known_origins: set[str] = set()
    try:
        for adapter in context.platform_adapter_manager.iter_adapters():
            if hasattr(adapter, "unified_msg_origin"):
                known_origins.add(adapter.unified_msg_origin)
    except Exception:  # noqa: BLE001
        pass

    for umo in list(known_origins):
        # 终止进行中的生成，避免其结束时把旧人格历史写回
        active_event_registry.stop_all(umo)
        try:
            conversations = await context.conversation_manager.get_conversations(
                unified_msg_origin=umo
            )
        except Exception:  # noqa: BLE001
            continue
        for conv in conversations:
            try:
                await context.conversation_manager.update_conversation(
                    unified_msg_origin=conv.unified_msg_origin,
                    conversation_id=conv.cid,
                    persona_id=target_persona_id,
                    history=[],
                )
                cleared += 1
            except Exception:  # noqa: BLE001
                pass

    logger.info(
        "Persona+ 已重置 %d 个群聊存储 / %d 个对话 → 晓山瑞希",
        count,
        cleared,
    )
    return count
