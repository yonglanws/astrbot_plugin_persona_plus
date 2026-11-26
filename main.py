from __future__ import annotations

import asyncio
import difflib
import json
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
from .core.image_renderer import (
    EXCLUDE_PERSONA_IDS,
    compute_display_order,
    render_persona_switch_html,
    render_persona_switch_list,
)
from .core.permissions import check_permission
from .core.session_flows import GroupScopedSessionFilter
from .core.switching import (
    DEFAULT_PERSONA_ID,
    clear_session_conversation_history,
    mark_session_cleanup_extras,
    reset_all_personas,
    switch_persona,
)
from .core.user_persona_store import GroupPersonaStore, PendingHistoryResetStore

from astrbot.core.utils.session_waiter import SessionController, session_waiter


class PersonaPlus(Star):
    """专注于人格切换的插件。"""

    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.context = context
        self.persona_mgr = context.persona_manager

        data_dir = StarTools.get_data_dir("astrbot_plugin_persona_plus")
        self.user_store = GroupPersonaStore(data_dir / "group_personas.json")
        self.pending_reset_store = PendingHistoryResetStore(
            data_dir / "pending_history_resets.json"
        )
        self._image_output_dir = str(data_dir / "images")
        self._guided_path = data_dir / "guided_umos.json"

        self.settings: PersonaPlusSettings
        self.manage_wait_timeout = 60
        self.admin_commands: set[str] = set()
        self.auto_switch_announce = True
        self._tasks: set[asyncio.Task] = set()
        self._active_switches: set[str] = set()
        # 人格列表图片：按"人格顺序 + 分组配置"缓存的最近产物（路径, 生成时间）
        self._render_cache: dict[tuple, tuple[str, float]] = {}
        self._render_cache_ttl = 300
        self._render_lock = asyncio.Lock()
        self._guided_umos: set[str] = set()
        self._guided_store: set[str] = set()
        self._char_store = CharacterStore(Path(__file__).resolve().parent / "characters.json")

        self._load_config(config)
        self._load_guided_store()
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

    def _cleanup_old_images(self, max_age: int = 3600, max_files: int = 20) -> None:
        """清理渲染产物：先按年龄，再按数量保留最新 max_files 张。

        原先只在插件初始化时调用一次，运行期产物只增不减；现在每次
        渲染后也会调用，两次渲染间隔短于 max_age 时靠数量上限兜底。
        """
        img_dir = Path(self._image_output_dir)
        if not img_dir.exists():
            return
        now = time.time()
        recent: list[tuple[float, Path]] = []
        for f in img_dir.iterdir():
            if not (f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg")):
                continue
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            if now - mtime > max_age:
                self._unlink_image(f)
            else:
                recent.append((mtime, f))
        if len(recent) > max_files:
            recent.sort(key=lambda item: item[0])
            for _, f in recent[: len(recent) - max_files]:
                self._unlink_image(f)

    @staticmethod
    def _unlink_image(path: Path) -> None:
        try:
            path.unlink()
        except OSError:
            pass

    def _get_image_output_dir(self) -> str:
        os.makedirs(self._image_output_dir, exist_ok=True)
        return self._image_output_dir

    # ==================== 首次引导状态（去重） ====================
    def _load_guided_store(self) -> None:
        """读取已引导过的会话列表（重启后不重复引导）。"""
        try:
            raw = json.loads(self._guided_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                self._guided_store = {str(x) for x in raw if x}
        except (OSError, json.JSONDecodeError):
            self._guided_store = set()

    def _save_guided_store(self) -> None:
        try:
            self._guided_path.parent.mkdir(parents=True, exist_ok=True)
            self._guided_path.write_text(
                json.dumps(sorted(self._guided_store), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Persona+ 写入引导状态失败：%s", exc)

    def _is_guide_pending(self, umo: str) -> bool:
        """该会话是否已经发过"未选择人格"引导。

        内存标记防并发；持久化标记防重启后重复引导（该会话仍未
        选择人格时，重启后只引导一次）。
        """
        if umo in self._guided_umos:
            return True
        return umo in self._guided_store

    def _mark_guide_pending(self, umo: str) -> None:
        self._guided_umos.add(umo)
        self._guided_store.add(umo)
        self._save_guided_store()

    def _clear_guide_pending(self, umo: str) -> None:
        """用户选定人格后清除引导标记，恢复"未选择"判定。"""
        self._guided_umos.discard(umo)
        self._guided_store.discard(umo)
        self._save_guided_store()

    @filter.on_astrbot_loaded()
    async def on_astrbot_loaded(self):
        logger.info("Persona+ 已就绪，群聊人格存储：%d 条", len(self.user_store.get_all()))

    # ==================== 等待LLM请求：未选择人格时引导切换 ====================
    @filter.on_waiting_llm_request(priority=999)
    async def on_waiting_llm_request(self, event: AstrMessageEvent):
        """从未选择人格的会话：发送人格切换引导并终止本次 LLM 请求。

        该钩子在本体 build_main_agent 与会话锁之前触发，此时 stop_event
        会让本体直接返回：不创建对话记录、不调用 LLM、不加回复前缀，
        用户只会收到引导消息，不会多出一次默认人格的对话。
        已注册的交互式切换流程（session_waiter）不受影响，用户随后
        发送序号即可完成选择。
        """
        umo = event.unified_msg_origin
        if self.pending_reset_store.contains(umo):
            target_pid = self.user_store.get(umo) or DEFAULT_PERSONA_ID
            if await clear_session_conversation_history(
                self.context, umo, target_pid
            ):
                self.pending_reset_store.discard(umo)
            mark_session_cleanup_extras(event)

        if self.user_store.get(umo) or self._is_guide_pending(umo):
            return

        self._mark_guide_pending(umo)
        logger.info("Persona+ [等待请求] %s 未选择人格，发送人格切换引导", umo)
        try:
            await self._start_interactive_switch(
                event,
                intro="当前尚未选择人格，请查看下方人格列表，直接发送序号即可切换人格。",
                stop_event=True,
            )
        except Exception:
            # 失败时仅移除内存标记，允许下次重试；持久化标记保留，
            # 防止渲染持续失败时每条消息都重复引导。
            logger.exception("Persona+ 引导流程异常")
            self._guided_umos.discard(umo)
            raise

    # ==================== LLM请求前：应用保存的人格（最高优先级） ====================
    @filter.on_llm_request(priority=999)
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """把持久化存储中的人格应用到本次 LLM 请求。

        快照人格与存储一致时（绝大多数请求）不修改请求——本体在构建
        阶段已把正确人格段连同安全模式、工具约定等提示一起注入
        system_prompt，整体覆盖会把人格段之外的段落全部抹掉。
        仅当快照落后（切换竞态窗口）时走 _align_request_snapshot
        定点对齐，保证新人格必定生效。

        未选择人格时的引导在 on_waiting_llm_request 中完成，走到这里
        说明本次请求已放行（store 已有值或异常窗口），沿用默认人格。
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
            # 每次 LLM 请求重置前缀标记：本轮对话（含工具调用的多段结果）
            # 只会加一次前缀
            event.set_extra("_persona_plus_prefixed", False)

            if self.pending_reset_store.contains(umo):
                if await clear_session_conversation_history(
                    self.context, umo, target_persona_id
                ):
                    self.pending_reset_store.discard(umo)
                mark_session_cleanup_extras(event)
                if isinstance(getattr(req, "contexts", None), list):
                    req.contexts = self._begin_dialog_entries(persona)

            conv = getattr(req, "conversation", None)
            snapshot_persona_id = getattr(conv, "persona_id", None) if conv else None
            # 4.30 的 prompt 用的是会话 override，构建阶段解析后写在
            # event 的 _trace_persona_id 上；conv.persona_id 只是对话行
            # 快照，override 被单独改过时两者会长期不一致且比较恒相等，
            # 所以以本轮真正生效的人格为基准。
            runtime_persona_id = event.get_extra("_trace_persona_id")
            if runtime_persona_id is None:
                runtime_persona_id = snapshot_persona_id
            if runtime_persona_id != target_persona_id:
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

        本体在构建请求时按当轮生效的会话 override 解析人格，并以
        "<persona_instructions>...</persona_instructions>"（4.30）或
        "\\n# Persona Instructions\\n\\n{prompt}\\n"（4.29）的格式注入
        system_prompt 段与开场对话；若构建与钩子之间发生了人格切换，
        注入的仍是旧人格。此时：
        1. 定点替换 system_prompt 中的人格段，保留本体注入的
           安全模式、工具约定等其他段落；
        2. 快照对话仍是当前对话时，把它的 persona_id 修正为存储值
          （切换指令只会新建对话，不会有并发写把这里改回去）；
        3. 把上下文头部的旧人格开场对话替换为新人格的，使本次请求
           等价于"保留历史的人格切换"。快照已不是当前对话时无需落库
          （切换指令已新建对话），只对齐本次请求。
        """
        conv = getattr(req, "conversation", None)
        # 本轮 prompt 里实际注入的是构建阶段解析出的 _trace_persona_id
        # 对应的人格；conv.persona_id 只是对话行快照，可能与之不一致。
        old_persona_id = event.get_extra("_trace_persona_id") or (
            getattr(conv, "persona_id", None) if conv else None
        )

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

        4.30 本体以 "\\n<persona_instructions>\\n{prompt}\\n
        </persona_instructions>\\n" 注入人格段，4.29 及更早用
        "\\n# Persona Instructions\\n\\n{prompt}\\n"。先按 4.30 格式定位、
        只替换标签内的内容，再回退到 4.29 格式；两者都不在时才追加。
        任何分支都只改人格段本身，保留安全模式、工具约定等其他段落。
        """
        sp = req.system_prompt or ""
        new_prompt = new_persona.system_prompt or ""
        old_prompt = (
            getattr(old_persona, "system_prompt", None) if old_persona else None
        )

        # 4.30：<persona_instructions> 段
        tag_open = "<persona_instructions>"
        tag_close = "</persona_instructions>"
        new_section_430 = f"\n{tag_open}\n{new_prompt}\n{tag_close}\n"

        replaced = False
        if old_prompt:
            old_section_430 = f"\n{tag_open}\n{old_prompt}\n{tag_close}\n"
            if old_section_430 in sp:
                sp = sp.replace(old_section_430, new_section_430, 1)
                replaced = True
        if not replaced:
            start = sp.find(tag_open)
            end = sp.find(tag_close, start + len(tag_open)) if start != -1 else -1
            if start != -1 and end != -1:
                # 旧人格文本未知（刚被删/改）：只替换标签内的内容，
                # 标签外的 safety/工具约定等段落原样保留
                sp = sp[:start] + f"{tag_open}\n{new_prompt}\n" + sp[end:]
                replaced = True

        # 4.29 回退：# Persona Instructions 段
        marker = "\n# Persona Instructions\n\n"
        if not replaced:
            new_section = marker + new_prompt + "\n"
            if old_prompt:
                old_section = marker + old_prompt + "\n"
                if old_section in sp:
                    sp = sp.replace(old_section, new_section, 1)
                    replaced = True
            if not replaced and marker in sp:
                # 旧人格文本未知：替换从 marker 到下一个一级标题之前的内容
                pos = sp.find(marker)
                body_start = pos + len(marker)
                next_heading = sp.find("\n\n# ", body_start)
                section_end = next_heading if next_heading != -1 else len(sp)
                sp = sp[:pos] + new_section + sp[section_end:]
                replaced = True

        if not replaced:
            sp = sp + new_section_430
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
            # 旧快照没有开场对话（人格为空或无效）。本体构建时通常已
            # 插入过新人格的 begin_dialogs，头部已经是这份内容时不能
            # 再插一遍（否则开场问答会重复两份），只有确实缺失才补。
            already_present = len(contexts) >= len(new_entries) and cls._head_matches(
                contexts[: len(new_entries)], new_entries
            )
            if new_entries and not already_present:
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

        personas = [p for p in personas if p.persona_id not in EXCLUDE_PERSONA_IDS]
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
        """按配置排序并应用分组显示顺序后的人格列表（序号即显示编号）。

        与图片渲染保持一致：剔除内置 default 等不渲染的人格，
        否则序号解析会比图片上的编号错位。
        """
        personas = await self.persona_mgr.get_all_personas()
        if not personas:
            return []
        ordered = compute_display_order(
            self._sort_personas(personas), self.settings.persona_groups or None
        )
        return [p for p in ordered if p.persona_id not in EXCLUDE_PERSONA_IDS]

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

        # 人格ID 精确命中（先精确，再大小写不敏感）
        if ref in persona_ids:
            return ref, []
        ref_lower = ref.lower()
        ci_matches = [pid for pid in persona_ids if pid.lower() == ref_lower]
        if len(ci_matches) == 1:
            return ci_matches[0], []

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
        exact_targets = [
            pid for pid in self._char_store.resolve_all(ref) if pid in persona_ids
        ]
        if len(exact_targets) == 1:
            return exact_targets[0], []
        if len(exact_targets) > 1:
            return None, sorted(set(exact_targets))

        # 模糊匹配：别名含关键词 或 人格ID含关键词；单字符 ASCII 不做子串匹配
        allow_substr = not (len(ref_lower) == 1 and ref_lower.isascii())
        candidates = set(self._char_store.search(ref, valid_ids=persona_ids))
        if allow_substr:
            candidates |= {pid for pid in persona_ids if ref_lower in pid.lower()}
        candidates &= persona_ids
        if len(candidates) == 1:
            return next(iter(candidates)), []
        if not candidates:
            # 子串无命中时按编辑距离近似匹配（容错错别字、漏字）
            candidates = self._close_match_persona_ids(ref_lower, persona_ids)
            if len(candidates) == 1:
                return next(iter(candidates)), []
        return None, sorted(candidates)

    def _close_match_persona_ids(self, ref_lower: str, persona_ids: set[str]) -> set[str]:
        """在别名键与人格ID上做高精度的编辑距离近似匹配。

        只在子串匹配零命中时调用；长度 < 3 不做近似匹配避免误命中，
        仅保留与最高相似度相差 0.08 以内的结果。
        """
        if len(ref_lower) < 3:
            return set()
        alias_map = self._char_store.alias_targets()
        keys: dict[str, set[str]] = {}
        for alias, targets in alias_map.items():
            valid = {t for t in targets if t in persona_ids}
            if valid:
                keys.setdefault(alias, set()).update(valid)
        for pid in persona_ids:
            keys.setdefault(pid.lower(), set()).add(pid)
        if not keys:
            return set()

        cutoff = 0.72 if len(ref_lower) == 3 else 0.65
        scored: list[tuple[float, str]] = []
        for k in keys:
            ratio = difflib.SequenceMatcher(None, ref_lower, k).ratio()
            if ratio >= cutoff:
                scored.append((ratio, k))
        if not scored:
            return set()
        best = max(r for r, _ in scored)
        matched: set[str] = set()
        for ratio, k in scored:
            if ratio >= best - 0.08:
                matched.update(keys[k])
        return matched

    def _persona_group_map(self) -> dict[str, str]:
        """构建 persona_id → 团体分组名 的映射。"""
        group_map: dict[str, str] = {}
        for gname, members in (self.settings.persona_groups or {}).items():
            for pid in members:
                clean = pid.strip()
                if clean and clean not in group_map:
                    group_map[clean] = gname
        return group_map

    async def _format_candidates(
        self, persona_ref: str, candidates: list[str], hint: str
    ) -> str:
        """生成多候选提示文本：格式为 [序号]名字(团体)。"""
        index_map = await self._display_index_map()
        group_map = self._persona_group_map()
        ordered = sorted(candidates, key=lambda pid: (index_map.get(pid, 10**9), pid))
        lines = [f"「{persona_ref}」匹配到多个角色，{hint}："]
        for pid in ordered:
            idx = index_map.get(pid)
            idx_str = f"[{idx}]" if idx else "[-]"
            group = group_map.get(pid)
            group_str = f"({group})" if group else ""
            lines.append(f"{idx_str}{pid}{group_str}")
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

        # 用户已做出选择：清除"未选择人格"的引导标记
        self._clear_guide_pending(event.unified_msg_origin)

        if announce is None and self.auto_switch_announce:
            announce = f"已切换人格为 {resolved_persona_id}"

        return await switch_persona(
            context=self.context,
            persona_mgr=self.persona_mgr,
            user_store=self.user_store,
            event=event,
            persona_id=resolved_persona_id,
            announce=announce,
            pending_reset_store=self.pending_reset_store,
        )

    # ==================== 交互式人格切换 ====================
    async def _start_interactive_switch(
        self,
        event: AstrMessageEvent,
        intro: str = "请查看下方人格列表，直接发送序号即可切换人格。",
        *,
        stop_event: bool = True,
    ) -> None:
        """占用该 umo 的切换槽位并启动流程，任何异常都不会泄漏占位。

        _active_switches 原先"先占位、等稍后创建的任务在 finally 释放"，
        占位与创建任务之间任何一步抛异常都会让该 umo 永久留在集合里，
        之后该会话的 pp 与引导全部静默失效。这里用 try/finally 覆盖
        这段窗口：只有确认占位已交给后台任务（handed_off=True）时，
        才由任务的 finally 释放。
        """
        umo = event.unified_msg_origin
        if umo in self._active_switches:
            return
        self._active_switches.add(umo)
        handed_off = False
        try:
            handed_off = await self._launch_interactive_switch(
                event, umo, intro, stop_event=stop_event
            )
        finally:
            if not handed_off:
                self._active_switches.discard(umo)

    async def _launch_interactive_switch(
        self,
        event: AstrMessageEvent,
        umo: str,
        intro: str,
        *,
        stop_event: bool,
    ) -> bool:
        """发送人格列表并登记 session_waiter；返回 True 表示占位已交给后台任务。"""
        personas = await self.persona_mgr.get_all_personas()
        if not personas:
            await event.send(event.plain_result("当前没有人格，请先在控制台或通过指令创建。"))
            return False

        personas = self._sort_personas(personas)
        ordered_personas = compute_display_order(personas, self.settings.persona_groups or None)
        # 与图片渲染、_ordered_personas 保持一致：剔除不渲染的 default
        persona_ids = [
            p.persona_id
            for p in ordered_personas
            if p.persona_id not in EXCLUDE_PERSONA_IDS
        ]

        try:
            image_ref = await self._render_persona_switch_image(
                personas, self.settings.persona_groups or None
            )
            img_comp = (
                Comp.Image.fromURL(image_ref)
                if image_ref.startswith(("http://", "https://"))
                else Comp.Image.fromFileSystem(image_ref)
            )
            result = event.make_result()
            result.chain = [
                Comp.Plain(intro),
                img_comp,
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
        # stop_event 只影响当前事件：终止本体对它的后续处理（LLM 调用、
        # 回复装饰与发送），不会影响 session_waiter 接收后续新消息。
        # 引导路径（on_waiting_llm_request）与指令路径都会传入 True。
        if stop_event:
            event.stop_event()
        # 占位由 run_switch_wait 的 finally 释放
        return True

    async def _render_persona_switch_image(self, personas: list, groups) -> str:
        """优先用 AstrBot t2i（html_render）渲染人格列表图片，失败时回退到 PIL。"""
        key = (
            tuple(getattr(p, "persona_id", "") for p in personas),
            json.dumps(groups or {}, ensure_ascii=False, sort_keys=True),
        )
        async with self._render_lock:
            now = time.time()
            cached = self._render_cache.get(key)
            if cached and now - cached[1] < self._render_cache_ttl:
                cached_ref = cached[0]
                if cached_ref.startswith(("http://", "https://")) or os.path.exists(cached_ref):
                    return cached_ref

            image_ref: str | None = None
            if hasattr(self, "html_render"):
                try:
                    html_str = render_persona_switch_html(personas, groups=groups)
                    image_ref = await self.html_render(
                        html_str,
                        {},
                        return_url=False,
                        options={
                            "type": "png",
                            "full_page": True,
                            "viewport": {"width": 2640, "height": 1800},
                            "device_scale_factor": 2,
                        },
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Persona+ html_render 失败，回退 PIL 渲染: %s", exc)
                    image_ref = None

            if not image_ref:
                image_ref = await asyncio.to_thread(
                    render_persona_switch_list,
                    personas,
                    self._get_image_output_dir(),
                    groups=groups,
                )

            self._render_cache[key] = (image_ref, time.time())
            self._cleanup_old_images()
            self._prune_render_cache()
            return image_ref

    def _prune_render_cache(self) -> None:
        """丢弃过期或文件已被清理的缓存项。"""
        now = time.time()
        for key, (path, ts) in list(self._render_cache.items()):
            if now - ts >= self._render_cache_ttl or not os.path.exists(path):
                self._render_cache.pop(key, None)

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
    # 带斜杠的写法也要登记：生产的 wake_prefix 是空列表，框架不会剥掉前缀，
    # "/人格切换" 会原样参与指令匹配，不加别名就匹配不到。
    @filter.command(
        "人格切换",
        alias={
            "切换人格",
            "人格",
            "切换",
            "/人格切换",
            "/切换人格",
            "/人格",
            "/切换",
        },
        priority=999,
    )
    async def cmd_persona_switch_cn(self, event: AstrMessageEvent):
        """交互式人格切换 / 直接切换：人格切换 人格名"""
        try:
            admin_flag = bool(event.is_admin())
        except Exception:  # noqa: BLE001
            admin_flag = False
        logger.info(
            "Persona+ [切人格指令] 命中: text=%r sender=%s umo=%s admin=%s",
            event.get_message_str(),
            event.get_sender_id(),
            event.unified_msg_origin,
            admin_flag,
        )
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
    @filter.command("重置人格", alias={"reset", "/重置人格", "/reset"}, priority=999)
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def cmd_reset_personas(self, event: AstrMessageEvent):
        """将所有用户的人格重置为默认"""
        count = await reset_all_personas(
            context=self.context,
            persona_mgr=self.persona_mgr,
            user_store=self.user_store,
            exclude_event=event,
            pending_reset_store=self.pending_reset_store,
        )
        # 人格选择已被清空：同步清除引导标记，让所有会话重新进入
        # "未选择人格" 状态，下次触发时重新引导。
        for umo in list(self._guided_umos):
            self._clear_guide_pending(umo)
        yield event.plain_result(f"已重置 {count} 个用户的人格状态，所有对话恢复为默认人格。")

    # ==================== 消息装饰：人格前缀（仅LLM对话回复）（高优先级） ====================
    @staticmethod
    def _is_llm_result(result) -> bool:
        """判断结果是否为 LLM 生成的回复（排除插件/工具状态等普通结果）。"""
        fn = getattr(result, "is_llm_result", None)
        if callable(fn):
            try:
                return bool(fn())
            except Exception:  # noqa: BLE001
                pass
        content_type = getattr(result, "result_content_type", None)
        return getattr(content_type, "name", "") in {
            "LLM_RESULT",
            "STREAMING_RESULT",
            "STREAMING_FINISH",
        }

    @filter.on_decorating_result(priority=999)
    async def on_decorating_result(self, event: AstrMessageEvent):
        """给 LLM 回复加人格前缀，每轮对话最多一次。

        本体管线是洋葱模型：ProcessStage 每次 yield 都会让装饰与回复
        阶段重跑一遍。Agent 工具调用场景下，模型"调用工具前的说明"和
        "最终回复"是同一 event 上先后独立的结果，若按 event 无差别加
        前缀，一轮就会出现多个 [人格] 前缀（配合分段回复更明显）。
        因此这里以 event 级标记保证一轮只加一次，并且只装饰 LLM 结果，
        不碰插件自己发出的消息与工具状态消息。
        """
        if not event.get_extra("_persona_plus_llm"):
            return
        if event.get_extra("_persona_plus_prefixed"):
            return

        try:
            persona_id = event.get_extra("_persona_plus_request_pid")
            if not persona_id:
                return

            result = event.get_result()
            if not result or not result.chain:
                return
            if not self._is_llm_result(result):
                return

            prefix = f"[{persona_id}]"
            for component in result.chain:
                if isinstance(component, Comp.Plain) and component.text.strip():
                    if not component.text.startswith(prefix):
                        component.text = f"{prefix}{component.text}"
                    event.set_extra("_persona_plus_prefixed", True)
                    break
        except Exception:  # noqa: BLE001
            logger.debug("Persona+ 人格前缀装饰失败，忽略")

    async def terminate(self):
        for task in list(self._tasks):
            task.cancel()
        self._tasks.clear()
        self._active_switches.clear()
        logger.info("Persona+ 插件卸载，已清理状态。")
