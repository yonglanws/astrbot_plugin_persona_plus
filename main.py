from __future__ import annotations

import asyncio
import difflib
import os
import time
from pathlib import Path

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star, StarTools

from .core.character_store import CharacterStore
from .core.config import PersonaPlusSettings, load_settings
from .core.image_renderer import compute_display_order, render_persona_switch_list
from .core.permissions import check_permission
from .core.session_flows import GroupScopedSessionFilter
from .core.switching import DEFAULT_PERSONA_ID, reset_all_personas, switch_persona
from .core.user_persona_store import GroupPersonaStore

from astrbot.core.utils.session_waiter import SessionController, session_waiter


class PersonaPlus(Star):
    """专注于人格切换的插件。"""

    EXCLUDE_PERSONA_PREFIX = {"晓山瑞希"}

    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.context = context
        self.persona_mgr = context.persona_manager

        data_dir = StarTools.get_data_dir("astrbot_plugin_persona_plus")
        self.user_store = GroupPersonaStore(data_dir / "group_personas.json")
        self._image_output_dir = str(data_dir / "images")

        self.settings: PersonaPlusSettings
        self.manage_wait_timeout = 60
        self.admin_commands: set[str] = set()
        self.auto_switch_announce = True
        self._tasks: set[asyncio.Task] = set()
        self._active_switches: set[str] = set()
        self._char_store = CharacterStore(Path(__file__).resolve().parent / "characters.json")

        self._load_config(config)
        self._cleanup_old_images()

    def _load_config(self, config) -> None:
        self.settings = load_settings(config)
        self.manage_wait_timeout = self.settings.manage_wait_timeout
        self.admin_commands = self.settings.admin_commands
        self.auto_switch_announce = self.settings.auto_switch_announce

        logger.info(
            "Persona+ 配置加载完成：超时=%ss，管理员指令=%s",
            self.manage_wait_timeout,
            sorted(self.admin_commands),
        )

    def _cleanup_old_images(self, max_age: int = 3600) -> None:
        img_dir = Path(self._image_output_dir)
        if not img_dir.exists():
            return
        now = time.time()
        for f in img_dir.iterdir():
            if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg"):
                age = now - f.stat().st_mtime
                if age > max_age:
                    try:
                        f.unlink()
                    except OSError:
                        pass

    def _get_image_output_dir(self) -> str:
        os.makedirs(self._image_output_dir, exist_ok=True)
        return self._image_output_dir

    @filter.on_astrbot_loaded()
    async def on_astrbot_loaded(self):
        logger.info("Persona+ 已就绪，群聊人格存储：%d 条", len(self.user_store.get_all()))

    # ==================== LLM请求前：应用保存的人格（最高优先级） ====================
    @filter.on_llm_request(priority=999)
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """把持久化存储中的人格应用到本次 LLM 请求。

        快照人格与存储一致时（绝大多数请求）不修改请求——本体在构建
        阶段已把正确人格段连同安全模式、工具约定等提示一起注入
        system_prompt，整体覆盖会把人格段之外的段落全部抹掉。
        仅当快照落后（切换竞态窗口）时走 _align_request_snapshot
        定点对齐，保证新人格必定生效。

        注意：这里只读取存储、修正本次请求，不写"当前对话"，
        避免与切换指令并发时把新人格改回旧值。
        """
        try:
            umo = event.unified_msg_origin
            logger.info("Persona+ [LLM请求] 处理开始: umo=%s", umo)

            saved_persona_id = self.user_store.get(umo)
            target_persona_id = (
                saved_persona_id if saved_persona_id else DEFAULT_PERSONA_ID
            )
            if not saved_persona_id:
                self.user_store.set(umo, target_persona_id)
                logger.info(
                    "Persona+ [LLM请求] %s 不在持久化存储中，已写入默认人格: %s",
                    umo,
                    target_persona_id,
                )

            try:
                persona = await self.persona_mgr.get_persona(target_persona_id)
            except ValueError:
                if target_persona_id == DEFAULT_PERSONA_ID:
                    raise
                logger.warning(
                    "Persona+ [LLM请求] 人格 %s 不存在，回退到默认 %s",
                    target_persona_id,
                    DEFAULT_PERSONA_ID,
                )
                target_persona_id = DEFAULT_PERSONA_ID
                self.user_store.set(umo, target_persona_id)
                persona = await self.persona_mgr.get_persona(target_persona_id)

            event.set_extra("_persona_plus_llm", True)
            event.set_extra("_persona_plus_request_pid", target_persona_id)

            conv = getattr(req, "conversation", None)
            snapshot_persona_id = getattr(conv, "persona_id", None) if conv else None
            if snapshot_persona_id != target_persona_id:
                await self._align_request_snapshot(
                    event, req, target_persona_id, persona
                )
        except Exception as e:
            logger.exception("Persona+ on_llm_request 异常: %s", e)

    async def _align_request_snapshot(
        self,
        event: AstrMessageEvent,
        req: ProviderRequest,
        target_persona_id: str,
        persona,
    ) -> None:
        """对齐构建期读到的旧人格快照与本次请求。

        本体在构建请求时读取 conversation 快照，并以固定格式
        （"\\n# Persona Instructions\\n\\n{prompt}\\n"）注入该人格的
        system_prompt 段与开场对话；若构建与钩子之间发生了人格切换，
        快照仍是旧人格。此时：
        1. 定点替换 system_prompt 中的人格段，保留本体注入的
           安全模式、工具约定等其他段落；
        2. 快照对话仍是当前对话时，把它的 persona_id 修正为存储值
          （切换指令只会新建对话，不会有并发写把这里改回去）；
        3. 把上下文头部的旧人格开场对话替换为新人格的，使本次请求
           等价于"保留历史的人格切换"。快照已不是当前对话时无需落库
          （切换指令已新建对话），只对齐本次请求。
        """
        conv = getattr(req, "conversation", None)
        old_persona_id = getattr(conv, "persona_id", None) if conv else None

        old_persona = None
        if old_persona_id:
            try:
                old_persona = await self.persona_mgr.get_persona(old_persona_id)
            except ValueError:
                old_persona = None

        self._rebase_system_prompt(req, old_persona, persona)

        umo = event.unified_msg_origin
        conv_mgr = self.context.conversation_manager
        try:
            curr_cid = await conv_mgr.get_curr_conversation_id(umo)
            if curr_cid and conv and curr_cid == conv.cid:
                await conv_mgr.update_conversation(
                    unified_msg_origin=umo,
                    conversation_id=conv.cid,
                    persona_id=target_persona_id,
                )
        except Exception:  # noqa: BLE001
            logger.warning(
                "Persona+ [LLM请求] 修正对话 persona_id 失败（不影响本次请求）",
                exc_info=True,
            )

        try:
            contexts = req.contexts
            if isinstance(contexts, list):
                req.contexts = self._rebase_begin_dialogs(
                    contexts, old_persona, persona
                )
                logger.info(
                    "Persona+ [LLM请求] 请求快照人格 %s 与目标 %s 不一致，已在本次请求中对齐",
                    old_persona_id,
                    target_persona_id,
                )
        except Exception:  # noqa: BLE001
            logger.warning("Persona+ [LLM请求] 对齐请求上下文失败", exc_info=True)

    @staticmethod
    def _rebase_system_prompt(req: ProviderRequest, old_persona, new_persona) -> None:
        """把 system_prompt 中本体注入的旧人格段替换为新人格段。

        本体以固定格式追加人格段（"\\n# Persona Instructions\\n\\n{prompt}\\n"），
        定点替换可保留安全模式、工具约定等其他段落。任何分支都保证
        新人格 prompt 在场（人格必定切换生效）：
        - 旧人格段能精确定位 → 定点替换；
        - 段在但无法定位（旧人格刚被删/刚被改）→ 全量替换兜底；
        - 本体未注入人格段（[%None]/人格不存在/空 prompt）→ 追加。
        """
        marker = "\n# Persona Instructions\n\n"
        new_section = marker + (new_persona.system_prompt or "") + "\n"
        sp = req.system_prompt or ""

        old_section = None
        if old_persona is not None and old_persona.system_prompt:
            old_section = marker + old_persona.system_prompt + "\n"

        if old_section and old_section in sp:
            sp = sp.replace(old_section, new_section, 1)
        elif marker in sp:
            sp = new_section
        else:
            sp = sp + new_section
        req.system_prompt = sp

    @staticmethod
    def _begin_dialog_entries(persona) -> list[dict]:
        """把 Persona.begin_dialogs 转换为本体注入上下文所用的消息格式。

        与本体 persona_mgr 的处理保持一致：user/assistant 交替、
        附带 _no_save 标记；条数为奇数时视为无效配置整体丢弃。
        """
        dialogs = list(getattr(persona, "begin_dialogs", None) or [])
        if not dialogs or len(dialogs) % 2 != 0:
            return []
        entries = []
        user_turn = True
        for dialog in dialogs:
            entries.append(
                {
                    "role": "user" if user_turn else "assistant",
                    "content": str(dialog),
                    "_no_save": True,
                }
            )
            user_turn = not user_turn
        return entries

    @classmethod
    def _rebase_begin_dialogs(cls, contexts: list, old_persona, new_persona) -> list:
        """把上下文头部的旧人格开场对话替换为新人格的开场对话。

        仅当头部与旧人格开场对话逐条匹配时才替换，防止误删正常历史；
        无法确认时保持原样，由 system_prompt 保证人格生效。
        """
        contexts = list(contexts)
        new_entries = cls._begin_dialog_entries(new_persona)
        old_entries = cls._begin_dialog_entries(old_persona) if old_persona else []
        n = len(old_entries)
        if n == 0:
            # 旧快照没有开场对话（人格为空或无效），直接补上新人格的
            if new_entries:
                contexts[:0] = new_entries
            return contexts
        if len(contexts) >= n and cls._head_matches(contexts[:n], old_entries):
            contexts = contexts[n:]
            if new_entries:
                contexts[:0] = new_entries
        return contexts

    @staticmethod
    def _head_matches(head: list, expected: list[dict]) -> bool:
        """检查上下文头部是否与预期消息逐条一致（只比对 role 与文本内容）。"""
        for msg, want in zip(head, expected):
            if not isinstance(msg, dict) or msg.get("role") != want["role"]:
                return False
            content = msg.get("content")
            if isinstance(content, str):
                if content != want["content"]:
                    return False
            elif isinstance(content, list):
                # 多模态分段：文本部分拼接后一致即视为匹配
                texts = [
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                ]
                if "".join(texts) != want["content"]:
                    return False
            else:
                return False
        return True

    # ==================== 权限工具 ====================
    def check_permission(self, event: AstrMessageEvent, command: str) -> tuple[bool, str]:
        return check_permission(
            context=self.context,
            event=event,
            command=command,
            admin_commands=self.admin_commands,
        )

    def _get_command_prefix(self, event: AstrMessageEvent) -> str:
        conf = self.context.get_config(event.unified_msg_origin)
        wake_prefix = conf.get("wake_prefix", ["/"])
        if isinstance(wake_prefix, list):
            for prefix in wake_prefix:
                prefix_text = str(prefix).strip()
                if prefix_text:
                    return prefix_text
            return "/"
        prefix_text = str(wake_prefix).strip()
        return prefix_text or "/"

    def _switch_help_text(self, event: AstrMessageEvent) -> str:
        pp = f"{self._get_command_prefix(event)}pp"
        return "\n".join(
            [
                "Persona+ 人格切换",
                f" {pp} — 打开人格列表（发送序号选择）",
                f" {pp} 序号/人格ID/别名 — 切换人格",
                " 切换人格 <目标> — 同上",
                " 重置人格 — 所有会话恢复默认人格（管理员）",
                "",
                "提示：群聊内所有用户共享一个人格；无法识别的输入将被忽略。",
            ]
        )

    # ==================== 人格列表渲染 ====================
    async def _render_persona_switch_list(self) -> tuple[str, list[str]]:
        personas = await self.persona_mgr.get_all_personas()
        if not personas:
            return "当前没有人格，请先在控制台或通过指令创建。", []

        persona_ids = [p.persona_id for p in personas]
        lines = ["请直接发送序号选择人格：", ""]
        for idx, persona in enumerate(personas, start=1):
            lines.append(f"  {idx}. {persona.persona_id}")
        lines.append("")
        lines.append(f"共 {len(personas)} 个人格，回复「取消」可退出。")
        return "\n".join(lines), persona_ids

    # ==================== 人格引用解析 ====================
    @staticmethod
    def _normalize_persona_reference(persona_reference: str) -> str:
        return persona_reference.strip().replace("\\", "/").strip("/")

    @staticmethod
    def _split_persona_reference(persona_reference: str) -> tuple[list[str], str]:
        normalized = PersonaPlus._normalize_persona_reference(persona_reference)
        if not normalized:
            raise ValueError("人格 ID 不能为空。")
        parts = [part for part in normalized.split("/") if part]
        if not parts:
            raise ValueError("人格 ID 不能为空。")
        return parts[:-1], parts[-1]

    async def _ordered_personas(self) -> list:
        """按配置排序并应用分组显示顺序后的人格列表（序号即显示编号）。"""
        personas = await self.persona_mgr.get_all_personas()
        if not personas:
            return []
        return compute_display_order(
            self._sort_personas(personas), self.settings.persona_groups or None
        )

    async def _display_index_map(self) -> dict[str, int]:
        """persona_id → 人格列表显示编号 的映射。"""
        ordered = await self._ordered_personas()
        return {p.persona_id: i for i, p in enumerate(ordered, start=1)}

    async def _resolve_display_index(self, raw: str) -> str | None:
        """将图片中显示的序号解析为 persona_id；无法解析时返回 None。

        显示编号即渲染图片左上角徽章中的数字，按分组与分列规则生成，
        与 characters.json 中的 characterId 无关。
        """
        if not raw.isdigit():
            return None
        index = int(raw)
        if index < 1:
            return None
        ordered = await self._ordered_personas()
        if index > len(ordered):
            return None
        return ordered[index - 1].persona_id

    async def _resolve_persona_fuzzy(
        self, persona_ref: str
    ) -> tuple[str | None, list[str]]:
        """解析人格引用：序号 / 人格ID / 别名精确命中，或模糊匹配。

        Returns:
            (persona_id, [])      唯一命中，可直接切换
            (None, candidates)    多个候选（按显示编号排序）
            (None, [])            无匹配
        """
        ref = persona_ref.strip()
        if not ref:
            return None, []

        # 纯数字按人格列表图片的显示序号解析（与 characterId 无关）
        if ref.isdigit():
            display_id = await self._resolve_display_index(ref)
            if display_id:
                return display_id, []

        personas = await self.persona_mgr.get_all_personas()
        if not personas:
            return None, []
        persona_ids = {p.persona_id for p in personas}

        # 人格ID 精确命中
        if ref in persona_ids:
            return ref, []

        # 文件夹路径（如 "分组/人格ID"）按路径解析
        if "/" in ref:
            try:
                _, folder_pid = await self._resolve_persona_reference(
                    ref, require_existing=True
                )
                return folder_pid, []
            except ValueError:
                return None, []

        # 别名精确命中（characters.json）
        resolved = self._char_store.resolve(ref)
        if resolved and resolved in persona_ids:
            return resolved, []

        # 模糊匹配：别名含关键词 或 人格ID含关键词；剔除已不存在的人格
        ref_lower = ref.lower()
        candidates = set(self._char_store.search(ref))
        candidates |= {pid for pid in persona_ids if ref_lower in pid.lower()}
        candidates &= persona_ids
        if len(candidates) == 1:
            return next(iter(candidates)), []
        if not candidates:
            # 子串无命中时按编辑距离近似匹配（容错错别字、漏字、
            # 罗马音/日文/中文之间的形近输入）
            candidates = self._close_match_persona_ids(ref_lower, persona_ids)
            if len(candidates) == 1:
                return next(iter(candidates)), []
        return None, sorted(candidates)

    def _close_match_persona_ids(self, ref_lower: str, persona_ids: set[str]) -> set[str]:
        """在别名键与人格ID上做 difflib 近似匹配，返回命中的人格集合。

        只在子串匹配零命中时调用；阈值为 difflib 默认 0.6，
        3-4 字名称可容错一个字的出入。匹配不上时返回空集合（静默）。
        """
        alias_map = self._char_store.alias_targets()
        keys: dict[str, str] = {}
        for alias, target in alias_map.items():
            if target in persona_ids:
                keys.setdefault(alias, target)
        for pid in persona_ids:
            keys.setdefault(pid.lower(), pid)
        if not keys or len(ref_lower) < 2:
            return set()
        close = difflib.get_close_matches(ref_lower, list(keys), n=10, cutoff=0.6)
        return {keys[k] for k in close}

    async def _format_candidates(
        self, persona_ref: str, candidates: list[str], hint: str
    ) -> str:
        """生成多候选提示文本；序号为渲染列表中的显示编号，可直接用于切换。"""
        index_map = await self._display_index_map()
        ordered = sorted(candidates, key=lambda pid: (index_map.get(pid, 10**9), pid))
        lines = [f"「{persona_ref}」匹配到多个人格，{hint}："]
        for pid in ordered:
            idx = index_map.get(pid)
            lines.append(f"  {idx}. {pid}" if idx else f"  - {pid}")
        return "\n".join(lines)

    async def _resolve_persona_reference(
        self, persona_reference: str, *, require_existing: bool
    ) -> tuple[str | None, str]:
        folder_parts, persona_id = self._split_persona_reference(persona_reference)

        if not require_existing:
            return None, persona_id

        try:
            persona = await self.persona_mgr.get_persona(persona_id)
        except ValueError as exc:
            if folder_parts:
                raise ValueError(f"未找到人格：{persona_reference}") from exc
            raise

        folder_id = None
        if folder_parts:
            folders = {f.folder_id: f for f in await self.persona_mgr.get_all_folders()}
            current_id = None
            for name in folder_parts:
                children = await self.persona_mgr.get_folders(current_id)
                matched = next((c for c in children if c.name == name), None)
                if matched is None:
                    raise ValueError(f"未找到文件夹路径：{'/'.join(folder_parts)}")
                current_id = matched.folder_id
            folder_id = current_id
            if getattr(persona, "folder_id", None) != folder_id:
                raise ValueError(f"未找到人格：{persona_reference}")

        return folder_id, persona_id

    def _sort_personas(self, personas: list) -> list:
        order = self.settings.persona_order
        if not order:
            return list(personas)
        order_map = {pid: i for i, pid in enumerate(order)}
        ordered = []
        seen = set()
        for pid in order:
            for p in personas:
                if p.persona_id == pid and p.persona_id not in seen:
                    ordered.append(p)
                    seen.add(p.persona_id)
                    break
        for p in personas:
            if p.persona_id not in seen:
                ordered.append(p)
                seen.add(p.persona_id)
        return ordered

    # ==================== 人格切换核心 ====================
    async def _switch_persona(
        self, event: AstrMessageEvent, persona_id: str, announce: str | None = None
    ) -> MessageEventResult | None:
        _, resolved_persona_id = await self._resolve_persona_reference(
            persona_id, require_existing=True
        )

        if announce is None and self.auto_switch_announce:
            announce = f"已切换人格为 {resolved_persona_id}"

        return await switch_persona(
            context=self.context,
            persona_mgr=self.persona_mgr,
            user_store=self.user_store,
            event=event,
            persona_id=resolved_persona_id,
            announce=announce,
        )

    # ==================== 交互式人格切换 ====================
    async def _start_interactive_switch(self, event: AstrMessageEvent) -> None:
        umo = event.unified_msg_origin
        if umo in self._active_switches:
            return
        self._active_switches.add(umo)

        personas = await self.persona_mgr.get_all_personas()
        if not personas:
            await event.send(event.plain_result("当前没有人格，请先在控制台或通过指令创建。"))
            self._active_switches.discard(umo)
            return

        personas = self._sort_personas(personas)
        ordered_personas = compute_display_order(personas, self.settings.persona_groups or None)
        persona_ids = [p.persona_id for p in ordered_personas]

        try:
            image_path = render_persona_switch_list(
                personas, self._get_image_output_dir(), groups=self.settings.persona_groups or None
            )
            result = event.make_result()
            result.chain = [
                Comp.Plain("请查看下方人格列表，直接发送序号即可切换人格。"),
                Comp.Image.fromFileSystem(image_path),
            ]
            await event.send(result)
        except Exception as e:
            logger.exception("Persona+ 渲染人格列表图片失败，回退到文本模式: %s", e)
            list_text, _ = await self._render_persona_switch_list()
            await event.send(event.plain_result(list_text))

        @session_waiter(timeout=self.manage_wait_timeout)
        async def switch_waiter(controller: SessionController, next_event: AstrMessageEvent):
            text = next_event.message_str.strip()

            if text in ("取消", "退出", "cancel", "exit"):
                await next_event.send(next_event.plain_result("已取消人格切换。"))
                controller.stop()
                return

            try:
                index = int(text)
                if index < 1 or index > len(persona_ids):
                    await next_event.send(
                        next_event.plain_result(
                            f"序号超出范围（1-{len(persona_ids)}），请重新输入。"
                        )
                    )
                    controller.keep(timeout=self.manage_wait_timeout, reset_timeout=True)
                    return
                selected_persona_id = persona_ids[index - 1]
            except ValueError:
                matched_id, candidates = await self._resolve_persona_fuzzy(text)
                if matched_id is not None:
                    selected_persona_id = matched_id
                else:
                    if candidates:
                        await next_event.send(
                            next_event.plain_result(
                                await self._format_candidates(
                                    text,
                                    candidates,
                                    hint="请直接发送序号或更完整的名称",
                                )
                            )
                        )
                    # 未匹配到任何人格：静默忽略，继续等待
                    controller.keep(
                        timeout=self.manage_wait_timeout, reset_timeout=True
                    )
                    return

            try:
                result = await self._switch_persona(next_event, persona_id=selected_persona_id)
            except ValueError as exc:
                await next_event.send(next_event.plain_result(str(exc)))
                controller.stop()
                return

            if result is not None:
                await next_event.send(result)
            controller.stop()

        async def run_switch_wait() -> None:
            try:
                await switch_waiter(event, session_filter=GroupScopedSessionFilter())
            except TimeoutError:
                await event.send(event.plain_result("人格切换超时，操作已取消。"))
            except Exception:  # noqa: BLE001
                logger.exception("Persona+ 交互式人格切换流程异常")
                await event.send(event.plain_result("人格切换流程异常，请稍后重试。"))
            finally:
                self._active_switches.discard(umo)

        task = asyncio.create_task(run_switch_wait())
        self._tasks.add(task)
        task.add_done_callback(lambda t: self._tasks.discard(t))
        event.stop_event()

    # ==================== 事件监听器：快捷切换（高优先级） ====================
    @filter.event_message_type(filter.EventMessageType.ALL, priority=999)
    async def on_quick_switch_command(self, event: AstrMessageEvent):
        if not event.is_at_or_wake_command:
            return

        text = event.get_message_str().strip()
        # 剥掉唤醒前缀（如 "/pp ena" 会被原样传入本监听器），否则
        # parts[0] 是 "/pp" 而非 "pp"，指令会被静默忽略
        prefix = self._get_command_prefix(event)
        if prefix and text.startswith(prefix):
            text = text[len(prefix) :].strip()
        if not text:
            return

        parts = text.split()
        if not parts:
            return

        cmd = parts[0].lower()
        aliases = {"pp", "persona_plus", "persona+"}
        if cmd not in aliases:
            return

        logger.info(
            "Persona+ [快捷切换] 收到指令: %r (sender=%s, umo=%s)",
            text,
            event.get_sender_id(),
            event.unified_msg_origin,
        )

        if len(parts) == 1:
            has_perm, err_msg = self.check_permission(event, "switch")
            if not has_perm:
                yield event.plain_result(err_msg)
                return
            await self._start_interactive_switch(event)
            return

        if len(parts) != 2:
            yield event.plain_result("用法：pp 人格名；或单独发送 pp 打开人格列表。")
            return

        persona_id = parts[1].strip()
        if not persona_id:
            return

        if persona_id.lower() == "help":
            yield event.plain_result(self._switch_help_text(event))
            return

        has_perm, err_msg = self.check_permission(event, "switch")
        if not has_perm:
            yield event.plain_result(err_msg)
            return

        matched_id, candidates = await self._resolve_persona_fuzzy(persona_id)
        if matched_id is None:
            if candidates:
                yield event.plain_result(
                    await self._format_candidates(
                        persona_id,
                        candidates,
                        hint="请发送 pp 序号（如 pp 3）或更完整的名称",
                    )
                )
            else:
                # 未匹配到任何人格：静默忽略，不回复
                logger.info(
                    "Persona+ [快捷切换] %r 未匹配到任何人格，已忽略", persona_id
                )
                event.stop_event()
            return

        logger.info("Persona+ [快捷切换] %r → 人格 %s", persona_id, matched_id)
        result = await self._switch_persona(event, persona_id=matched_id)
        if result is not None:
            yield result
        event.stop_event()

    # ==================== 指令：人格切换（高优先级） ====================
    @filter.command("人格切换", alias={"切换人格", "人格", "切换"}, priority=999)
    async def cmd_persona_switch_cn(self, event: AstrMessageEvent):
        """交互式人格切换 / 直接切换：人格切换 人格名"""
        has_perm, err_msg = self.check_permission(event, "switch")
        if not has_perm:
            yield event.plain_result(err_msg)
            return

        text = event.get_message_str().strip()
        parts = text.split(None, 1)

        if len(parts) >= 2:
            persona_ref = parts[1].strip()
            matched_id, candidates = await self._resolve_persona_fuzzy(persona_ref)
            if matched_id is None:
                if candidates:
                    yield event.plain_result(
                        await self._format_candidates(
                            persona_ref,
                            candidates,
                            hint="请发送序号或更完整的名称（如：切换人格 3）",
                        )
                    )
                else:
                    # 未匹配到任何人格：静默忽略，不回复
                    logger.info(
                        "Persona+ [切换人格] %r 未匹配到任何人格，已忽略", persona_ref
                    )
                    event.stop_event()
                return
            result = await self._switch_persona(event, persona_id=matched_id)
            if result is not None:
                yield result
            event.stop_event()
            return

        await self._start_interactive_switch(event)

    # ==================== 指令：重置人格（管理员）（高优先级） ====================
    @filter.command("重置人格", alias={"reset"}, priority=999)
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def cmd_reset_personas(self, event: AstrMessageEvent):
        """将所有用户的人格重置为默认"""
        count = await reset_all_personas(
            context=self.context,
            persona_mgr=self.persona_mgr,
            user_store=self.user_store,
        )
        yield event.plain_result(f"已重置 {count} 个用户的人格状态，所有对话恢复为默认人格。")

    # ==================== 消息装饰：人格前缀（仅LLM对话回复）（高优先级） ====================
    @filter.on_decorating_result(priority=999)
    async def on_decorating_result(self, event: AstrMessageEvent):
        if not event.get_extra("_persona_plus_llm"):
            return

        try:
            persona_id = event.get_extra("_persona_plus_request_pid")
            if not persona_id:
                return
            if persona_id in self.EXCLUDE_PERSONA_PREFIX:
                return

            result = event.get_result()
            if not result or not result.chain:
                return

            for component in result.chain:
                if isinstance(component, Comp.Plain) and component.text.strip():
                    prefix = f"[{persona_id}]"
                    if not component.text.startswith(prefix):
                        component.text = f"{prefix}{component.text}"
                    break
        except Exception:  # noqa: BLE001
            logger.debug("Persona+ 人格前缀装饰失败，忽略")

    async def terminate(self):
        for task in list(self._tasks):
            task.cancel()
        self._tasks.clear()
        self._active_switches.clear()
        logger.info("Persona+ 插件卸载，已清理状态。")
