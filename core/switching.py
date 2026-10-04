from __future__ import annotations

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context

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
    """切换人格：写入持久化存储，并新建一条绑定该人格的对话。

    通过"新建对话"而不是原地修改当前对话来切换，避免与进行中的
    LLM 请求竞态：进行中的请求持有旧对话的快照 cid，其结果只会
    落回旧对话，不会污染新对话；旧对话连同历史保留，可在 WebUI 查看。
    """
    await persona_mgr.get_persona(persona_id)

    umo = event.unified_msg_origin
    user_store.set(umo, persona_id)

    await context.conversation_manager.new_conversation(
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
