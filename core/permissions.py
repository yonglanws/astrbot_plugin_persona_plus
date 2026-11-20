from __future__ import annotations

from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context


def is_admin(context: Context, event: AstrMessageEvent) -> bool:
    """是否管理员：以框架解析出的角色为准，admins_id 仅在无角色信息时回退。

    绑定插件在 replace 模式下会把 sender_id 换成用户绑定的 QQ，
    直接用 sender_id 比对 admins_id 会让普通用户绑定管理员 QQ 后
    通过 /pp 门禁。框架在 WakingStage 里按事件原始 sender_id 解析过
    role（AstrMessageEvent.is_admin 即 role == "admin"，本体的
    PermissionType.ADMIN 也只认它），这里以它为准；只有事件完全
    没有角色信息（第三方合成事件）时才回退到 admins_id 比对。
    """
    role = str(getattr(event, "role", "") or "").strip().lower()
    if role:
        return role == "admin"

    is_admin_fn = getattr(event, "is_admin", None)
    if callable(is_admin_fn):
        try:
            if is_admin_fn():
                return True
        except Exception:  # noqa: BLE001
            pass

    sender_id = str(event.get_sender_id())
    default_conf = context.get_config()
    admin_ids = {str(admin) for admin in default_conf.get("admins_id", [])}
    return sender_id in admin_ids


def check_permission(
    *,
    context: Context,
    event: AstrMessageEvent,
    command: str,
    admin_commands: set[str],
) -> tuple[bool, str]:
    if command in admin_commands and not is_admin(context, event):
        return False, "此操作需要管理员权限。"
    return True, ""
