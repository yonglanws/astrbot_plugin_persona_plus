# AstrBot 开发文档

> 本文件包含 AstrBot 的 dev/（开发）目录下的所有文档。

## 目录

1. [AstrBot 配置文件](#astrbot-config)
2. [AstrBot HTTP API](#openapi)
3. [开发一个平台适配器](#plugin-platform-adapter)
4. [插件开发（重定向页）](#plugin)
5. [AstrBot 插件开发指南](#plugin-new)
6. [发布插件到插件市场](#plugin-publish)
7. [旧版插件开发指南（完整版）](#plugin-old)
8. [最小实例](#simple)
9. [环境准备](#env)
10. [处理消息事件](#listen-message-event)
11. [消息的发送](#send-message)
12. [会话控制](#session-control)
13. [AI 相关](#ai)
14. [文转图](#html-to-pic)
15. [插件配置](#plugin-config)
16. [插件国际化](#plugin-i18n)
17. [插件 Pages](#plugin-pages)
18. [杂项](#other)
19. [插件存储](#storage)

---

<a id="astrbot-config"></a>

---
outline: deep
---

# AstrBot 配置文件

## data/cmd_config.json

AstrBot 的配置文件是一个 JSON 格式的文件。AstrBot 会在启动时读取这个文件，并根据文件中的配置来初始化 AstrBot，其路径位于 `data/cmd_config.json`。

> 在 AstrBot v4.0.0 版本及之后，我们引入了[多配置文件](https://blog.astrbot.app/posts/what-is-changed-in-4.0.0/#%E5%A4%9A%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6)的概念。`data/cmd_config.json` 作为默认配置文件 `default`。其他您在 WebUI 新建的配置文件会存储在 `data/config/` 目录下，以 `abconf_` 开头。

AstrBot 默认配置如下：

```jsonc
{
    "config_version": 2,
    "platform_settings": {
        "unique_session": False,
        "rate_limit": {
            "time": 60,
            "count": 30,
            "strategy": "stall",  # stall, discard
        },
        "reply_prefix": "",
        "forward_threshold": 1500,
        "enable_id_white_list": True,
        "id_whitelist": [],
        "id_whitelist_log": True,
        "wl_ignore_admin_on_group": True,
        "wl_ignore_admin_on_friend": True,
        "reply_with_mention": False,
        "reply_with_quote": False,
        "path_mapping": [],
        "segmented_reply": {
            "enable": False,
            "only_llm_result": True,
            "interval_method": "random",
            "interval": "1.5,3.5",
            "log_base": 2.6,
            "words_count_threshold": 150,
            "regex": ".*?[。？！~…]+|.+$",
            "content_cleanup_rule": "",
        },
        "no_permission_reply": True,
        "empty_mention_waiting": True,
        "empty_mention_waiting_need_reply": True,
        "friend_message_needs_wake_prefix": False,
        "ignore_bot_self_message": False,
        "ignore_at_all": False,
    },
    "provider": [],
    "provider_settings": {
        "enable": True,
        "default_provider_id": "",
        "default_image_caption_provider_id": "",
        "image_caption_prompt": "Please describe the image using Chinese.",
        "provider_pool": ["*"],  # "*" 表示使用所有可用的提供者
        "wake_prefix": "",
        "web_search": False,
        "websearch_provider": "tavily",
        "websearch_tavily_key": [],
        "websearch_bocha_key": [],
        "websearch_brave_key": [],
        "web_search_link": False,
        "display_reasoning_text": False,
        "identifier": False,
        "group_name_display": False,
        "datetime_system_prompt": True,
        "default_personality": "default",
        "persona_pool": ["*"],
        "prompt_prefix": "{{prompt}}",
        "max_context_length": -1,
        "dequeue_context_length": 1,
        "streaming_response": False,
        "show_tool_use_status": False,
        "streaming_segmented": False,
        "max_agent_step": 30,
        "tool_call_timeout": 120,
    },
    "provider_stt_settings": {
        "enable": False,
        "provider_id": "",
    },
    "provider_tts_settings": {
        "enable": False,
        "provider_id": "",
        "dual_output": False,
        "use_file_service": False,
    },
    "provider_ltm_settings": {
        "group_icl_enable": False,
        "group_message_max_cnt": 300,
        "image_caption": False,
        "active_reply": {
            "enable": False,
            "method": "possibility_reply",
            "possibility_reply": 0.1,
            "whitelist": [],
        },
    },
    "content_safety": {
        "also_use_in_response": False,
        "internal_keywords": {"enable": True, "extra_keywords": []},
        "baidu_aip": {"enable": False, "app_id": "", "api_key": "", "secret_key": ""},
    },
    "admins_id": ["astrbot"],
    "t2i": False,
    "t2i_word_threshold": 150,
    "t2i_strategy": "remote",
    "t2i_endpoint": "",
    "t2i_use_file_service": False,
    "t2i_active_template": "base",
    "http_proxy": "",
    "no_proxy": ["localhost", "127.0.0.1", "::1"],
    "dashboard": {
        "enable": True,
        "username": "astrbot",
        "password": "77b90590a8945a7d36c963981a307dc9",
        "jwt_secret": "",
        "host": "0.0.0.0",
        "port": 6185,
    },
    "platform": [],
    "platform_specific": {
        # 平台特异配置：按平台分类，平台下按功能分组
        "lark": {
            "pre_ack_emoji": {"enable": False, "emojis": ["Typing"]},
        },
        "telegram": {
            "pre_ack_emoji": {"enable": False, "emojis": ["✍️"]},
        },
        "discord": {
            "pre_ack_emoji": {"enable": False, "emojis": ["🤔"]},
        },
    },
    "wake_prefix": ["/"],
    "log_level": "INFO",
    "trace_enable": False,
    "pip_install_arg": "",
    "pypi_index_url": "https://mirrors.aliyun.com/pypi/simple/",
    "persona": [],  # deprecated
    "timezone": "Asia/Shanghai",
    "callback_api_base": "",
    "default_kb_collection": "",  # 默认知识库名称
    "plugin_set": ["*"],  # "*" 表示使用所有可用的插件, 空列表表示不使用任何插件
}
```

## 字段详解

### `config_version`

配置文件版本，请勿修改。

### `platform_settings`

消息平台适配器的通用设置。

#### `platform_settings.unique_session`

是否启用会话隔离。默认为 `false`。启用后，在群组或者频道中，每个人的对话的上下文都是独立的。

#### `platform_settings.rate_limit`

当消息速率超过限制时的处理策略。`time` 为时间窗口，`count` 为消息数量，`strategy` 为限制策略。`stall` 为等待，`discard` 为丢弃。

#### `platform_settings.reply_prefix`

回复消息时的固定前缀字符串。默认为空。

#### `platform_settings.forward_threshold`

> 目前仅 QQ 平台适配器适用。

消息转发阈值。当回复内容超过一定字数后，机器人会将消息折叠成 QQ 群聊的 “转发消息”，以防止刷屏。

#### `platform_settings.enable_id_white_list`

是否启用 ID 白名单。默认为 `true`。启用后，只有在白名单中的 ID 发来的消息才会被处理。

#### `platform_settings.id_whitelist`

ID 白名单。填写后，将只处理所填写的 ID 发来的消息事件。为空时表示不启用白名单过滤。可以使用 `/sid` 指令获取在某个平台上的会话 ID。

也可在 AstrBot 日志内获取会话 ID，当一条消息没通过白名单时，会输出 INFO 级别的日志，格式类似 `aiocqhttp:GroupMessage:547540978`

#### `platform_settings.id_whitelist_log`

是否打印未通过 ID 白名单的消息日志。默认为 `true`。

#### `platform_settings.wl_ignore_admin_on_group` & `platform_settings.wl_ignore_admin_on_friend`

- `wl_ignore_admin_on_group`: 是否管理员发送的群组消息无视 ID 白名单。默认为 `true`。

- `wl_ignore_admin_on_friend`: 是否管理员发送的私聊消息无视 ID 白名单。默认为 `true`。

#### `platform_settings.reply_with_mention`

是否在回复消息时 @ 提到用户。默认为 `false`。

#### `platform_settings.reply_with_quote`

是否在回复消息时引用用户的消息。默认为 `false`。

#### `platform_settings.path_mapping`

*该配置项已经在 v4.0.0 版本之后被废弃。*

路径映射列表。用于将消息中的文件路径进行替换。每个映射项包含 `from` 和 `to` 两个字段，表示将消息中的 `from` 路径替换为 `to` 路径。

#### `platform_settings.segmented_reply`

分段回复设置。

- `enable`: 是否启用分段回复。默认为 `false`。
- `only_llm_result`: 是否仅对 LLM 生成的回复进行分段。默认为 `true`。
- `interval_method`: 分段间隔方法。可选值为 `random` 和 `log`。默认为 `random`。
- `interval`: 分段间隔时间。对于 `random` 方法，填写两个逗号分隔的数字，表示最小和最大间隔时间（单位：秒）。对于 `log` 方法，填写一个数字，表示对数基底。默认为 `"1.5,3.5"`。
- `log_base`: 对数基底，仅在 `interval_method` 为 `log` 时适用。默认为 `2.6`。
- `words_count_threshold`: 分段回复的字数上限。只有字数小于此值的消息才会被分段，超过此值的长消息将直接发送（不分段）。默认为 `150`。
- `regex`: 用于分隔一段消息。默认情况下会根据句号、问号等标点符号分隔。`re.findall(r'<regex>', text)`。默认值为 `".*?[。？！~…]+|.+$"`。
- `content_cleanup_rule`: 移除分段后的内容中的指定的内容。支持正则表达式。如填写 `[。？！]` 将移除所有的句号、问号、感叹号。`re.sub(r'<regex>', '', text)`。

#### `platform_settings.no_permission_reply`

是否在用户没有权限时回复无权限的提示消息。默认为 `true`。

#### `platform_settings.empty_mention_waiting`

是否启用空 @ 等待机制。默认为 `true`。启用后，当用户发送一条仅包含 @ 机器人的消息时，机器人会等待用户在 60 秒内发送下一条消息，并将两条消息合并后进行处理。这在某些平台不支持 @ 和语音/图片等消息同时发送时特别有用。

#### `platform_settings.empty_mention_waiting_need_reply`

在上面一个配置项(`empty_mention_waiting`)中，如果启用了触发等待，启用此项后，机器人会立即使用 LLM 生成一条回复。否则，将不回复而只是等待。默认为 `true`。

#### `platform_settings.friend_message_needs_wake_prefix`

是否在消息平台的私聊消息中需要唤醒前缀。默认为 `false`。启用后，在私聊消息中，用户需要使用唤醒前缀才能触发机器人的响应。

#### `platform_settings.ignore_bot_self_message`

是否忽略机器人自己发送的消息。默认为 `false`。启用后，机器人将不会处理自己发送的消息，在某些平台可以防止死循环。

#### `platform_settings.ignore_at_all`

是否忽略 @ 全体成员的消息。默认为 `false`。启用后，机器人将不会响应包含 @ 全体成员的消息。

### `provider`

> 此配置项仅在 `data/cmd_config.json` 中生效，AstrBot 不会读取 `data/config/` 目录下的配置文件中的此项。

已配置的模型服务提供商的配置列表。

### `provider_settings`

大语言模型提供商的通用设置。

#### `provider_settings.enable`

是否启用大语言模型聊天。默认为 `true`。

#### `provider_settings.default_provider_id`

默认的对话模型提供商 ID。必须是 `provider` 列表中已配置的提供商 ID。如果为空，则使用配置列表中的第一个对话模型提供商。

#### `provider_settings.default_image_caption_provider_id`

默认的图像描述模型提供商 ID。必须是 `provider` 列表中已配置的提供商 ID。如果为空，则代表不使用图像描述功能。

此配置项的意思是，当用户发送一张图片时，AstrBot 会使用此提供商来生成对图片的描述文本，并将描述文本作为对话的上下文之一。这在对话模型不支持多模态输入时特别有用。

#### `provider_settings.image_caption_prompt`

图像描述的提示词模板。默认为 `"Please describe the image using Chinese."`。

#### `provider_settings.provider_pool`

*此配置项尚未实际使用*

#### `provider_settings.wake_prefix`

使用 LLM 聊天额外的触发条件。如填写 `chat`，则需要发送消息时要以 `/chat` 才能触发 LLM 聊天。其中 `/` 是机器人的唤醒前缀。是一个防止滥用的手段。

#### `provider_settings.web_search`

是否启用 AstrBot 自带的网页搜索能力。默认为 `false`。启用后，LLM 可能会自动搜索网页并根据内容回答。

#### `provider_settings.websearch_provider`

网页搜索提供商类型。默认为 `tavily`。目前支持 `tavily`、`bocha`、`baidu_ai_search`、`brave`。

- `tavily`：使用 Tavily 搜索引擎。
- `bocha`：使用 BoCha 搜索引擎。
- `baidu_ai_search`：使用百度 AI Search（MCP）。
- `brave`：使用 Brave Search API。

#### `provider_settings.websearch_tavily_key`

Tavily 搜索引擎的 API Key 列表。使用 `tavily` 作为网页搜索提供商时需要填写。

#### `provider_settings.websearch_bocha_key`

BoCha 搜索引擎的 API Key 列表。使用 `bocha` 作为网页搜索提供商时需要填写。

#### `provider_settings.websearch_brave_key`

Brave 搜索引擎的 API Key 列表。使用 `brave` 作为网页搜索提供商时需要填写。

#### `provider_settings.web_search_link`

是否在回复中提示模型附上搜索结果的链接。默认为 `false`。

#### `provider_settings.display_reasoning_text`

是否在回复中显示模型的推理过程。默认为 `false`。

#### `provider_settings.identifier`

是否在 Prompt 前加上群成员的名字以让模型更好地了解群聊状态。默认为 `false`。启用将略微增加 token 开销。

#### `provider_settings.group_name_display`

是否在提示模型了解所在群的名称。默认为 `false`。此配置项目前仅在 QQ 平台适配器中生效。

#### `provider_settings.datetime_system_prompt`

是否在系统提示词中加上当前机器的日期时间。默认为 `true`。

#### `provider_settings.default_personality`

默认使用的人格的 ID。请在 WebUI 配置人格。

#### `provider_settings.persona_pool`

*此配置项尚未实际使用*

#### `provider_settings.prompt_prefix`

用户提示词。可使用 `{{prompt}}` 作为用户输入的占位符。如果不输入占位符则代表添加在用户输入的前面。

#### `provider_settings.max_context_length`

当对话上下文超出这个数量时丢弃最旧的部分，一轮聊天记为 1 条。-1 为不限制。

#### `provider_settings.dequeue_context_length`

当触发上面提到的 `max_context_length` 限制时，每次丢弃的对话轮数。

#### `provider_settings.streaming_response`

是否启用流式响应。默认为 `false`。启用后，模型的回复会实时类似打字机的效果发送给用户。此配置项仅在 WebChat、Telegram、飞书平台生效。

#### `provider_settings.show_tool_use_status`

是否显示工具使用状态。默认为 `false`。启用后，模型在使用工具时会显示工具的名称和输入参数。

#### `provider_settings.streaming_segmented`

不支持流式响应的消息平台是否降级为使用分段回复。默认为 `false`。意思是，如果启用了流式响应，但当前消息平台不支持流式响应，那么是否使用分段多次回复来代替。

#### `provider_settings.max_agent_step`

Agent 最大步骤数限制。默认为 `30`。模型的每次工具调用算作一步。

#### `provider_settings.tool_call_timeout`

Added in `v4.3.5`

工具调用的最大超时时间（秒），默认为 `60` 秒。

#### `provider_stt_settings`

语音转文本服务提供商的通用设置。

#### `provider_stt_settings.enable`

是否启用语音转文本服务。默认为 `false`。

#### `provider_stt_settings.provider_id`

语音转文本服务提供商 ID。必须是 `provider` 列表中已配置的 STT 提供商 ID。

#### `provider_tts_settings`

文本转语音服务提供商的通用设置。

#### `provider_tts_settings.enable`

是否启用文本转语音服务。默认为 `false`。

#### `provider_tts_settings.provider_id`

文本转语音服务提供商 ID。必须是 `provider` 列表中已配置的 TTS 提供商 ID。

#### `provider_tts_settings.dual_output`

是否启用双输出。默认为 `false`。启用后，机器人会同时发送文本和语音消息。

#### `provider_tts_settings.use_file_service`

是否启用文件服务。默认为 `false`。启用后，机器人会将输出的语音文件以 HTTP 文件外链的形式提供给消息平台。此配置项依赖于 `callback_api_base` 的配置。

#### `provider_ltm_settings`

群聊上下文感知服务提供商的通用设置。

#### `provider_ltm_settings.group_icl_enable`

是否启用群聊上下文感知。默认为 `false`。启用后，机器人会记录群聊中的对话内容，以便更好地理解群聊的上下文。

上下文的内容会被放在对话的系统提示词中。

#### `provider_ltm_settings.group_message_max_cnt`

群聊消息的最大记录数量。默认为 `100`。超过此数量的消息将被丢弃。

#### `provider_ltm_settings.image_caption`

是否记录群聊中的图片，并自动使用图像描述模型生成图片的描述文本。默认为 `false`。此配置项依赖于 `provider_settings.default_image_caption_provider_id` 的配置。请谨慎使用，因为这可能会增加大量的 API 调用和 token 开销。

#### `provider_ltm_settings.active_reply`

- `enable`: 是否启用主动回复。默认为 `false`。
- `method`: 主动回复的方法。可选值为 `possibility_reply`。
- `possibility_reply`: 主动回复的概率。默认为 `0.1`。仅在 `method` 为 `possibility_reply` 时适用。
- `whitelist`: 主动回复的 ID 白名单。仅在此列表中的 ID 才会触发主动回复。为空时表示不启用白名单过滤。可以使用 `/sid` 指令获取在某个平台上的会话 ID。

### `content_safety`

内容安全设置。

#### `content_safety.also_use_in_response`

是否在 LLM 回复中也进行内容安全检查。默认为 `false`。启用后，机器人生成的回复也会经过内容安全检查，以防止生成不当内容。

#### `content_safety.internal_keywords`

内部关键词检测设置。

- `enable`: 是否启用内部关键词检测。默认为 `true`。
- `extra_keywords`: 额外的关键词列表，支持正则表达式。默认为空。

#### `content_safety.baidu_aip`

百度 AI 内容审核设置。

- `enable`: 是否启用百度 AI 内容审核。默认为 `false`。
- `app_id`: 百度 AI 内容审核的 App ID。
- `api_key`: 百度 AI 内容审核的 API Key。
- `secret_key`: 百度 AI 内容审核的 Secret Key。

> [!TIP]
> 如果要启用百度 AI 内容审核，请先 `pip install baidu-aip`。

### `admins_id`

管理员 ID 列表。此外，还可以使用 `/op`, `/deop` 指令来添加或删除管理员。

### `t2i`

是否启用文本转图像功能。默认为 `false`。启用后，当用户发送的消息超过一定字数时，机器人会将消息渲染成图片发送给用户，以提高可读性并防止刷屏。支持 Markdown 渲染。

### `t2i_word_threshold`

文本转图像的字数阈值。默认为 `150`。当用户发送的消息超过此字数时，机器人会将消息渲染成图片发送给用户。

### `t2i_strategy`

文本转图像的渲染策略。可选值为 `local` 和 `remote`。默认为 `remote`。

- `local`: 使用 AstrBot 本地的文本转图像服务进行渲染。效果较差，但不依赖外部服务。
- `remote`: 使用远程的文本转图像服务进行渲染。默认使用 AstrBot 官方提供的服务，效果较好。

### `t2i_endpoint`

AstrBot API 的地址。用于渲染 Markdown 图片。当 `t2i_strategy` 为 `remote` 时生效。默认为空，表示使用 AstrBot 官方提供的服务。

### `t2i_use_file_service`

是否启用文件服务。默认为 `false`。启用后，机器人会将渲染的图片以 HTTP 文件外链的形式提供给消息平台。此配置项依赖于 `callback_api_base` 的配置。

### `http_proxy`

HTTP 代理。如 `http://localhost:7890`。

### `no_proxy`

不使用代理的地址列表。如 `["localhost", "127.0.0.1"]`。

### `dashboard`

AstrBot WebUI 配置。

请不要随意修改 `password` 的值。它是一个经过 `md5` 编码的密码。请在控制面板修改密码。

- `enable`: 是否启用 AstrBot WebUI。默认为 `true`。
- `username`: AstrBot WebUI 的用户名。默认为 `astrbot`。
- `password`: AstrBot WebUI 的密码。默认为 `astrbot` 的 `md5` 编码值。请勿直接修改，除非您知道自己在做什么。
- `jwt_secret`: JWT 的密钥。AstrBot 会在初始化时随机生成。请勿修改，除非您知道自己在做什么。
- `host`: AstrBot WebUI 监听的地址。默认为 `0.0.0.0`。
- `port`: AstrBot WebUI 监听的端口。默认为 `6185`。

### `platform`

> 此配置项仅在 `data/cmd_config.json` 中生效，AstrBot 不会读取 `data/config/` 目录下的配置文件中的此项。

已配置的 AstrBot 消息平台适配器的配置列表。

### `platform_specific`

平台特异配置。按平台分类，平台下按功能分组。

#### `platform_specific.<platform>.pre_ack_emoji`

启用后，当请求 LLM 前，AstrBot 会先发送一个预回复的表情以告知用户正在处理请求。此功能目前仅在飞书平台适配器和 Telegram 中生效。

##### lark (飞书)

- `enable`: 是否启用飞书消息预回复表情。默认为 `false`。
- `emojis`: 预回复的表情列表。默认为 `["Typing"]`。表情枚举名参考：[表情文案说明](https://open.feishu.cn/document/server-docs/im-v1/message-reaction/emojis-introduce)

##### telegram

- `enable`: 是否启用 Telegram 消息预回复表情。默认为 `false`。
- `emojis`: 预回复的表情列表。默认为 `["✍️"]`。Telegram 仅支持固定反应集合，参考：[reactions.txt](https://gist.github.com/Soulter/3f22c8e5f9c7e152e967e8bc28c97fc9)

##### discord

- `enable`: 是否启用 Discord 消息预回复表情。默认为 `false`。
- `emojis`: 预回复的表情列表。默认为 `["🤔"]`。Discord反应支持参考：[Discord Reaction FAQ](https://support.discord.com/hc/en-us/articles/12102061808663-Reactions-and-Super-Reactions-FAQ)

### `wake_prefix`

唤醒前缀。默认为 `/`。当消息以 `/` 开头时，AstrBot 会被唤醒。

> [!TIP]
> 如果唤醒的会话不在 ID 白名单中，AstrBot 将不会响应。

### `log_level`

日志级别。默认为 `INFO`。可以设置为 `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`。

### `trace_enable`

是否启用追踪记录。默认为 `false`。启用后，AstrBot 会记录运行追踪信息，可以在管理面板的 Trace 页面查看。

### `pip_install_arg`

`pip install` 的参数。如 `-i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple`。

### `pypi_index_url`

PyPI 镜像源地址。默认为 `https://mirrors.aliyun.com/pypi/simple/`。

### `persona`

*此配置项已经在 v4.0.0 版本之后被废弃。请使用 WebUI 来配置人格。*

已配置的人格列表。每个人格包含 `id`, `name`, `description`, `system_prompt` 四个字段。

### `timezone`

时区设置。请填写 IANA 时区名称, 如 Asia/Shanghai, 为空时使用系统默认时区。所有时区请查看: [IANA Time Zone Database](https://data.iana.org/time-zones/tzdb-2021a/zone1970.tab)。

### `callback_api_base`

AstrBot API 的基础地址。用于文件服务和插件回调等功能。如 `http://example.com:6185`。默认为空，表示不启用文件服务和插件回调功能。

### `default_kb_collection`

默认知识库名称。用于 RAG 功能。如果为空，则不使用知识库。

### `plugin_set`

已启用的插件列表。`*` 表示启用所有可用的插件。默认为 `["*"]`。


---

<a id="openapi"></a>

---
outline: deep
---

# AstrBot HTTP API

从 v4.18.0 开始，AstrBot 提供基于 API Key 的 HTTP API，开发者可以通过标准 HTTP 请求访问核心能力。

## 快速开始

1. 在 WebUI - 设置中创建 API Key。
2. 在请求头中携带 API Key：

```http
Authorization: Bearer abk_xxx
```

也支持：

```http
X-API-Key: abk_xxx
```

3. 对于对话接口，`username` 为必填参数：

- `POST /api/v1/chat`：请求体必须包含 `username`
- `GET /api/v1/chat/sessions`：查询参数必须包含 `username`

## Scope 权限说明

创建 API Key 时可配置 `scopes`。每个 scope 控制可访问的接口范围：

| Scope | 作用 | 可访问接口 |
| --- | --- | --- |
| `chat` | 调用对话能力、查询对话会话 | `POST /api/v1/chat`、`GET /api/v1/chat/sessions` |
| `config` | 获取可用配置文件列表 | `GET /api/v1/configs` |
| `file` | 上传附件文件，获取 `attachment_id` | `POST /api/v1/file` |
| `im` | 主动发 IM 消息、查询 bot/platform 列表 | `POST /api/v1/im/message`、`GET /api/v1/im/bots` |

如果 API Key 未包含目标接口所需 scope，请求会返回 `403 Insufficient API key scope`。

## 常用接口

**对话类**

调用 AstrBot 内建的 Agent 进行对话交互。支持插件调用、工具调用等能力，与 IM 端对话能力一致。

- `POST /api/v1/chat`：发送对话消息（SSE 流式返回，不传 `session_id` 会自动创建 UUID）
- `GET /api/v1/chat/sessions`：分页获取指定 `username` 的会话
- `GET /api/v1/configs`：获取可用配置文件列表

**文件上传**

- `POST /api/v1/file`：上传附件

**IM 消息发送**

- `POST /api/v1/im/message`：按 UMO 主动发消息
- `GET /api/v1/im/bots`：获取 bot/platform ID 列表

## `message` 字段格式（重点）

`POST /api/v1/chat` 和 `POST /api/v1/im/message` 的 `message` 字段支持两种格式：

1. 字符串：纯文本消息
2. 数组：消息段（message chain）

### 1. 纯文本格式

```json
{
  "message": "Hello"
}
```

### 2. 消息段数组格式

```json
{
  "message": [
    { "type": "plain", "text": "请看这个文件" },
    { "type": "file", "attachment_id": "9a2f8c72-e7af-4c0e-b352-111111111111" }
  ]
}
```

支持的 `type`：

| type | 必填字段 | 可选字段 | 说明 |
| --- | --- | --- | --- |
| `plain` | `text` | - | 文本段 |
| `reply` | `message_id` | `selected_text` | 引用回复某条消息 |
| `image` | `attachment_id` | - | 图片附件段 |
| `record` | `attachment_id` | - | 音频附件段 |
| `file` | `attachment_id` | - | 通用文件段 |
| `video` | `attachment_id` | - | 视频附件段 |

* reply 消息段目前仅适配 `/api/v1/chat`，不适用于 `POST /api/v1/im/message`。


说明：

- `attachment_id` 来自 `POST /api/v1/file` 上传结果。
- `reply` 不能单独作为唯一内容，至少需要一个有实际内容的段（如 `plain/image/file/...`）。
- 仅 `reply` 或空内容会返回错误。

### Chat API 的 `message` 用法

`POST /api/v1/chat` 额外需要 `username`，可选 `session_id`（不传会自动创建 UUID）。

```json
{
  "username": "alice",
  "session_id": "my_session_001",
  "message": [
    { "type": "plain", "text": "帮我总结这个 PDF" },
    { "type": "file", "attachment_id": "9a2f8c72-e7af-4c0e-b352-111111111111" }
  ],
  "enable_streaming": true
}
```

### IM Message API 的 `message` 用法

`POST /api/v1/im/message` 需要 `umo` + `message`。

```json
{
  "umo": "webchat:FriendMessage:openapi_probe",
  "message": [
    { "type": "plain", "text": "这是主动消息" },
    { "type": "image", "attachment_id": "9a2f8c72-e7af-4c0e-b352-222222222222" }
  ]
}
```

## 示例

```bash
curl -N 'http://localhost:6185/api/v1/chat' \
  -H 'Authorization: Bearer abk_xxx' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hello","username":"alice"}'
```

## 完整 API 文档

交互式 API 文档请查看：

- https://docs.astrbot.app/scalar.html


---

<a id="plugin-platform-adapter"></a>

---
outline: deep
---

# 开发一个平台适配器

AstrBot 支持以插件的形式接入平台适配器，你可以自行接入 AstrBot 没有的平台。如飞书、钉钉甚至是哔哩哔哩私信、Minecraft。

我们以一个平台 `FakePlatform` 为例展开讲解。

首先，在插件目录下新增 `fake_platform_adapter.py` 和 `fake_platform_event.py` 文件。前者主要是平台适配器的实现，后者是平台事件的定义。

## 平台适配器

假设 FakePlatform 的客户端 SDK 是这样：

```py
import asyncio

class FakeClient():
    '''模拟一个消息平台，这里 5 秒钟下发一个消息'''
    def __init__(self, token: str, username: str):
        self.token = token
        self.username = username
        # ...
                
    async def start_polling(self):
        while True:
            await asyncio.sleep(5)
            await getattr(self, 'on_message_received')({
                'bot_id': '123',
                'content': '新消息',
                'username': 'zhangsan',
                'userid': '123',
                'message_id': 'asdhoashd',
                'group_id': 'group123',
            })
            
    async def send_text(self, to: str, message: str):
        print('发了消息:', to, message)
        
    async def send_image(self, to: str, image_path: str):
        print('发了消息:', to, image_path)
```

我们创建  `fake_platform_adapter.py`：

```py
import asyncio

from astrbot.api.platform import Platform, AstrBotMessage, MessageMember, PlatformMetadata, MessageType
from astrbot.api.event import MessageChain
from astrbot.api.message_components import Plain, Image, Record # 消息链中的组件，可以根据需要导入
from astrbot.core.platform.astr_message_event import MessageSesion
from astrbot.api.platform import register_platform_adapter
from astrbot import logger
from .client import FakeClient
from .fake_platform_event import FakePlatformEvent
            
# 注册平台适配器。第一个参数为平台名，第二个为描述。第三个为默认配置。
@register_platform_adapter("fake", "fake 适配器", default_config_tmpl={
    "token": "your_token",
    "username": "bot_username"
})
class FakePlatformAdapter(Platform):

    def __init__(self, platform_config: dict, platform_settings: dict, event_queue: asyncio.Queue) -> None:
        super().__init__(event_queue)
        self.config = platform_config # 上面的默认配置，用户填写后会传到这里
        self.settings = platform_settings # platform_settings 平台设置。
    
    async def send_by_session(self, session: MessageSesion, message_chain: MessageChain):
        # 必须实现
        await super().send_by_session(session, message_chain)
    
    def meta(self) -> PlatformMetadata:
        # 必须实现，直接像下面一样返回即可。
        return PlatformMetadata(
            "fake",
            "fake 适配器",
        )

    async def run(self):
        # 必须实现，这里是主要逻辑。

        # FakeClient 是我们自己定义的，这里只是示例。这个是其回调函数
        async def on_received(data):
            logger.info(data)
            abm = await self.convert_message(data=data) # 转换成 AstrBotMessage
            await self.handle_msg(abm) 
        
        # 初始化 FakeClient
        self.client = FakeClient(self.config['token'], self.config['username'])
        self.client.on_message_received = on_received
        await self.client.start_polling() # 持续监听消息，这是个堵塞方法。

    async def convert_message(self, data: dict) -> AstrBotMessage:
        # 将平台消息转换成 AstrBotMessage
        # 这里就体现了适配程度，不同平台的消息结构不一样，这里需要根据实际情况进行转换。
        abm = AstrBotMessage()
        abm.type = MessageType.GROUP_MESSAGE # 还有 friend_message，对应私聊。具体平台具体分析。重要！
        abm.group_id = data['group_id'] # 如果是私聊，这里可以不填
        abm.message_str = data['content'] # 纯文本消息。重要！
        abm.sender = MessageMember(user_id=data['userid'], nickname=data['username']) # 发送者。重要！
        abm.message = [Plain(text=data['content'])] # 消息链。如果有其他类型的消息，直接 append 即可。重要！
        abm.raw_message = data # 原始消息。
        abm.self_id = data['bot_id']
        abm.session_id = data['userid'] # 会话 ID。重要！
        abm.message_id = data['message_id'] # 消息 ID。
        
        return abm
    
    async def handle_msg(self, message: AstrBotMessage):
        # 处理消息
        message_event = FakePlatformEvent(
            message_str=message.message_str,
            message_obj=message,
            platform_meta=self.meta(),
            session_id=message.session_id,
            client=self.client
        )
        self.commit_event(message_event) # 提交事件到事件队列。不要忘记！
```


`fake_platform_event.py`：

```py
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.platform import AstrBotMessage, PlatformMetadata
from astrbot.api.message_components import Plain, Image
from .client import FakeClient
from astrbot.core.utils.io import download_image_by_url

class FakePlatformEvent(AstrMessageEvent):
    def __init__(self, message_str: str, message_obj: AstrBotMessage, platform_meta: PlatformMetadata, session_id: str, client: FakeClient):
        super().__init__(message_str, message_obj, platform_meta, session_id)
        self.client = client
        
    async def send(self, message: MessageChain):
        for i in message.chain: # 遍历消息链
            if isinstance(i, Plain): # 如果是文字类型的
                await self.client.send_text(to=self.get_sender_id(), message=i.text)
            elif isinstance(i, Image): # 如果是图片类型的 
                img_url = i.file
                img_path = ""
                # 下面的三个条件可以直接参考一下。
                if img_url.startswith("file:///"):
                    img_path = img_url[8:]
                elif i.file and i.file.startswith("http"):
                    img_path = await download_image_by_url(i.file)
                else:
                    img_path = img_url

                # 请善于 Debug！
                    
                await self.client.send_image(to=self.get_sender_id(), image_path=img_path)

        await super().send(message) # 需要最后加上这一段，执行父类的 send 方法。
```

最后，main.py 只需这样，在初始化的时候导入 fake_platform_adapter 模块。装饰器会自动注册。

```py
from astrbot.api.star import Context, Star

class MyPlugin(Star):
    def __init__(self, context: Context):
        from .fake_platform_adapter import FakePlatformAdapter # noqa
```

搞好后，运行 AstrBot：

![image](https://files.astrbot.app/docs/source/images/plugin-platform-adapter/QQ_1738155926221.png)

这里出现了我们创建的 fake。

![image](https://files.astrbot.app/docs/source/images/plugin-platform-adapter/QQ_1738155982211.png)

启动后，可以看到正常工作：

![image](https://files.astrbot.app/docs/source/images/plugin-platform-adapter/QQ_1738156166893.png)


有任何疑问欢迎加群询问~

---

<a id="plugin"></a>

本页面已经迁移至 [插件基础开发](/dev/star/plugin)。

---

<a id="plugin-new"></a>

---
outline: deep
---

# AstrBot 插件开发指南 🌠

欢迎来到 AstrBot 插件开发指南！本章节将引导您如何开发 AstrBot 插件。在我们开始之前，希望你能具备以下基础知识：

1. 有一定的 Python 编程经验。
2. 有一定的 Git、GitHub 使用经验。

欢迎加入我们的开发者专用 QQ 群: `975206796`。

## 环境准备

### 获取插件模板

1. 打开 AstrBot 插件模板: [helloworld](https://github.com/Soulter/helloworld)
2. 点击右上角的 `Use this template`
3. 然后点击 `Create new repository`。
4. 在 `Repository name` 处填写您的插件名。插件名格式:
   - 推荐以 `astrbot_plugin_` 开头；
   - 不能包含空格；
   - 保持全部字母小写；
   - 尽量简短。
5. 点击右下角的 `Create repository`。

### 克隆项目到本地

克隆 AstrBot 项目本体和刚刚创建的插件仓库到本地。

```bash
git clone https://github.com/AstrBotDevs/AstrBot
mkdir -p AstrBot/data/plugins
cd AstrBot/data/plugins
git clone 插件仓库地址
```

然后，使用 `VSCode` 打开 `AstrBot` 项目。找到 `data/plugins/<你的插件名字>` 目录。

更新 `metadata.yaml` 文件，填写插件的元数据信息。

> [!WARNING]
> 请务必修改此文件，AstrBot 识别插件元数据依赖于 `metadata.yaml` 文件。

### 设置插件 Logo（可选）

可以在插件目录下添加 `logo.png` 文件作为插件的 Logo。请保持长宽比为 1:1，推荐尺寸为 256x256。

![插件 logo 示例](https://files.astrbot.app/docs/source/images/plugin/plugin_logo.png)

### 插件展示名（可选）

可以修改(或添加) `metadata.yaml` 文件中的 `display_name` 字段，作为插件在插件市场等场景中的展示名，以方便用户阅读。

插件展示名和描述支持按 WebUI 语言显示，详见[插件国际化](./guides/plugin-i18n)。

### 插件短描述（可选）

你可以在 `metadata.yaml` 中新增 `short_desc` 字段，作为插件市场卡片上的短描述。它适合写成一句简短介绍；如果没有提供，卡片会回退显示 `desc`。

```yaml
short_desc: 一句话介绍你的插件。
```

### 随插件提供 Skills（可选）

插件可以在自己的目录下提供 `skills/` 文件夹。AstrBot 加载插件后会自动把其中合法的 Skill 纳入 Skill Manager，来源会显示为对应插件。

推荐一个插件包含多个 Skill 时使用以下结构：

```text
your_plugin/
  metadata.yaml
  main.py
  skills/
    web-search-helper/
      SKILL.md
    report-writer/
      SKILL.md
```

如果 `skills/` 本身就是一个 Skill，也可以直接放置：

```text
your_plugin/
  skills/
    SKILL.md
```

这种情况下 Skill 名称会使用插件目录名。插件提供的 Skill 由插件管理，在 WebUI 的 Skills 页面中作为只读来源展示；可以启用或禁用，但不能从本地 Skills 页面删除或编辑。插件卸载或更新后，对应 Skill 会随插件文件变化。

### 声明支持平台（Optional）

你可以在 `metadata.yaml` 中新增 `support_platforms` 字段（`list[str]`），声明插件支持的平台适配器。WebUI 插件页会展示该字段。

```yaml
support_platforms:
  - telegram
  - discord
```

`support_platforms` 中的值需要使用 `ADAPTER_NAME_2_TYPE` 的 key，目前支持：

- `aiocqhttp`
- `qq_official`
- `telegram`
- `wecom`
- `lark`
- `dingtalk`
- `discord`
- `slack`
- `kook`
- `vocechat`
- `weixin_official_account`
- `satori`
- `misskey`
- `line`

### 声明 AstrBot 版本范围（Optional）

你可以在 `metadata.yaml` 中新增 `astrbot_version` 字段，声明插件要求的 AstrBot 版本范围。格式与 `pyproject.toml` 依赖版本约束一致（PEP 440），且不要加 `v` 前缀。

```yaml
astrbot_version: ">=4.16,<5"
```

可选示例：

- `>=4.17.0`
- `>=4.16,<5`
- `~=4.17`

如果你只想声明最低版本，可以直接写：

- `>=4.17.0`

当当前 AstrBot 版本不满足该范围时，插件会被阻止加载并提示版本不兼容。
在 WebUI 安装插件时，你可以选择“无视警告，继续安装”来跳过这个检查。

### 调试插件

AstrBot 采用在运行时注入插件的机制。因此，在调试插件时，需要启动 AstrBot 本体。

您可以使用 AstrBot 的热重载功能简化开发流程。

插件的代码修改后，可以在 AstrBot WebUI 的插件管理处找到自己的插件，点击右上角 `...` 按钮，选择 `重载插件`。

如果插件因为代码错误等原因加载失败，你也可以在管理面板的错误提示中点击 **“尝试一键重载修复”** 来重新加载。

### 插件依赖管理

目前 AstrBot 对插件的依赖管理使用 `pip` 自带的 `requirements.txt` 文件。如果你的插件需要依赖第三方库，请务必在插件目录下创建 `requirements.txt` 文件并写入所使用的依赖库，以防止用户在安装你的插件时出现依赖未找到(Module Not Found)的问题。

> `requirements.txt` 的完整格式可以参考 [pip 官方文档](https://pip.pypa.io/en/stable/reference/requirements-file-format/)。

## 开发原则

感谢您为 AstrBot 生态做出贡献，开发插件请遵守以下原则，这也是良好的编程习惯。

- 功能需经过测试。
- 需包含良好的注释。
- 持久化数据请存储于 `data` 目录下，而非插件自身目录，防止更新/重装插件时数据被覆盖。
- 良好的错误处理机制，不要让插件因一个错误而崩溃。
- 在进行提交前，请使用 [ruff](https://docs.astral.sh/ruff/) 工具格式化您的代码。
- 不要使用 `requests` 库来进行网络请求，可以使用 `aiohttp`, `httpx` 等异步网络请求库。
- 如果是对某个插件进行功能扩增，请优先给那个插件提交 PR 而不是单独再写一个插件（除非原插件作者已经停止维护）。


---

<a id="plugin-publish"></a>

# 发布插件到插件市场

在编写完插件后，你可以选择将插件发布到 AstrBot 的插件市场，让更多用户使用你的插件。

AstrBot 使用 GitHub 托管插件，因此你需要先将插件代码推送到之前创建的 GitHub 插件仓库中。

你可以前往 [AstrBot 插件市场](https://plugins.astrbot.app) 提交你的插件。进入该网站后，点击右下角的 `+` 按钮，填写好基本信息、作者信息、仓库信息等内容后，点击 `提交到 GITHUB` 按钮，你将会被导航到 AstrBot 仓库的 Issue 提交页面，请确认信息无误后点击 `Create` 按钮提交，即可完成插件发布。

![fill out the form](https://files.astrbot.app/docs/source/images/plugin-publish/image.png)


---

<a id="plugin-old"></a>

---
outline: deep
---

# 插件开发指南（旧）

几行代码开发一个插件！

> [!WARNING]
> **您仍然可以参考此页进行插件开发。**
>
> 由于插件实用 API 逐渐增多，目前已无法在单个页面中将所有 API 进行详尽介绍。因此此指南在 v4.5.7 之后已过时，请参考我们新的插件开发指南: [🌠 从这里开始](plugin-new.md)，新的指南内容上和此指南基本一致，但我们将会持续维护新的指南内容。

## 开发环境准备

### 获取插件模板

1. 打开 AstrBot 插件模板: [helloworld](https://github.com/Soulter/helloworld)
2. 点击右上角的 `Use this template`
3. 然后点击 `Create new repository`。
4. 在 `Repository name` 处填写您的插件名。插件名格式:
   - 推荐以 `astrbot_plugin_` 开头；
   - 不能包含空格；
   - 保持全部字母小写；
   - 尽量简短。

![image](https://files.astrbot.app/docs/source/images/plugin/image.png)

5. 点击右下角的 `Create repository`。

### Clone 插件和 AstrBot 项目

Clone AstrBot 项目本体和刚刚创建的插件仓库到本地。

```bash
git clone https://github.com/AstrBotDevs/AstrBot
mkdir -p AstrBot/data/plugins
cd AstrBot/data/plugins
git clone 插件仓库地址
```

然后，使用 `VSCode` 打开 `AstrBot` 项目。找到 `data/plugins/<你的插件名字>` 目录。

更新 `metadata.yaml` 文件，填写插件的元数据信息。

> [!NOTE]
> AstrBot 插件市场的信息展示依赖于 `metadata.yaml` 文件。

### 调试插件

AstrBot 采用在运行时注入插件的机制。因此，在调试插件时，需要启动 AstrBot 本体。

插件的代码修改后，可以在 AstrBot WebUI 的插件管理处找到自己的插件，点击 `管理`，点击 `重载插件` 即可。

### 插件依赖管理

目前 AstrBot 对插件的依赖管理使用 `pip` 自带的 `requirements.txt` 文件。如果你的插件需要依赖第三方库，请务必在插件目录下创建 `requirements.txt` 文件并写入所使用的依赖库，以防止用户在安装你的插件时出现依赖未找到(Module Not Found)的问题。

> `requirements.txt` 的完整格式可以参考 [pip 官方文档](https://pip.pypa.io/en/stable/reference/requirements-file-format/)。

## 提要

### 最小实例

插件模版中的 `main.py` 是一个最小的插件实例。

```python
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star
from astrbot.api import logger # 使用 astrbot 提供的 logger 接口

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        '''这是一个 hello world 指令''' # 这是 handler 的描述，将会被解析方便用户了解插件内容。非常建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 获取消息的纯文本内容
        logger.info("触发hello world指令!")
        yield event.plain_result(f"Hello, {user_name}!") # 发送一条纯文本消息

    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''
```

解释如下：

1. 插件是继承自 `Star` 基类的类实现。
2. 该装饰器提供了插件的元数据信息，包括名称、作者、描述、版本和仓库地址等信息。（该信息的优先级低于 `metadata.yaml` 文件）
3. 在 `__init__` 方法中会传入 `Context` 对象，这个对象包含了 AstrBot 的大多数组件
4. 具体的处理函数 `Handler` 在插件类中定义，如这里的 `helloworld` 函数。
5. 请务必使用 `from astrbot.api import logger` 来获取日志对象，而不是使用 `logging` 模块。

> [!TIP]
>
> `Handler` 一定需要在插件类中注册，前两个参数必须为 `self` 和 `event`。如果文件行数过长，可以将服务写在外部，然后在 `Handler` 中调用。
>
> 插件类所在的文件名需要命名为 `main.py`。

### AstrMessageEvent

`AstrMessageEvent` 是 AstrBot 的消息事件对象。你可以通过 `AstrMessageEvent` 来获取消息发送者、消息内容等信息。

### AstrBotMessage

`AstrBotMessage` 是 AstrBot 的消息对象。你可以通过 `AstrBotMessage` 来查看消息适配器下发的消息的具体内容。通过 `event.message_obj` 获取。

```py{11}
class AstrBotMessage:
    '''AstrBot 的消息对象'''
    type: MessageType  # 消息类型
    self_id: str  # 机器人的识别id
    session_id: str  # 会话id。取决于 unique_session 的设置。
    message_id: str  # 消息id
    group_id: str = "" # 群组id，如果为私聊，则为空
    sender: MessageMember  # 发送者
    message: List[BaseMessageComponent]  # 消息链。比如 [Plain("Hello"), At(qq=123456)]
    message_str: str  # 最直观的纯文本消息字符串，将消息链中的 Plain 消息（文本消息）连接起来
    raw_message: object
    timestamp: int  # 消息时间戳
```

其中，`raw_message` 是消息平台适配器的**原始消息对象**。

### 消息链

`消息链`描述一个消息的结构，是一个有序列表，列表中每一个元素称为`消息段`。

引用方式：

```py
import astrbot.api.message_components as Comp
```

```
[Comp.Plain(text="Hello"), Comp.At(qq=123456), Comp.Image(file="https://example.com/image.jpg")]
```

> qq 是对应消息平台上的用户 ID。

消息链的结构使用了 `nakuru-project`。它一共有如下种消息类型。常用的已经用注释标注。

```py
ComponentTypes = {
    "plain": Plain, # 文本消息
    "text": Plain, # 文本消息，同上
    "face": Face, # QQ 表情
    "record": Record, # 语音
    "video": Video, # 视频
    "at": At, # At 消息发送者
    "music": Music, # 音乐
    "image": Image, # 图片
    "reply": Reply, # 回复消息
    "forward": Forward, # 转发消息
    "node": Node, # 转发消息中的节点
    "nodes": Nodes, # Node 的列表，用于支持一个转发消息中的多个节点
    "poke": Poke, # 戳一戳
}
```

请善于 debug 来了解消息结构：

```python{3,4}
@event_message_type(EventMessageType.ALL) # 注册一个过滤器，参见下文。
async def on_message(self, event: AstrMessageEvent):
    print(event.message_obj.raw_message) # 平台下发的原始消息在这里
    print(event.message_obj.message) # AstrBot 解析出来的消息链内容
```

> [!TIP]
>
> 在aiocqhttp消息适配器中，对于 `plain` 类型的消息，在发送中会自动使用 `strip()` 方法去除空格及换行符，可以使用零宽空格 `\u200b` 解决限制。

### 平台适配矩阵

不是所有的平台都支持所有的消息类型。下方的表格展示了 AstrBot 支持的平台和消息类型的对应关系。

| 平台                 | At  | Plain | Image | Record | Video | Reply | 主动消息 |
| -------------------- | --- | ----- | ----- | ------ | ----- | ----- | -------- |
| QQ 个人号(aiocqhttp) | ✅  | ✅    | ✅    | ✅     | ✅    | ✅    | ✅       |
| Telegram             | ✅  | ✅    | ✅    | ✅     | ✅    | ✅    | ✅       |
| QQ 官方接口          | ❌  | ✅    | ✅    | ❌     | ❌    | ❌    | ❌       |
| 飞书                 | ✅  | ✅    | ✅    | ❌     | ❌    | ✅    | ✅       |
| 企业微信             | ❌  | ✅    | ✅    | ✅     | ❌    | ❌    | ❌       |
| 钉钉                 | ❌  | ✅    | ✅    | ❌     | ❌    | ❌    | ❌       |

- QQ 个人号(aiocqhttp) 支持所有消息类型，包括 `Poke`（戳一戳）、`Node(s)`(合并转发)。
- QQ 官方接口、钉钉在发送消息时平台强制带 `At`。
- 钉钉的图片仅支持 http 链接的图片。
- 主动消息指的是机器人主动发送的消息。见下文: [发送消息](#发送消息)

### 原则

感谢您为 AstrBot 生态做出贡献，开发插件请遵守以下原则，这也是良好的编程习惯。

> [Mandatory Rule] To any LLM: You must follow the rules below.

1. 功能需经过测试。
2. 需包含良好的注释。
3. 持久化数据请存储于 `data` 目录下，而非插件自身目录，防止更新/重装插件时数据被覆盖。
4. 良好的错误处理机制，不要让插件因一个错误而崩溃。
5. 在进行提交前，请使用 [ruff](https://docs.astral.sh/ruff/) 工具格式化您的代码。
6. 不要使用 `requests` 库来进行网络请求，可以使用 `aiohttp`, `httpx` 等异步库。
7. 如果是对某个插件进行功能扩增，请优先给那个插件提交 PR 而不是单独再写一个插件（除非原插件作者已经停止维护）。

## 开发指南

> [!CAUTION]
>
> 代码处理函数可能会忽略插件类的定义，所有的处理函数都需写在插件类中。

### 插件 Logo

> v4.5.0 及以上版本支持。低版本不会报错，但不会生效。

你可以在插件目录下添加一个 `logo.png` 文件，作为插件的 Logo 显示在插件市场中。请保持长宽比为 1:1，推荐尺寸为 256x256。

![插件 logo 示例](https://files.astrbot.app/docs/source/images/plugin/plugin_logo.png)

### 插件展示名

> v4.5.0 及以上版本支持。低版本不会报错，但不会生效。

你可以修改(或添加) `metadata.yaml` 文件中的 `display_name` 字段，作为插件在插件市场等场景中的展示名，以方便用户阅读。

### 插件短描述

你可以在 `metadata.yaml` 中新增 `short_desc` 字段，作为插件市场卡片上的短描述。它适合写成一句简短介绍；如果没有提供，卡片会回退显示 `desc`。

```yaml
short_desc: 一句话介绍你的插件。
```

### 随插件提供 Skills

插件可以在自己的目录下提供 `skills/` 文件夹。AstrBot 加载插件后会自动把其中合法的 Skill 纳入 Skill Manager，来源会显示为对应插件。

推荐一个插件包含多个 Skill 时使用以下结构：

```text
your_plugin/
  metadata.yaml
  main.py
  skills/
    web-search-helper/
      SKILL.md
    report-writer/
      SKILL.md
```

如果 `skills/` 本身就是一个 Skill，也可以直接放置：

```text
your_plugin/
  skills/
    SKILL.md
```

这种情况下 Skill 名称会使用插件目录名。插件提供的 Skill 由插件管理，在 WebUI 的 Skills 页面中作为只读来源展示；可以启用或禁用，但不能从本地 Skills 页面删除或编辑。插件卸载或更新后，对应 Skill 会随插件文件变化。

### 声明支持平台（Optional）

你可以在 `metadata.yaml` 中新增 `support_platforms` 字段（`list[str]`），声明插件支持的平台适配器。WebUI 插件页会展示该字段。

```yaml
support_platforms:
  - telegram
  - discord
```

`support_platforms` 中的值需要使用 `ADAPTER_NAME_2_TYPE` 的 key，目前支持：

- `aiocqhttp`
- `qq_official`
- `telegram`
- `wecom`
- `lark`
- `dingtalk`
- `discord`
- `slack`
- `kook`
- `vocechat`
- `weixin_official_account`
- `satori`
- `misskey`
- `line`

### 声明 AstrBot 版本范围（Optional）

你可以在 `metadata.yaml` 中新增 `astrbot_version` 字段，声明插件要求的 AstrBot 版本范围。格式与 `pyproject.toml` 依赖版本约束一致（PEP 440），且不要加 `v` 前缀。

```yaml
astrbot_version: ">=4.16,<5"
```

可选示例：

- `>=4.17.0`
- `>=4.16,<5`
- `~=4.17`

如果你只想声明最低版本，可以直接写：

- `>=4.17.0`

当当前 AstrBot 版本不满足该范围时，插件会被阻止加载并提示版本不兼容。
在 WebUI 安装插件时，你可以选择“无视警告，继续安装”来跳过这个检查。

### 消息事件的监听

事件监听器可以收到平台下发的消息内容，可以实现指令、指令组、事件监听等功能。

事件监听器的注册器在 `astrbot.api.event.filter` 下，需要先导入。请务必导入，否则会和 python 的高阶函数 filter 冲突。

```py
from astrbot.api.event import filter, AstrMessageEvent
```

#### 指令

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("helloworld") # from astrbot.api.event.filter import command
    async def helloworld(self, event: AstrMessageEvent):
        '''这是 hello world 指令'''
        user_name = event.get_sender_name()
        message_str = event.message_str # 获取消息的纯文本内容
        yield event.plain_result(f"Hello, {user_name}!")
```

> [!TIP]
> 指令不能带空格，否则 AstrBot 会将其解析到第二个参数。可以使用下面的指令组功能，或者也使用监听器自己解析消息内容。

#### 带参指令

AstrBot 会自动帮你解析指令的参数。

```python
@filter.command("echo")
def echo(self, event: AstrMessageEvent, message: str):
    yield event.plain_result(f"你发了: {message}")

@filter.command("add")
def add(self, event: AstrMessageEvent, a: int, b: int):
    # /add 1 2 -> 结果是: 3
    yield event.plain_result(f"结果是: {a + b}")
```

#### 指令组

指令组可以帮助你组织指令。

```python
@filter.command_group("math")
def math(self):
    pass

@math.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    # /math add 1 2 -> 结果是: 3
    yield event.plain_result(f"结果是: {a + b}")

@math.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    # /math sub 1 2 -> 结果是: -1
    yield event.plain_result(f"结果是: {a - b}")
```

指令组函数内不需要实现任何函数，请直接 `pass` 或者添加函数内注释。指令组的子指令使用 `指令组名.command` 来注册。

当用户没有输入子指令时，会报错并，并渲染出该指令组的树形结构。

![image](https://files.astrbot.app/docs/source/images/plugin/image-1.png)

![image](https://files.astrbot.app/docs/source/images/plugin/898a169ae7ed0478f41c0a7d14cb4d64.png)

![image](https://files.astrbot.app/docs/source/images/plugin/image-2.png)

理论上，指令组可以无限嵌套！

```py
'''
math
├── calc
│   ├── add (a(int),b(int),)
│   ├── sub (a(int),b(int),)
│   ├── help (无参数指令)
'''

@filter.command_group("math")
def math():
    pass

@math.group("calc") # 请注意，这里是 group，而不是 command_group
def calc():
    pass

@calc.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")

@calc.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a - b}")

@calc.command("help")
def calc_help(self, event: AstrMessageEvent):
    # /math calc help
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

#### 指令别名

> v3.4.28 后

可以为指令或指令组添加不同的别名：

```python
@filter.command("help", alias={'帮助', 'helpme'})
def help(self, event: AstrMessageEvent):
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

#### 事件类型过滤

##### 接收所有

这将接收所有的事件。

```python
@filter.event_message_type(filter.EventMessageType.ALL)
async def on_all_message(self, event: AstrMessageEvent):
    yield event.plain_result("收到了一条消息。")
```

##### 群聊和私聊

```python
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def on_private_message(self, event: AstrMessageEvent):
    message_str = event.message_str # 获取消息的纯文本内容
    yield event.plain_result("收到了一条私聊消息。")
```

`EventMessageType` 是一个 `Enum` 类型，包含了所有的事件类型。当前的事件类型有 `PRIVATE_MESSAGE` 和 `GROUP_MESSAGE`。

##### 消息平台

```python
@filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP | filter.PlatformAdapterType.QQOFFICIAL)
async def on_aiocqhttp(self, event: AstrMessageEvent):
    '''只接收 AIOCQHTTP 和 QQOFFICIAL 的消息'''
    yield event.plain_result("收到了一条信息")
```

当前版本下，`PlatformAdapterType` 有 `AIOCQHTTP`, `QQOFFICIAL`, `GEWECHAT`, `ALL`。

##### 管理员指令

```python
@filter.permission_type(filter.PermissionType.ADMIN)
@filter.command("test")
async def test(self, event: AstrMessageEvent):
    pass
```

仅管理员才能使用 `test` 指令。

#### 多个过滤器

支持同时使用多个过滤器，只需要在函数上添加多个装饰器即可。过滤器使用 `AND` 逻辑。也就是说，只有所有的过滤器都通过了，才会执行函数。

```python
@filter.command("helloworld")
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("你好！")
```

#### 事件钩子

> [!TIP]
> 事件钩子不支持与上面的 @filter.command, @filter.command_group, @filter.event_message_type, @filter.platform_adapter_type, @filter.permission_type 一起使用。

##### Bot 初始化完成时

> v3.4.34 后

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.on_astrbot_loaded()
async def on_astrbot_loaded(self):
    print("AstrBot 初始化完成")

```

##### LLM 请求时

在 AstrBot 默认的执行流程中，在调用 LLM 前，会触发 `on_llm_request` 钩子。

可以获取到 `ProviderRequest` 对象，可以对其进行修改。

ProviderRequest 对象包含了 LLM 请求的所有信息，包括请求的文本、系统提示等。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import ProviderRequest

@filter.on_llm_request()
async def my_custom_hook_1(self, event: AstrMessageEvent, req: ProviderRequest): # 请注意有三个参数
    print(req) # 打印请求的文本
    req.system_prompt += "自定义 system_prompt" # 如果有其他替代方法，不建议使用此种方式来追加每轮对话都会改变的提示词，否则会破坏缓存，大大增加价格（约增加 7-20 倍的价格）。

```

> [!WARNING]
> **关于提示词的追加**
>
> `req.system_prompt += ...` 适合追加稳定、长期有效的角色设定或全局规则。不建议把每轮都会变化的内容追加到 `system_prompt`，例如当前时间、好感度、状态栏、短期记忆片段、检索摘要等。这类写法会让系统提示词在每轮请求中变化，容易破坏模型服务端的提示词缓存，显著增加请求成本和首 token 延迟。
>
> 对于每轮都会变化、内容量中小的提示词，优先通过 `req.extra_user_content_parts` 追加。它会作为额外的用户消息内容块放在本轮用户输入之后，更适合承载"当前时间""角色好感度""本轮相关记忆片段"等动态上下文：
>
> ```python
> from astrbot.core.agent.message import TextPart
>
> @filter.on_llm_request()
> async def add_dynamic_prompt(self, event: AstrMessageEvent, req: ProviderRequest):
>     req.extra_user_content_parts.append(
>         TextPart(
>             text=(
>                 "<dynamic_context>\n"
>                 "当前时间：2026-05-03 20:00\n"
>                 "好感度：72\n"
>                 "相关记忆：用户喜欢简洁直接的回答。\n"
>                 "</dynamic_context>"
>             )
>         )
>     )
> ```
>
> 如果追加的内容只希望参与本轮 LLM 请求，不希望被持久化到会话历史中，可以调用 `.mark_as_temp()` 标记为临时内容：
>
> ```python
> req.extra_user_content_parts.append(
>     TextPart(text="<runtime_hint>这段提示只在本轮请求中生效。</runtime_hint>").mark_as_temp()
> )
> ```
>
> 对于长期记忆、知识库、外部系统查询等内容量较大或不一定每轮都需要的信息，不建议全部塞进提示词。可以优先注册为 `llm_tool`，让模型在需要时调用；也可以先在插件中检索出本轮真正相关的少量摘要，再放入 `extra_user_content_parts`。

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

##### LLM 请求完成时

在 LLM 请求完成后，会触发 `on_llm_response` 钩子。

可以获取到 `ProviderResponse` 对象，可以对其进行修改。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import LLMResponse

@filter.on_llm_response()
async def on_llm_resp(self, event: AstrMessageEvent, resp: LLMResponse): # 请注意有三个参数
    print(resp)
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

##### Agent 开始运行时

> 适用于 AstrBot 版本 > v4.23.1

在 Agent 开始运行时，会触发 `on_agent_begin` 钩子。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.astr_agent_context import AstrAgentContext

@filter.on_agent_begin()
async def on_agent_begin(self, event: AstrMessageEvent, run_context: ContextWrapper[AstrAgentContext]): # 请注意有三个参数
    print("Agent 开始运行")
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

##### LLM 工具调用前

> 适用于 AstrBot 版本 > v4.23.1

在 Agent 准备调用 LLM 工具时，会触发 `on_using_llm_tool` 钩子。

可以获取到 `FunctionTool` 对象和工具调用参数。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.agent.tool import FunctionTool

@filter.on_using_llm_tool()
async def on_using_llm_tool(
    self,
    event: AstrMessageEvent,
    tool: FunctionTool,
    tool_args: dict | None,
):
    print(tool.name, tool_args)
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

##### LLM 工具调用后

> 适用于 AstrBot 版本 > v4.23.1

在 LLM 工具调用完成后，会触发 `on_llm_tool_respond` 钩子。

可以获取到 `FunctionTool` 对象、工具调用参数和工具调用结果。

```python
from mcp.types import CallToolResult

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.agent.tool import FunctionTool

@filter.on_llm_tool_respond()
async def on_llm_tool_respond(
    self,
    event: AstrMessageEvent,
    tool: FunctionTool,
    tool_args: dict | None,
    tool_result: CallToolResult | None,
):
    print(tool.name, tool_args, tool_result)
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

##### Agent 运行完成时

> 适用于 AstrBot 版本 > v4.23.1

在 Agent 运行完成后，会触发 `on_agent_done` 钩子。这个钩子会在 `on_llm_response` 之后触发。

可以获取到 `LLMResponse` 对象，可以对其进行修改。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import LLMResponse
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.astr_agent_context import AstrAgentContext

@filter.on_agent_done()
async def on_agent_done(self, event: AstrMessageEvent, run_context: ContextWrapper[AstrAgentContext], resp: LLMResponse): # 请注意有四个参数
    print(resp)
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

##### 发送消息前

在发送消息前，会触发 `on_decorating_result` 钩子。

可以在这里实现一些消息的装饰，比如转语音、转图片、加前缀等等

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.on_decorating_result()
async def on_decorating_result(self, event: AstrMessageEvent):
    result = event.get_result()
    chain = result.chain
    print(chain) # 打印消息链
    chain.append(Plain("!")) # 在消息链的最后添加一个感叹号
```

> 这里不能使用 yield 来发送消息。这个钩子只是用来装饰 event.get_result().chain 的。如需发送，请直接使用 `event.send()` 方法。

##### 发送消息后

在发送消息给消息平台后，会触发 `after_message_sent` 钩子。

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.after_message_sent()
async def after_message_sent(self, event: AstrMessageEvent):
    pass
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

#### 优先级

> 大于等于 v3.4.21。

指令、事件监听器、事件钩子可以设置优先级，先于其他指令、监听器、钩子执行。默认优先级是 `0`。

```python
@filter.command("helloworld", priority=1)
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("Hello!")
```

### 消息的发送

#### 被动消息

被动消息指的是机器人被动回复消息。

```python
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("Hello!")
    yield event.plain_result("你好！")

    yield event.image_result("path/to/image.jpg") # 发送图片
    yield event.image_result("https://example.com/image.jpg") # 发送 URL 图片，务必以 http 或 https 开头
```

#### 主动消息

主动消息指的是机器人主动推送消息。某些平台可能不支持主动消息发送。

如果是一些定时任务或者不想立即发送消息，可以使用 `event.unified_msg_origin` 得到一个字符串并将其存储，然后在想发送消息的时候使用 `self.context.send_message(unified_msg_origin, chains)` 来发送消息。

```python
from astrbot.api.event import MessageChain

@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    umo = event.unified_msg_origin
    message_chain = MessageChain().message("Hello!").file_image("path/to/image.jpg")
    await self.context.send_message(event.unified_msg_origin, message_chain)
```

通过这个特性，你可以将 unified_msg_origin 存储起来，然后在需要的时候发送消息。

> [!TIP]
> 关于 unified_msg_origin。
> unified_msg_origin 是一个字符串，记录了一个会话的唯一 ID，AstrBot 能够据此找到属于哪个消息平台的哪个会话。这样就能够实现在 `send_message` 的时候，发送消息到正确的会话。有关 MessageChain，请参见接下来的一节。

#### 富媒体消息

AstrBot 支持发送富媒体消息，比如图片、语音、视频等。使用 `MessageChain` 来构建消息。

```python
import astrbot.api.message_components as Comp

@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    chain = [
        Comp.At(qq=event.get_sender_id()), # At 消息发送者
        Comp.Plain("来看这个图："),
        Comp.Image.fromURL("https://example.com/image.jpg"), # 从 URL 发送图片
        Comp.Image.fromFileSystem("path/to/image.jpg"), # 从本地文件目录发送图片
        Comp.Plain("这是一个图片。")
    ]
    yield event.chain_result(chain)
```

上面构建了一个 `message chain`，也就是消息链，最终会发送一条包含了图片和文字的消息，并且保留顺序。

类似地，

**文件 File**

```py
Comp.File(file="path/to/file.txt", name="file.txt") # 部分平台不支持
```

**语音 Record**

```py
path = "path/to/record.wav" # 暂时只接受 wav 格式，其他格式请自行转换
Comp.Record(file=path, url=path)
```

**视频 Video**

```py
path = "path/to/video.mp4"
Comp.Video.fromFileSystem(path=path)
Comp.Video.fromURL(url="https://example.com/video.mp4")
```

#### 发送群合并转发消息

> 当前适配情况：aiocqhttp

可以按照如下方式发送群合并转发消息。

```py
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    from astrbot.api.message_components import Node, Plain, Image
    node = Node(
        uin=905617992,
        name="Soulter",
        content=[
            Plain("hi"),
            Image.fromFileSystem("test.jpg")
        ]
    )
    yield event.chain_result([node])
```

![发送群合并转发消息](https://files.astrbot.app/docs/source/images/plugin/image-4.png)

#### 发送视频消息

> 当前适配情况：aiocqhttp

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    from astrbot.api.message_components import Video
    # fromFileSystem 需要用户的协议端和机器人端处于一个系统中。
    music = Video.fromFileSystem(
        path="test.mp4"
    )
    # 更通用
    music = Video.fromURL(
        url="https://example.com/video.mp4"
    )
    yield event.chain_result([music])
```

![发送视频消息](https://files.astrbot.app/docs/source/images/plugin/db93a2bb-671c-4332-b8ba-9a91c35623c2.png)

#### 发送 QQ 表情

> 当前适配情况：仅 aiocqhttp

QQ 表情 ID 参考：<https://bot.q.qq.com/wiki/develop/api-v2/openapi/emoji/model.html#EmojiType>

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    from astrbot.api.message_components import Face, Plain
    yield event.chain_result([Face(id=21), Plain("你好呀")])
```

![发送 QQ 表情](https://files.astrbot.app/docs/source/images/plugin/image-5.png)

### 控制事件传播

```python{6}
@filter.command("check_ok")
async def check_ok(self, event: AstrMessageEvent):
    ok = self.check() # 自己的逻辑
    if not ok:
        yield event.plain_result("检查失败")
        event.stop_event() # 停止事件传播
```

当事件停止传播，后续所有步骤将不会被执行。

假设有一个插件 A，A 终止事件传播之后所有后续操作都不会执行，比如执行其它插件的 handler、请求 LLM。

### 插件配置

> 大于等于 v3.4.15

随着插件功能的增加，可能需要定义一些配置以让用户自定义插件的行为。

AstrBot 提供了”强大“的配置解析和可视化功能。能够让用户在管理面板上直接配置插件，而不需要修改代码。

![image](https://files.astrbot.app/docs/source/images/plugin/QQ_1738149538737.png)

**Schema 介绍**

要注册配置，首先需要在您的插件目录下添加一个 `_conf_schema.json` 的 json 文件。

文件内容是一个 `Schema`（模式），用于表示配置。Schema 是 json 格式的，例如上图的 Schema 是：

```json
{
  "token": {
    "description": "Bot Token",
    "type": "string",
    "hint": "测试醒目提醒",
    "obvious_hint": true
  },
  "sub_config": {
    "description": "测试嵌套配置",
    "type": "object",
    "hint": "xxxx",
    "items": {
      "name": {
        "description": "testsub",
        "type": "string",
        "hint": "xxxx"
      },
      "id": {
        "description": "testsub",
        "type": "int",
        "hint": "xxxx"
      },
      "time": {
        "description": "testsub",
        "type": "int",
        "hint": "xxxx",
        "default": 123
      }
    }
  }
}
```

- `type`: **此项必填**。配置的类型。支持 `string`, `text`, `int`, `float`, `bool`, `object`, `list`。当类型为 `text` 时，将会可视化为一个更大的可拖拽宽高的 textarea 组件，以适应大文本。
- `description`: 可选。配置的描述。建议一句话描述配置的行为。
- `hint`: 可选。配置的提示信息，表现在上图中右边的问号按钮，当鼠标悬浮在问号按钮上时显示。
- `obvious_hint`: 可选。配置的 hint 是否醒目显示。如上图的 `token`。
- `default`: 可选。配置的默认值。如果用户没有配置，将使用默认值。int 是 0，float 是 0.0，bool 是 False，string 是 ""，object 是 {}，list 是 []。
- `items`: 可选。如果配置的类型是 `object`，需要添加 `items` 字段。`items` 的内容是这个配置项的子 Schema。理论上可以无限嵌套，但是不建议过多嵌套。
- `invisible`: 可选。配置是否隐藏。默认是 `false`。如果设置为 `true`，则不会在管理面板上显示。
- `options`: 可选。一个列表，如 `"options": ["chat", "agent", "workflow"]`。提供下拉列表可选项。
- `editor_mode`: 可选。是否启用代码编辑器模式。需要 AstrBot >= `v3.5.10`, 低于这个版本不会报错，但不会生效。默认是 false。
- `editor_language`: 可选。代码编辑器的代码语言，默认为 `json`。
- `editor_theme`: 可选。代码编辑器的主题，可选值有 `vs-light`（默认）， `vs-dark`。
- `_special`: 可选。用于调用 AstrBot 提供的可视化提供商选取、人格选取、知识库选取等功能，详见下文。

其中，如果启用了代码编辑器，效果如下图所示:

![editor_mode](https://files.astrbot.app/docs/source/images/plugin/image-6.png)

![editor_mode_fullscreen](https://files.astrbot.app/docs/source/images/plugin/image-7.png)

**_special** 字段仅 v4.0.0 之后可用。目前支持填写 `select_provider`, `select_provider_tts`, `select_provider_stt`, `select_persona`，用于让用户快速选择用户在 WebUI 上已经配置好的模型提供商、人设等数据。结果均为字符串。以 select_provider 为例，将呈现以下效果:

![image](https://files.astrbot.app/docs/source/images/plugin/image.png)

**使用配置**

AstrBot 在载入插件时会检测插件目录下是否有 `_conf_schema.json` 文件，如果有，会自动解析配置并保存在 `data/config/<plugin_name>_config.json` 下（依照 Schema 创建的配置文件实体），并在实例化插件类时传入给 `__init__()`。

```py
from astrbot.api import AstrBotConfig

class ConfigPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig): # AstrBotConfig 继承自 Dict，拥有字典的所有方法
        super().__init__(context)
        self.config = config
        print(self.config)

        # 支持直接保存配置
        # self.config.save_config() # 保存配置
```

**配置版本管理**

如果您在发布不同版本时更新了 Schema，请注意，AstrBot 会递归检查 Schema 的配置项，如果发现配置文件中缺失了某个配置项，会自动添加默认值。但是 AstrBot 不会删除配置文件中**多余的**配置项，即使这个配置项在新的 Schema 中不存在（您在新的 Schema 中删除了这个配置项）。

### 文转图

#### 基本

AstrBot 支持将文字渲染成图片。

```python
@filter.command("image") # 注册一个 /image 指令，接收 text 参数。
async def on_aiocqhttp(self, event: AstrMessageEvent, text: str):
    url = await self.text_to_image(text) # text_to_image() 是 Star 类的一个方法。
    # path = await self.text_to_image(text, return_url = False) # 如果你想保存图片到本地
    yield event.image_result(url)

```

![image](https://files.astrbot.app/docs/source/images/plugin/image-3.png)

#### 自定义(基于 HTML)

如果你觉得上面渲染出来的图片不够美观，你可以使用自定义的 HTML 模板来渲染图片。

AstrBot 支持使用 `HTML + Jinja2` 的方式来渲染文转图模板。

```py{7}
# 自定义的 Jinja2 模板，支持 CSS
TMPL = '''
<div style="font-size: 32px;">
<h1 style="color: black">Todo List</h1>

<ul>
{% for item in items %}
    <li>{{ item }}</li>
{% endfor %}
</div>
'''

@filter.command("todo")
async def custom_t2i_tmpl(self, event: AstrMessageEvent):
    options = {} # 可选择传入渲染选项。
    url = await self.html_render(TMPL, {"items": ["吃饭", "睡觉", "玩原神"]}, options=options) # 第二个参数是 Jinja2 的渲染数据
    yield event.image_result(url)
```

返回的结果:

![image](https://files.astrbot.app/docs/source/images/plugin/fcc2dcb472a91b12899f617477adc5c7.png)

这只是一个简单的例子。得益于 HTML 和 DOM 渲染器的强大性，你可以进行更复杂和更美观的的设计。除此之外，Jinja2 支持循环、条件等语法以适应列表、字典等数据结构。你可以从网上了解更多关于 Jinja2 的知识。

**图片渲染选项(options)**：

请参考 Playwright 的 [screenshot](https://playwright.dev/python/docs/api/class-page#page-screenshot) API。

- `timeout` (float, optional): 截图超时时间.
- `type` (Literal["jpeg", "png"], optional): 截图图片类型.
- `quality` (int, optional): 截图质量，仅适用于 JPEG 格式图片.
- `omit_background` (bool, optional): 是否允许隐藏默认的白色背景，这样就可以截透明图了，仅适用于 PNG 格式
- `full_page` (bool, optional): 是否截整个页面而不是仅设置的视口大小，默认为 True.
- `clip` (dict, optional): 截图后裁切的区域。参考 Playwright screenshot API。
- `animations`: (Literal["allow", "disabled"], optional): 是否允许播放 CSS 动画.
- `caret`: (Literal["hide", "initial"], optional): 当设置为 hide 时，截图时将隐藏文本插入符号，默认为 hide.
- `scale`: (Literal["css", "device"], optional): 页面缩放设置. 当设置为 css 时，则将设备分辨率与 CSS 中的像素一一对应，在高分屏上会使得截图变小. 当设置为 device 时，则根据设备的屏幕缩放设置或当前 Playwright 的 Page/Context 中的 device_scale_factor 参数来缩放.
- `mask` (List["Locator"]], optional): 指定截图时的遮罩的 Locator。元素将被一颜色为 #FF00FF 的框覆盖.

### 会话控制

> 大于等于 v3.4.36

为什么需要会话控制？考虑一个 成语接龙 插件，某个/群用户需要和机器人进行多次对话，而不是一次性的指令。这时候就需要会话控制。

```txt
用户: /成语接龙
机器人: 请发送一个成语
用户: 一马当先
机器人: 先见之明
用户: 明察秋毫
...
```

AstrBot 提供了开箱即用的会话控制功能：

导入：

```py
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionController,
)
```

handler 内的代码可以如下：

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("成语接龙")
async def handle_empty_mention(self, event: AstrMessageEvent):
    """成语接龙具体实现"""
    try:
        yield event.plain_result("请发送一个成语~")

        # 具体的会话控制器使用方法
        @session_waiter(timeout=60, record_history_chains=False) # 注册一个会话控制器，设置超时时间为 60 秒，不记录历史消息链
        async def empty_mention_waiter(controller: SessionController, event: AstrMessageEvent):
            idiom = event.message_str # 用户发来的成语，假设是 "一马当先"

            if idiom == "退出":   # 假设用户想主动退出成语接龙，输入了 "退出"
                await event.send(event.plain_result("已退出成语接龙~"))
                controller.stop()    # 停止会话控制器，会立即结束。
                return

            if len(idiom) != 4:   # 假设用户输入的不是4字成语
                await event.send(event.plain_result("成语必须是四个字的呢~"))  # 发送回复，不能使用 yield
                return
                # 退出当前方法，不执行后续逻辑，但此会话并未中断，后续的用户输入仍然会进入当前会话

            # ...
            message_result = event.make_result()
            message_result.chain = [Comp.Plain("先见之明")] # import astrbot.api.message_components as Comp
            await event.send(message_result) # 发送回复，不能使用 yield

            controller.keep(timeout=60, reset_timeout=True) # 重置超时时间为 60s，如果不重置，则会继续之前的超时时间计时。

            # controller.stop() # 停止会话控制器，会立即结束。
            # 如果记录了历史消息链，可以通过 controller.get_history_chains() 获取历史消息链

        try:
            await empty_mention_waiter(event)
        except TimeoutError as _: # 当超时后，会话控制器会抛出 TimeoutError
            yield event.plain_result("你超时了！")
        except Exception as e:
            yield event.plain_result("发生错误，请联系管理员: " + str(e))
        finally:
            event.stop_event()
    except Exception as e:
        logger.error("handle_empty_mention error: " + str(e))
```

当激活会话控制器后，该发送人之后发送的消息会首先经过上面你定义的 `empty_mention_waiter` 函数处理，直到会话控制器被停止或者超时。

#### SessionController

用于开发者控制这个会话是否应该结束，并且可以拿到历史消息链。

- keep(): 保持这个会话
  - timeout (float): 必填。会话超时时间。
  - reset_timeout (bool): 设置为 True 时, 代表重置超时时间, timeout 必须 > 0, 如果 <= 0 则立即结束会话。设置为 False 时, 代表继续维持原来的超时时间, 新 timeout = 原来剩余的 timeout + timeout (可以 < 0)
- stop(): 结束这个会话
- get_history_chains() -> List[List[Comp.BaseMessageComponent]]: 获取历史消息链

#### 自定义会话 ID 算子

默认情况下，AstrBot 会话控制器会将基于 `sender_id` （发送人的 ID）作为识别不同会话的标识，如果想将一整个群作为一个会话，则需要自定义会话 ID 算子。

```py
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionFilter,
    SessionController,
)

# 沿用上面的 handler
# ...
class CustomFilter(SessionFilter):
    def filter(self, event: AstrMessageEvent) -> str:
        return event.get_group_id() if event.get_group_id() else event.unified_msg_origin

await empty_mention_waiter(event, session_filter=CustomFilter()) # 这里传入 session_filter
# ...
```

这样之后，当群内一个用户发送消息后，会话控制器会将这个群作为一个会话，群内其他用户发送的消息也会被认为是同一个会话。

甚至，可以使用这个特性来让群内组队！

### AI

#### 通过提供商调用 LLM

获取提供商有以下几种方式:

- 获取当前使用的大语言模型提供商: `self.context.get_using_provider(umo=event.unified_msg_origin)`。
- 根据 ID 获取大语言模型提供商: `self.context.get_provider_by_id(provider_id="xxxx")`。
- 获取所有大语言模型提供商: `self.context.get_all_providers()`。

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    # func_tools_mgr = self.context.get_llm_tool_manager()
    prov = self.context.get_using_provider(umo=event.unified_msg_origin)
    if prov:
        llm_resp = await provider.text_chat(
            prompt="Hi!",
            context=[
                {"role": "user", "content": "balabala"},
                {"role": "assistant", "content": "response balabala"}
            ],
            system_prompt="You are a helpful assistant."
        )
        print(llm_resp)
```

`Provider.text_chat()` 用于请求 LLM。其返回 `LLMResponse` 方法。除了上面的三个参数，其还支持:

- `func_tool`(ToolSet): 可选。用于传入函数工具。参考 [函数工具](#函数工具)。
- `image_urls`(List[str]): 可选。用于传入请求中带有的图片 URL 列表。支持文件路径。
- `model`(str): 可选。用于强制指定使用的模型。默认使用这个提供商默认配置的模型。
- `tool_calls_result`(dict): 可选。用于传入工具调用的结果。

::: details LLMResponse 类型定义

```py

@dataclass
class LLMResponse:
    role: str
    """角色, assistant, tool, err"""
    result_chain: MessageChain = None
    """返回的消息链"""
    tools_call_args: List[Dict[str, any]] = field(default_factory=list)
    """工具调用参数"""
    tools_call_name: List[str] = field(default_factory=list)
    """工具调用名称"""
    tools_call_ids: List[str] = field(default_factory=list)
    """工具调用 ID"""

    raw_completion: ChatCompletion = None
    _new_record: Dict[str, any] = None

    _completion_text: str = ""

    is_chunk: bool = False
    """是否是流式输出的单个 Chunk"""

    def __init__(
        self,
        role: str,
        completion_text: str = "",
        result_chain: MessageChain = None,
        tools_call_args: List[Dict[str, any]] = None,
        tools_call_name: List[str] = None,
        tools_call_ids: List[str] = None,
        raw_completion: ChatCompletion = None,
        _new_record: Dict[str, any] = None,
        is_chunk: bool = False,
    ):
        """初始化 LLMResponse

        Args:
            role (str): 角色, assistant, tool, err
            completion_text (str, optional): 返回的结果文本，已经过时，推荐使用 result_chain. Defaults to "".
            result_chain (MessageChain, optional): 返回的消息链. Defaults to None.
            tools_call_args (List[Dict[str, any]], optional): 工具调用参数. Defaults to None.
            tools_call_name (List[str], optional): 工具调用名称. Defaults to None.
            raw_completion (ChatCompletion, optional): 原始响应, OpenAI 格式. Defaults to None.
        """
        if tools_call_args is None:
            tools_call_args = []
        if tools_call_name is None:
            tools_call_name = []
        if tools_call_ids is None:
            tools_call_ids = []

        self.role = role
        self.completion_text = completion_text
        self.result_chain = result_chain
        self.tools_call_args = tools_call_args
        self.tools_call_name = tools_call_name
        self.tools_call_ids = tools_call_ids
        self.raw_completion = raw_completion
        self._new_record = _new_record
        self.is_chunk = is_chunk

    @property
    def completion_text(self):
        if self.result_chain:
            return self.result_chain.get_plain_text()
        return self._completion_text

    @completion_text.setter
    def completion_text(self, value):
        if self.result_chain:
            self.result_chain.chain = [
                comp
                for comp in self.result_chain.chain
                if not isinstance(comp, Comp.Plain)
            ]  # 清空 Plain 组件
            self.result_chain.chain.insert(0, Comp.Plain(value))
        else:
            self._completion_text = value

    def to_openai_tool_calls(self) -> List[Dict]:
        """将工具调用信息转换为 OpenAI 格式"""
        ret = []
        for idx, tool_call_arg in enumerate(self.tools_call_args):
            ret.append(
                {
                    "id": self.tools_call_ids[idx],
                    "function": {
                        "name": self.tools_call_name[idx],
                        "arguments": json.dumps(tool_call_arg),
                    },
                    "type": "function",
                }
            )
        return ret
```

:::

#### 获取其他类型的提供商

> 嵌入、重排序 没有 “当前使用”。这两个提供商主要用于知识库。

- 获取当前使用的语音识别提供商(STTProvider): `self.context.get_using_stt_provider(umo=event.unified_msg_origin)`。
- 获取当前使用的语音合成提供商(TTSProvider): `self.context.get_using_tts_provider(umo=event.unified_msg_origin)`。
- 获取所有语音识别提供商: `self.context.get_all_stt_providers()`。
- 获取所有语音合成提供商: `self.context.get_all_tts_providers()`。
- 获取所有嵌入提供商: `self.context.get_all_embedding_providers()`。

::: details STTProvider / TTSProvider / EmbeddingProvider 类型定义

```py
class TTSProvider(AbstractProvider):
    def __init__(self, provider_config: dict, provider_settings: dict) -> None:
        super().__init__(provider_config)
        self.provider_config = provider_config
        self.provider_settings = provider_settings

    @abc.abstractmethod
    async def get_audio(self, text: str) -> str:
        """获取文本的音频，返回音频文件路径"""
        raise NotImplementedError()


class EmbeddingProvider(AbstractProvider):
    def __init__(self, provider_config: dict, provider_settings: dict) -> None:
        super().__init__(provider_config)
        self.provider_config = provider_config
        self.provider_settings = provider_settings

    @abc.abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """获取文本的向量"""
        ...

    @abc.abstractmethod
    async def get_embeddings(self, text: list[str]) -> list[list[float]]:
        """批量获取文本的向量"""
        ...

    @abc.abstractmethod
    def get_dim(self) -> int:
        """获取向量的维度"""
        ...

class STTProvider(AbstractProvider):
    def __init__(self, provider_config: dict, provider_settings: dict) -> None:
        super().__init__(provider_config)
        self.provider_config = provider_config
        self.provider_settings = provider_settings

    @abc.abstractmethod
    async def get_text(self, audio_url: str) -> str:
        """获取音频的文本"""
        raise NotImplementedError()
```

:::

#### 函数工具

函数工具给了大语言模型调用外部工具的能力。在 AstrBot 中，函数工具有多种定义方式。

##### 以类的形式（推荐）

推荐在插件目录下新建 `tools` 文件夹，然后在其中编写工具类：

`tools/search.py`:

```py
from astrbot.api import FunctionTool
from astrbot.api.event import AstrMessageEvent
from dataclasses import dataclass, field

@dataclass
class HelloWorldTool(FunctionTool):
    name: str = "hello_world" # 工具名称
    description: str = "Say hello to the world." # 工具描述
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "greeting": {
                    "type": "string",
                    "description": "The greeting message.",
                },
            },
            "required": ["greeting"],
        }
    ) # 工具参数定义，见 OpenAI 官网或 https://json-schema.org/understanding-json-schema/

    async def run(
        self,
        event: AstrMessageEvent, # 必须包含此 event 参数在前面，用于获取上下文
        greeting: str, # 工具参数，必须与 parameters 中定义的参数名一致
    ):
        return f"{greeting}, World!" # 也支持 mcp.types.CallToolResult 类型
```

要将上述工具注册到 AstrBot，可以在插件主文件的 `__init__.py` 中添加以下代码：

```py
from .tools.search import SearchTool

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # >= v4.5.1 使用：
        self.context.add_llm_tools(HelloWorldTool(), SecondTool(), ...)

        # < v4.5.1 之前使用：
        tool_mgr = self.context.provider_manager.llm_tools
        tool_mgr.func_list.append(HelloWorldTool())
```

##### 以装饰器的形式

这个形式定义的工具函数会被自动加载到 AstrBot Core 中，在 Core 请求大模型时会被自动带上。

请务必按照以下格式编写一个工具（包括**函数注释**，AstrBot 会解析该函数注释，请务必将注释格式写对）

```py{3,4,5,6,7}
@filter.llm_tool(name="get_weather") # 如果 name 不填，将使用函数名
async def get_weather(self, event: AstrMessageEvent, location: str) -> MessageEventResult:
    '''获取天气信息。

    Args:
        location(string): 地点
    '''
    resp = self.get_weather_from_api(location)
    yield event.plain_result("天气信息: " + resp)
```

在 `location(string): 地点` 中，`location` 是参数名，`string` 是参数类型，`地点` 是参数描述。

支持的参数类型有 `string`, `number`, `object`, `boolean`。

> [!NOTE]
> 对于装饰器注册的 llm_tool，如果需要调用 Provider.text_chat()，func_tool（ToolSet 类型） 可以通过以下方式获取：
>
> ```py
> func_tool = self.context.get_llm_tool_manager() # 获取 AstrBot 的 LLM Tool Manager，包含了所有插件和 MCP 注册的 Tool
> tool = func_tool.get_func("xxx")
> if tool:
>     tool_set = ToolSet()
>     tool_set.add_tool(tool)
> ```

#### 对话管理器 ConversationManager

**获取会话当前的 LLM 对话历史**

```py
from astrbot.core.conversation_mgr import Conversation

uid = event.unified_msg_origin
conv_mgr = self.context.conversation_manager
curr_cid = await conv_mgr.get_curr_conversation_id(uid)
conversation = await conv_mgr.get_conversation(uid, curr_cid)  # Conversation
```

::: details Conversation 类型定义

```py
@dataclass
class Conversation:
    """LLM 对话类

    对于 WebChat，history 存储了包括指令、回复、图片等在内的所有消息。
    对于其他平台的聊天，不存储非 LLM 的回复（因为考虑到已经存储在各自的平台上）。

    在 v4.0.0 版本及之后，WebChat 的历史记录被迁移至 `PlatformMessageHistory` 表中，
    """

    platform_id: str
    user_id: str
    cid: str
    """对话 ID, 是 uuid 格式的字符串"""
    history: str = ""
    """字符串格式的对话列表。"""
    title: str | None = ""
    persona_id: str | None = ""
    """对话当前使用的人格 ID"""
    created_at: int = 0
    updated_at: int = 0
```

:::

**所有方法**

##### `new_conversation`

- **Usage**  
  在当前会话中新建一条对话，并自动切换为该对话。
- **Arguments**  
  - `unified_msg_origin: str` – 形如 `platform_name:message_type:session_id`  
  - `platform_id: str | None` – 平台标识，默认从 `unified_msg_origin` 解析  
  - `content: list[dict] | None` – 初始历史消息  
  - `title: str | None` – 对话标题  
  - `persona_id: str | None` – 绑定的 persona ID
- **Returns**  
  `str` – 新生成的 UUID 对话 ID

##### `switch_conversation`

- **Usage**  
  将会话切换到指定的对话。
- **Arguments**  
  - `unified_msg_origin: str`  
  - `conversation_id: str`
- **Returns**  
  `None`

##### `delete_conversation`

- **Usage**  
  删除会话中的某条对话；若 `conversation_id` 为 `None`，则删除当前对话。
- **Arguments**  
  - `unified_msg_origin: str`  
  - `conversation_id: str | None`
- **Returns**  
  `None`

##### `get_curr_conversation_id`

- **Usage**  
  获取当前会话正在使用的对话 ID。
- **Arguments**  
  - `unified_msg_origin: str`
- **Returns**  
  `str | None` – 当前对话 ID，不存在时返回 `None`

##### `get_conversation`

- **Usage**  
  获取指定对话的完整对象；若不存在且 `create_if_not_exists=True` 则自动创建。
- **Arguments**  
  - `unified_msg_origin: str`  
  - `conversation_id: str`  
  - `create_if_not_exists: bool = False`
- **Returns**  
  `Conversation | None`

##### `get_conversations`

- **Usage**  
  拉取用户或平台下的全部对话列表。
- **Arguments**  
  - `unified_msg_origin: str | None` – 为 `None` 时不过滤用户  
  - `platform_id: str | None`
- **Returns**  
  `List[Conversation]`

##### `get_filtered_conversations`

- **Usage**  
  分页 + 关键词搜索对话。
- **Arguments**  
  - `page: int = 1`  
  - `page_size: int = 20`  
  - `platform_ids: list[str] | None`  
  - `search_query: str = ""`  
  - `**kwargs` – 透传其他过滤条件
- **Returns**  
  `tuple[list[Conversation], int]` – 对话列表与总数

##### `update_conversation`

- **Usage**  
  更新对话的标题、历史记录或 persona_id。
- **Arguments**  
  - `unified_msg_origin: str`  
  - `conversation_id: str | None` – 为 `None` 时使用当前对话  
  - `history: list[dict] | None`  
  - `title: str | None`  
  - `persona_id: str | None`
- **Returns**  
  `None`

##### `get_human_readable_context`

- **Usage**  
  生成分页后的人类可读对话上下文，方便展示或调试。
- **Arguments**  
  - `unified_msg_origin: str`  
  - `conversation_id: str`  
  - `page: int = 1`  
  - `page_size: int = 10`
- **Returns**  
  `tuple[list[str], int]` – 当前页文本列表与总页数

```py
import json

context = json.loads(conversation.history)
```

#### 人格设定管理器 PersonaManager

`PersonaManager` 负责统一加载、缓存并提供所有人格（Persona）的增删改查接口，同时兼容 AstrBot 4.x 之前的旧版人格格式（v3）。  
初始化时会自动从数据库读取全部人格，并生成一份 v3 兼容数据，供旧代码无缝使用。

```py
persona_mgr = self.context.persona_manager
```

##### `get_persona`

- **Usage**
  获取根据人格 ID 获取人格数据。
- **Arguments**
  - `persona_id: str` – 人格 ID
- **Returns**
  `Persona` – 人格数据，若不存在则返回 None
- **Raises**
  `ValueError` – 当不存在时抛出

##### `get_all_personas`

- **Usage**  
  一次性获取数据库中所有人格。
- **Returns**  
  `list[Persona]` – 人格列表，可能为空

##### `create_persona`

- **Usage**  
  新建人格并立即写入数据库，成功后自动刷新本地缓存。
- **Arguments**  
  - `persona_id: str` – 新人格 ID（唯一）  
  - `system_prompt: str` – 系统提示词  
  - `begin_dialogs: list[str]` – 可选，开场对话（偶数条，user/assistant 交替）  
  - `tools: list[str]` – 可选，允许使用的工具列表；`None`=全部工具，`[]`=禁用全部
- **Returns**  
  `Persona` – 新建后的人格对象
- **Raises**  
  `ValueError` – 若 `persona_id` 已存在

##### `update_persona`

- **Usage**  
  更新现有人格的任意字段，并同步到数据库与缓存。
- **Arguments**  
  - `persona_id: str` – 待更新的人格 ID  
  - `system_prompt: str` – 可选，新的系统提示词  
  - `begin_dialogs: list[str]` – 可选，新的开场对话  
  - `tools: list[str]` – 可选，新的工具列表；语义同 `create_persona`
- **Returns**  
  `Persona` – 更新后的人格对象
- **Raises**  
  `ValueError` – 若 `persona_id` 不存在

##### `delete_persona`

- **Usage**  
  删除指定人格，同时清理数据库与缓存。
- **Arguments**  
  - `persona_id: str` – 待删除的人格 ID
- **Raises**  
  `Valueable` – 若 `persona_id` 不存在

##### `get_default_persona_v3`

- **Usage**  
  根据当前会话配置，获取应使用的默认人格（v3 格式）。  
  若配置未指定或指定的人格不存在，则回退到 `DEFAULT_PERSONALITY`。
- **Arguments**  
  - `umo: str | MessageSession | None` – 会话标识，用于读取用户级配置
- **Returns**  
  `Personality` – v3 格式的默认人格对象

::: details Persona / Personality 类型定义

```py

class Persona(SQLModel, table=True):
    """Persona is a set of instructions for LLMs to follow.

    It can be used to customize the behavior of LLMs.
    """

    __tablename__ = "personas"

    id: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": True})
    persona_id: str = Field(max_length=255, nullable=False)
    system_prompt: str = Field(sa_type=Text, nullable=False)
    begin_dialogs: Optional[list] = Field(default=None, sa_type=JSON)
    """a list of strings, each representing a dialog to start with"""
    tools: Optional[list] = Field(default=None, sa_type=JSON)
    """None means use ALL tools for default, empty list means no tools, otherwise a list of tool names."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": datetime.now(timezone.utc)},
    )

    __table_args__ = (
        UniqueConstraint(
            "persona_id",
            name="uix_persona_id",
        ),
    )


class Personality(TypedDict):
    """LLM 人格类。

    在 v4.0.0 版本及之后，推荐使用上面的 Persona 类。并且， mood_imitation_dialogs 字段已被废弃。
    """

    prompt: str
    name: str
    begin_dialogs: list[str]
    mood_imitation_dialogs: list[str]
    """情感模拟对话预设。在 v4.0.0 版本及之后，已被废弃。"""
    tools: list[str] | None
    """工具列表。None 表示使用所有工具，空列表表示不使用任何工具"""
```

:::

### 其他

#### 配置文件

##### 默认配置文件

```py
config = self.context.get_config()
```

不建议修改默认配置文件，建议只读取。

##### 会话配置文件

v4.0.0 后，AstrBot 支持会话粒度的多配置文件。

```py
umo = event.unified_msg_origin
config = self.context.get_config(umo=umo)
```

#### 获取消息平台实例

> v3.4.34 后

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test_(self, event: AstrMessageEvent):
    from astrbot.api.platform import AiocqhttpAdapter # 其他平台同理
    platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
    assert isinstance(platform, AiocqhttpAdapter)
    # platform.get_client().api.call_action()
```

#### 调用 QQ 协议端 API

```py
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    if event.get_platform_name() == "aiocqhttp":
        # qq
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        assert isinstance(event, AiocqhttpMessageEvent)
        client = event.bot # 得到 client
        payloads = {
            "message_id": event.message_obj.message_id,
        }
        ret = await client.api.call_action('delete_msg', **payloads) # 调用 协议端  API
        logger.info(f"delete_msg: {ret}")
```

关于 CQHTTP API，请参考如下文档：

Napcat API 文档：<https://napcat.apifox.cn/>

Lagrange API 文档：<https://lagrange-onebot.apifox.cn/>

#### 载入的所有插件

```py
plugins = self.context.get_all_stars() # 返回 StarMetadata 包含了插件类实例、配置等等
```

#### 注册一个异步任务

直接在 **init**() 中使用 `asyncio.create_task()` 即可。

```py
import asyncio

class TaskPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        asyncio.create_task(self.my_task())

    async def my_task(self):
        await asyncio.sleep(1)
        print("Hello")
```

#### 获取加载的所有平台

```py
from astrbot.api.platform import Platform
platforms = self.context.platform_manager.get_insts() # List[Platform]
```


---

<a id="simple"></a>

# 最小实例

插件模版中的 `main.py` 是一个最小的插件实例。

```python
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger # 使用 astrbot 提供的 logger 接口

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        '''这是一个 hello world 指令''' # 这是 handler 的描述，将会被解析方便用户了解插件内容。非常建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 获取消息的纯文本内容
        logger.info("触发hello world指令!")
        yield event.plain_result(f"Hello, {user_name}!") # 发送一条纯文本消息

    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''
```

解释如下：

- 插件需要继承 `Star` 类。
- `Context` 类用于插件与 AstrBot Core 交互，可以由此调用 AstrBot Core 提供的各种 API。
- 具体的处理函数 `Handler` 在插件类中定义，如这里的 `helloworld` 函数。
- `AstrMessageEvent` 是 AstrBot 的消息事件对象，存储了消息发送者、消息内容等信息。
- `AstrBotMessage` 是 AstrBot 的消息对象，存储了消息平台下发的消息的具体内容。可以通过 `event.message_obj` 获取。

> [!TIP]
>
> `Handler` 一定需要在插件类中注册，前两个参数必须为 `self` 和 `event`。如果文件行数过长，可以将服务写在外部，然后在 `Handler` 中调用。
>
> 插件类所在的文件名需要命名为 `main.py`。

所有的处理函数都需写在插件类中。为了精简内容，在之后的章节中，我们可能会忽略插件类的定义。


---

<a id="env"></a>


# 开发环境准备

## 获取插件模板

1. 打开 AstrBot 插件模板: [helloworld](https://github.com/Soulter/helloworld)
2. 点击右上角的 `Use this template`
3. 然后点击 `Create new repository`。
4. 在 `Repository name` 处填写您的插件名。插件名格式:
   - 推荐以 `astrbot_plugin_` 开头；
   - 不能包含空格；
   - 保持全部字母小写；
   - 尽量简短。
5. 点击右下角的 `Create repository`。

![New repo](https://files.astrbot.app/docs/source/images/plugin/image.png)

## Clone 插件和 AstrBot 项目

Clone AstrBot 项目本体和刚刚创建的插件仓库到本地。

```bash
git clone https://github.com/AstrBotDevs/AstrBot
mkdir -p AstrBot/data/plugins
cd AstrBot/data/plugins
git clone 插件仓库地址
```

然后，使用 `VSCode` 打开 `AstrBot` 项目。找到 `data/plugins/<你的插件名字>` 目录。

更新 `metadata.yaml` 文件，填写插件的元数据信息。

> [!NOTE]
> AstrBot 插件市场的信息展示依赖于 `metadata.yaml` 文件。

## 调试插件

AstrBot 采用在运行时注入插件的机制。因此，在调试插件时，需要启动 AstrBot 本体。

您可以使用 AstrBot 的热重载功能简化开发流程。

插件的代码修改后，可以在 AstrBot WebUI 的插件管理处找到自己的插件，点击右上角 `...` 按钮，选择 `重载插件`。

## 插件依赖管理

目前 AstrBot 对插件的依赖管理使用 `pip` 自带的 `requirements.txt` 文件。如果你的插件需要依赖第三方库，请务必在插件目录下创建 `requirements.txt` 文件并写入所使用的依赖库，以防止用户在安装你的插件时出现依赖未找到(Module Not Found)的问题。

> `requirements.txt` 的完整格式可以参考 [pip 官方文档](https://pip.pypa.io/en/stable/reference/requirements-file-format/)。


---

<a id="listen-message-event"></a>


# 处理消息事件

事件监听器可以收到平台下发的消息内容，可以实现指令、指令组、事件监听等功能。

事件监听器的注册器在 `astrbot.api.event.filter` 下，需要先导入。请务必导入，否则会和 python 的高阶函数 filter 冲突。

```py
from astrbot.api.event import filter, AstrMessageEvent
```

## 消息与事件

AstrBot 接收消息平台下发的消息，并将其封装为 `AstrMessageEvent` 对象，传递给插件进行处理。

![message-event](https://files.astrbot.app/docs/zh/dev/star/guides/message-event.svg)

### 消息事件

`AstrMessageEvent` 是 AstrBot 的消息事件对象，其中存储了消息发送者、消息内容等信息。

### 消息对象

`AstrBotMessage` 是 AstrBot 的消息对象，其中存储了消息平台下发的消息具体内容，`AstrMessageEvent` 对象中包含一个 `message_obj` 属性用于获取该消息对象。

```py{11}
class AstrBotMessage:
    '''AstrBot 的消息对象'''
    type: MessageType  # 消息类型
    self_id: str  # 机器人的识别id
    session_id: str  # 会话id。取决于 unique_session 的设置。
    message_id: str  # 消息id
    group_id: str = "" # 群组id，如果为私聊，则为空
    sender: MessageMember  # 发送者
    message: List[BaseMessageComponent]  # 消息链。比如 [Plain("Hello"), At(qq=123456)]
    message_str: str  # 最直观的纯文本消息字符串，将消息链中的 Plain 消息（文本消息）连接起来
    raw_message: object
    timestamp: int  # 消息时间戳
```

其中，`raw_message` 是消息平台适配器的**原始消息对象**。

### 消息链

![message-chain](https://files.astrbot.app/docs/zh/dev/star/guides/message-chain.svg)

`消息链`描述一个消息的结构，是一个有序列表，列表中每一个元素称为`消息段`。

常见的消息段类型有：

- `Plain`：文本消息段
- `At`：提及消息段
- `Image`：图片消息段
- `Record`：语音消息段
- `Video`：视频消息段
- `File`：文件消息段

大多数消息平台都支持上面的消息段类型。

此外，OneBot v11 平台（QQ 个人号等）还支持以下较为常见的消息段类型：

- `Face`：表情消息段
- `Node`：合并转发消息中的一个节点
- `Nodes`：合并转发消息中的多个节点
- `Poke`：戳一戳消息段

在 AstrBot 中，消息链表示为 `List[BaseMessageComponent]` 类型的列表。

## 指令

![message-event-simple-command](https://files.astrbot.app/docs/zh/dev/star/guides/message-event-simple-command.svg)

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("helloworld") # from astrbot.api.event.filter import command
    async def helloworld(self, event: AstrMessageEvent):
        '''这是 hello world 指令'''
        user_name = event.get_sender_name()
        message_str = event.message_str # 获取消息的纯文本内容
        yield event.plain_result(f"Hello, {user_name}!")
```

> [!TIP]
> 指令不能带空格，否则 AstrBot 会将其解析到第二个参数。可以使用下面的指令组功能，或者也使用监听器自己解析消息内容。

## 带参指令

![command-with-param](https://files.astrbot.app/docs/zh/dev/star/guides/command-with-param.svg)

AstrBot 会自动帮你解析指令的参数。

```python
@filter.command("add")
def add(self, event: AstrMessageEvent, a: int, b: int):
    # /add 1 2 -> 结果是: 3
    yield event.plain_result(f"Wow! The anwser is {a + b}!")
```

## 指令组

指令组可以帮助你组织指令。

```python
@filter.command_group("math")
def math(self):
    pass

@math.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    # /math add 1 2 -> 结果是: 3
    yield event.plain_result(f"结果是: {a + b}")

@math.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    # /math sub 1 2 -> 结果是: -1
    yield event.plain_result(f"结果是: {a - b}")
```

指令组函数内不需要实现任何函数，请直接 `pass` 或者添加函数内注释。指令组的子指令使用 `指令组名.command` 来注册。

当用户没有输入子指令时，会报错并，并渲染出该指令组的树形结构。

![image](https://files.astrbot.app/docs/source/images/plugin/image-1.png)

![image](https://files.astrbot.app/docs/source/images/plugin/898a169ae7ed0478f41c0a7d14cb4d64.png)

![image](https://files.astrbot.app/docs/source/images/plugin/image-2.png)

理论上，指令组可以无限嵌套！

```py
'''
math
├── calc
│   ├── add (a(int),b(int),)
│   ├── sub (a(int),b(int),)
│   ├── help (无参数指令)
'''

@filter.command_group("math")
def math():
    pass

@math.group("calc") # 请注意，这里是 group，而不是 command_group
def calc():
    pass

@calc.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")

@calc.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a - b}")

@calc.command("help")
def calc_help(self, event: AstrMessageEvent):
    # /math calc help
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

## 指令别名

> v3.4.28 后

可以为指令或指令组添加不同的别名：

```python
@filter.command("help", alias={'帮助', 'helpme'})
def help(self, event: AstrMessageEvent):
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

### 事件类型过滤

#### 接收所有

这将接收所有的事件。

```python
@filter.event_message_type(filter.EventMessageType.ALL)
async def on_all_message(self, event: AstrMessageEvent):
    yield event.plain_result("收到了一条消息。")
```

#### 群聊和私聊

```python
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def on_private_message(self, event: AstrMessageEvent):
    message_str = event.message_str # 获取消息的纯文本内容
    yield event.plain_result("收到了一条私聊消息。")
```

`EventMessageType` 是一个 `Enum` 类型，包含了所有的事件类型。当前的事件类型有 `PRIVATE_MESSAGE` 和 `GROUP_MESSAGE`。

#### 消息平台

```python
@filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP | filter.PlatformAdapterType.QQOFFICIAL)
async def on_aiocqhttp(self, event: AstrMessageEvent):
    '''只接收 AIOCQHTTP 和 QQOFFICIAL 的消息'''
    yield event.plain_result("收到了一条信息")
```

当前版本下，`PlatformAdapterType` 有 `AIOCQHTTP`, `QQOFFICIAL`, `GEWECHAT`, `ALL`。

#### 管理员指令

```python
@filter.permission_type(filter.PermissionType.ADMIN)
@filter.command("test")
async def test(self, event: AstrMessageEvent):
    pass
```

仅管理员才能使用 `test` 指令。

### 多个过滤器

支持同时使用多个过滤器，只需要在函数上添加多个装饰器即可。过滤器使用 `AND` 逻辑。也就是说，只有所有的过滤器都通过了，才会执行函数。

```python
@filter.command("helloworld")
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("你好！")
```

### 事件钩子

> [!TIP]
> 事件钩子不支持与上面的 @filter.command, @filter.command_group, @filter.event_message_type, @filter.platform_adapter_type, @filter.permission_type 一起使用。

#### Bot 初始化完成时

> v3.4.34 后

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.on_astrbot_loaded()
async def on_astrbot_loaded(self):
    print("AstrBot 初始化完成")

```

#### 等待 LLM 请求时

在 AstrBot 准备调用 LLM 但还未获取会话锁时，会触发 `on_waiting_llm_request` 钩子。

这个钩子适合用于发送"正在等待请求..."等用户反馈提示，亦或是在锁外及时获取LLM请求而不用等到锁被释放。

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.on_waiting_llm_request()
async def on_waiting_llm(self, event: AstrMessageEvent):
    await event.send("🤔 正在等待请求...")
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

#### LLM 请求时

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

在 AstrBot 默认的执行流程中，在调用 LLM 前，会触发 `on_llm_request` 钩子。

可以获取到 `ProviderRequest` 对象，可以对其进行修改。

ProviderRequest 对象包含了 LLM 请求的所有信息，包括请求的文本、系统提示等。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import ProviderRequest

@filter.on_llm_request()
async def my_custom_hook_1(self, event: AstrMessageEvent, req: ProviderRequest): # 请注意有三个参数
    print(req) # 打印请求的文本
    req.system_prompt += "自定义 system_prompt" # 如果有其他替代方法，不建议使用此种方式来追加每轮对话都会改变的提示词，否则会破坏缓存，大大增加价格（约增加 7-20 倍的价格）。
    req.extra_user_content_parts.append(...)

```

> [!WARNING]
> **关于提示词的追加**
>
> `req.system_prompt += ...` 适合追加稳定、长期有效的角色设定或全局规则。不建议把每轮都会变化的内容追加到 `system_prompt`，例如当前时间、好感度、状态栏、短期记忆片段、检索摘要等。这类写法会让系统提示词在每轮请求中变化，容易破坏模型服务端的提示词缓存，显著增加请求成本和首 token 延迟。
>
> 对于每轮都会变化、内容量中小的提示词，优先通过 `req.extra_user_content_parts` 追加。它会作为额外的用户消息内容块放在本轮用户输入之后，更适合承载"当前时间""角色好感度""本轮相关记忆片段"等动态上下文：
>
> ```python
> from astrbot.core.agent.message import TextPart
>
> @filter.on_llm_request()
> async def add_dynamic_prompt(self, event: AstrMessageEvent, req: ProviderRequest):
>     req.extra_user_content_parts.append(
>         TextPart(
>             text=(
>                 "<dynamic_context>\n"
>                 "当前时间：2026-05-03 20:00\n"
>                 "好感度：72\n"
>                 "相关记忆：用户喜欢简洁直接的回答。\n"
>                 "</dynamic_context>"
>             )
>         )
>     )
> ```
>
> 如果追加的内容只希望参与本轮 LLM 请求，不希望被持久化到会话历史中，可以调用 `.mark_as_temp()` 标记为临时内容（`>= v4.24.0`）：
>
> ```python
> req.extra_user_content_parts.append(
>     TextPart(text="<runtime_hint>这段提示只在本轮请求中生效。</runtime_hint>").mark_as_temp()
> )
> ```
>
> 对于长期记忆、知识库、外部系统查询等内容量较大或不一定每轮都需要的信息，不建议全部塞进提示词。可以优先注册为 `llm_tool`，让模型在需要时调用；也可以先在插件中检索出本轮真正相关的少量摘要，再放入 `extra_user_content_parts`。

#### LLM 请求完成时

在 LLM 请求完成后，会触发 `on_llm_response` 钩子。

可以获取到 `ProviderResponse` 对象，可以对其进行修改。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import LLMResponse

@filter.on_llm_response()
async def on_llm_resp(self, event: AstrMessageEvent, resp: LLMResponse): # 请注意有三个参数
    print(resp)
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

#### Agent 开始运行时

> 适用于 AstrBot 版本 > v4.23.1

在 Agent 开始运行时，会触发 `on_agent_begin` 钩子。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.astr_agent_context import AstrAgentContext

@filter.on_agent_begin()
async def on_agent_begin(self, event: AstrMessageEvent, run_context: ContextWrapper[AstrAgentContext]):
    print("Agent 开始运行")
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

#### LLM 工具调用前

> 适用于 AstrBot 版本 > v4.23.1

在 Agent 准备调用 LLM 工具时，会触发 `on_using_llm_tool` 钩子。

可以获取到 `FunctionTool` 对象和工具调用参数。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.agent.tool import FunctionTool

@filter.on_using_llm_tool()
async def on_using_llm_tool(
    self,
    event: AstrMessageEvent,
    tool: FunctionTool,
    tool_args: dict | None,
):
    print(tool.name, tool_args)
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

#### LLM 工具调用后

> 适用于 AstrBot 版本 > v4.23.1

在 LLM 工具调用完成后，会触发 `on_llm_tool_respond` 钩子。

可以获取到 `FunctionTool` 对象、工具调用参数和工具调用结果。

```python
from mcp.types import CallToolResult

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.agent.tool import FunctionTool

@filter.on_llm_tool_respond()
async def on_llm_tool_respond(
    self,
    event: AstrMessageEvent,
    tool: FunctionTool,
    tool_args: dict | None,
    tool_result: CallToolResult | None,
):
    print(tool.name, tool_args, tool_result)
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

#### Agent 运行完成时

> 适用于 AstrBot 版本 > v4.23.1

在 Agent 运行完成后，会触发 `on_agent_done` 钩子。这个钩子会在 `on_llm_response` 之后触发。本质上和 `on_llm_response` 一样。

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import LLMResponse
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.astr_agent_context import AstrAgentContext

@filter.on_agent_done()
async def on_agent_done(self, event: AstrMessageEvent, run_context: ContextWrapper[AstrAgentContext], resp: LLMResponse):
    print(resp)
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

#### 发送消息前

在发送消息前，会触发 `on_decorating_result` 钩子。

可以在这里实现一些消息的装饰，比如转语音、转图片、加前缀等等

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.on_decorating_result()
async def on_decorating_result(self, event: AstrMessageEvent):
    result = event.get_result()
    chain = result.chain
    print(chain) # 打印消息链
    chain.append(Plain("!")) # 在消息链的最后添加一个感叹号
```

> 这里不能使用 yield 来发送消息。这个钩子只是用来装饰 event.get_result().chain 的。如需发送，请直接使用 `event.send()` 方法。

#### 发送消息后

在发送消息给消息平台后，会触发 `after_message_sent` 钩子。

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.after_message_sent()
async def after_message_sent(self, event: AstrMessageEvent):
    pass
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

### 优先级

指令、事件监听器、事件钩子可以设置优先级，先于其他指令、监听器、钩子执行。默认优先级是 `0`。

```python
@filter.command("helloworld", priority=1)
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("Hello!")
```

## 控制事件传播

```python{6}
@filter.command("check_ok")
async def check_ok(self, event: AstrMessageEvent):
    ok = self.check() # 自己的逻辑
    if not ok:
        yield event.plain_result("检查失败")
        event.stop_event() # 停止事件传播
```

当事件停止传播，后续所有步骤将不会被执行。

假设有一个插件 A，A 终止事件传播之后所有后续操作都不会执行，比如执行其它插件的 handler、请求 LLM。


---

<a id="send-message"></a>


# 消息的发送

## 被动消息

被动消息指的是机器人被动回复消息。

```python
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("Hello!")
    yield event.plain_result("你好！")

    yield event.image_result("path/to/image.jpg") # 发送图片
    yield event.image_result("https://example.com/image.jpg") # 发送 URL 图片，务必以 http 或 https 开头
```

## 主动消息

主动消息指的是机器人主动推送消息。某些平台可能不支持主动消息发送。

如果是一些定时任务或者不想立即发送消息，可以使用 `event.unified_msg_origin` 得到一个字符串并将其存储，然后在想发送消息的时候使用 `self.context.send_message(unified_msg_origin, chains)` 来发送消息。

```python
from astrbot.api.event import MessageChain

@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    umo = event.unified_msg_origin
    message_chain = MessageChain().message("Hello!").file_image("path/to/image.jpg")
    await self.context.send_message(event.unified_msg_origin, message_chain)
```

通过这个特性，你可以将 unified_msg_origin 存储起来，然后在需要的时候发送消息。

> [!TIP]
> 关于 unified_msg_origin。
> unified_msg_origin 是一个字符串，记录了一个会话的唯一 ID，AstrBot 能够据此找到属于哪个消息平台的哪个会话。这样就能够实现在 `send_message` 的时候，发送消息到正确的会话。有关 MessageChain，请参见接下来的一节。

## 富媒体消息

AstrBot 支持发送富媒体消息，比如图片、语音、视频等。使用 `MessageChain` 来构建消息。

```python
import astrbot.api.message_components as Comp

@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    chain = [
        Comp.At(qq=event.get_sender_id()), # At 消息发送者
        Comp.Plain("来看这个图："),
        Comp.Image.fromURL("https://example.com/image.jpg"), # 从 URL 发送图片
        Comp.Image.fromFileSystem("path/to/image.jpg"), # 从本地文件目录发送图片
        Comp.Plain("这是一个图片。")
    ]
    yield event.chain_result(chain)
```

上面构建了一个 `message chain`，也就是消息链，最终会发送一条包含了图片和文字的消息，并且保留顺序。

> [!TIP]
> 在 aiocqhttp 消息适配器中，对于 `plain` 类型的消息，在发送中会使用 `strip()` 方法去除空格及换行符，可以在消息前后添加零宽空格 `\u200b` 以解决这个问题。

类似地，

**文件 File**

```py
Comp.File(file="path/to/file.txt", name="file.txt") # 部分平台不支持
```

**语音 Record**

```py
path = "path/to/record.wav" # 暂时只接受 wav 格式，其他格式请自行转换
Comp.Record(file=path, url=path)
```

**视频 Video**

```py
path = "path/to/video.mp4"
Comp.Video.fromFileSystem(path=path)
Comp.Video.fromURL(url="https://example.com/video.mp4")
```

## 发送视频消息

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    from astrbot.api.message_components import Video
    # fromFileSystem 需要用户的协议端和机器人端处于一个系统中。
    music = Video.fromFileSystem(
        path="test.mp4"
    )
    # 更通用
    music = Video.fromURL(
        url="https://example.com/video.mp4"
    )
    yield event.chain_result([music])
```

![发送视频消息](https://files.astrbot.app/docs/source/images/plugin/db93a2bb-671c-4332-b8ba-9a91c35623c2.png)

## 发送群合并转发消息

> 大多数平台都不支持此种消息类型，当前适配情况：OneBot v11

可以按照如下方式发送群合并转发消息。

```py
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    from astrbot.api.message_components import Node, Plain, Image
    node = Node(
        uin=905617992,
        name="Soulter",
        content=[
            Plain("hi"),
            Image.fromFileSystem("test.jpg")
        ]
    )
    yield event.chain_result([node])
```

![发送群合并转发消息](https://files.astrbot.app/docs/source/images/plugin/image-4.png)


---

<a id="session-control"></a>


# 会话控制

> 大于等于 v3.4.36

为什么需要会话控制？考虑一个 成语接龙 插件，某个/群用户需要和机器人进行多次对话，而不是一次性的指令。这时候就需要会话控制。

```txt
用户: /成语接龙
机器人: 请发送一个成语
用户: 一马当先
机器人: 先见之明
用户: 明察秋毫
...
```

AstrBot 提供了开箱即用的会话控制功能：

导入：

```py
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionController,
)
```

handler 内的代码可以如下：

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("成语接龙")
async def handle_empty_mention(self, event: AstrMessageEvent):
    """成语接龙具体实现"""
    try:
        yield event.plain_result("请发送一个成语~")

        # 具体的会话控制器使用方法
        @session_waiter(timeout=60, record_history_chains=False) # 注册一个会话控制器，设置超时时间为 60 秒，不记录历史消息链
        async def empty_mention_waiter(controller: SessionController, event: AstrMessageEvent):
            idiom = event.message_str # 用户发来的成语，假设是 "一马当先"

            if idiom == "退出":   # 假设用户想主动退出成语接龙，输入了 "退出"
                await event.send(event.plain_result("已退出成语接龙~"))
                controller.stop()    # 停止会话控制器，会立即结束。
                return

            if len(idiom) != 4:   # 假设用户输入的不是4字成语
                await event.send(event.plain_result("成语必须是四个字的呢~"))  # 发送回复，不能使用 yield
                return
                # 退出当前方法，不执行后续逻辑，但此会话并未中断，后续的用户输入仍然会进入当前会话

            # ...
            message_result = event.make_result()
            message_result.chain = [Comp.Plain("先见之明")] # import astrbot.api.message_components as Comp
            await event.send(message_result) # 发送回复，不能使用 yield

            controller.keep(timeout=60, reset_timeout=True) # 重置超时时间为 60s，如果不重置，则会继续之前的超时时间计时。

            # controller.stop() # 停止会话控制器，会立即结束。
            # 如果记录了历史消息链，可以通过 controller.get_history_chains() 获取历史消息链

        try:
            await empty_mention_waiter(event)
        except TimeoutError as _: # 当超时后，会话控制器会抛出 TimeoutError
            yield event.plain_result("你超时了！")
        except Exception as e:
            yield event.plain_result("发生错误，请联系管理员: " + str(e))
        finally:
            event.stop_event()
    except Exception as e:
        logger.error("handle_empty_mention error: " + str(e))
```

当激活会话控制器后，该发送人之后发送的消息会首先经过上面你定义的 `empty_mention_waiter` 函数处理，直到会话控制器被停止或者超时。

## SessionController

用于开发者控制这个会话是否应该结束，并且可以拿到历史消息链。

- keep(): 保持这个会话
  - timeout (float): 必填。会话超时时间。
  - reset_timeout (bool): 设置为 True 时, 代表重置超时时间, timeout 必须 > 0, 如果 <= 0 则立即结束会话。设置为 False 时, 代表继续维持原来的超时时间, 新 timeout = 原来剩余的 timeout + timeout (可以 < 0)
- stop(): 结束这个会话
- get_history_chains() -> List[List[Comp.BaseMessageComponent]]: 获取历史消息链

## 自定义会话 ID 算子

默认情况下，AstrBot 会话控制器会将基于 `sender_id` （发送人的 ID）作为识别不同会话的标识，如果想将一整个群作为一个会话，则需要自定义会话 ID 算子。

```py
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionFilter,
    SessionController,
)

# 沿用上面的 handler
# ...
class CustomFilter(SessionFilter):
    def filter(self, event: AstrMessageEvent) -> str:
        return event.get_group_id() if event.get_group_id() else event.unified_msg_origin

await empty_mention_waiter(event, session_filter=CustomFilter()) # 这里传入 session_filter
# ...
```

这样之后，当群内一个用户发送消息后，会话控制器会将这个群作为一个会话，群内其他用户发送的消息也会被认为是同一个会话。

甚至，可以使用这个特性来让群内组队！


---

<a id="ai"></a>


# AI

AstrBot 内置了对多种大语言模型（LLM）提供商的支持，并且提供了统一的接口，方便插件开发者调用各种 LLM 服务。

您可以使用 AstrBot 提供的 LLM / Agent 接口来实现自己的智能体。

我们在 `v4.5.7` 版本之后对 LLM 提供商的调用方式进行了较大调整，推荐使用新的调用方式。新的调用方式更加简洁，并且支持更多的功能。当然，您仍然可以使用[旧的调用方式](/dev/star/plugin#ai)。

## 获取当前会话使用的聊天模型 ID

> [!TIP]
> 在 v4.5.7 时加入

```py
umo = event.unified_msg_origin
provider_id = await self.context.get_current_chat_provider_id(umo=umo)
```

## 调用大模型

> [!TIP]
> 在 v4.5.7 时加入

```py
llm_resp = await self.context.llm_generate(
    chat_provider_id=provider_id, # 聊天模型 ID
    prompt="Hello, world!",
)
# print(llm_resp.completion_text) # 获取返回的文本
```

## 定义 Tool

Tool 是大语言模型调用外部工具的能力。

```py
from pydantic import Field
from pydantic.dataclasses import dataclass

from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext


@dataclass
class BilibiliTool(FunctionTool[AstrAgentContext]):
    name: str = "bilibili_videos"  # 工具名称
    description: str = "A tool to fetch Bilibili videos."  # 工具描述
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "Keywords to search for Bilibili videos.",
                },
            },
            "required": ["keywords"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        return "1. 视频标题：如何使用AstrBot\n视频链接：xxxxxx"
```

## 注册 Tool 到 AstrBot

在上面定义好 Tool 之后，如果你需要实现的功能是让用户在使用 AstrBot 进行对话时自动调用该 Tool，那么你需要在插件的 __init__ 方法中将 Tool 注册到 AstrBot 中：

```py
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # >= v4.5.1 使用：
        self.context.add_llm_tools(BilibiliTool(), SecondTool(), ...)

        # < v4.5.1 之前使用：
        tool_mgr = self.context.provider_manager.llm_tools
        tool_mgr.func_list.append(BilibiliTool())
```

### 通过装饰器定义 Tool 和注册 Tool

除了上述的通过 `@dataclass` 定义 Tool 的方式之外，你也可以使用装饰器的方式注册 tool 到 AstrBot。如果请务必按照以下格式编写一个工具（包括函数注释，AstrBot 会解析该函数注释，请务必将注释格式写对）

```py{3,4,5,6,7}
@filter.llm_tool(name="get_weather") # 如果 name 不填，将使用函数名
async def get_weather(self, event: AstrMessageEvent, location: str) -> MessageEventResult:
    '''获取天气信息。

    Args:
        location(string): 地点
    '''
    resp = self.get_weather_from_api(location)
    yield event.plain_result("天气信息: " + resp)
```

在 `location(string): 地点` 中，`location` 是参数名，`string` 是参数类型，`地点` 是参数描述。

支持的参数类型有 `string`, `number`, `object`, `boolean`, `array`。在 v4.5.7 之后，支持对 `array` 类型参数指定子类型，例如 `array[string]`。

## 调用 Agent

> [!TIP]
> 在 v4.5.7 时加入

Agent 可以被定义为 system_prompt + tools + llm 的结合体，可以实现更复杂的智能体行为。

在上面定义好 Tool 之后，可以通过以下方式调用 Agent：

```py
llm_resp = await self.context.tool_loop_agent(
    event=event,
    chat_provider_id=prov_id,
    prompt="搜索一下 bilibili 上关于 AstrBot 的相关视频。",
    tools=ToolSet([BilibiliTool()]),
    max_steps=30, # Agent 最大执行步骤
    tool_call_timeout=60, # 工具调用超时时间
)
# print(llm_resp.completion_text) # 获取返回的文本
```

`tool_loop_agent()` 方法会自动处理工具调用和大模型请求的循环，直到大模型不再调用工具或者达到最大步骤数为止。

## Multi-Agent

> [!TIP]
> 在 v4.5.7 时加入

Multi-Agent（多智能体）系统将复杂应用分解为多个专业化智能体，它们协同解决问题。不同于依赖单个智能体处理每一步，多智能体架构允许将更小、更专注的智能体组合成协调的工作流程。我们使用 `agent-as-tool` 模式来实现多智能体系统。

在下面的例子中，我们定义了一个主智能体（Main Agent），它负责根据用户查询将任务分配给不同的子智能体（Sub-Agents）。每个子智能体专注于特定任务，例如获取天气信息。

![multi-agent-example-1](https://files.astrbot.app/docs/zh/dev/star/guides/multi-agent-example-1.svg)

定义 Tools:

```py
from pydantic import Field
from pydantic.dataclasses import dataclass

from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext

@dataclass
class AssignAgentTool(FunctionTool[AstrAgentContext]):
    """Main agent uses this tool to decide which sub-agent to delegate a task to."""

    name: str = "assign_agent"
    description: str = "Assign an agent to a task based on the given query"
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to call the sub-agent with.",
                },
            },
            "required": ["query"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        # Here you would implement the actual agent assignment logic.
        # For demonstration purposes, we'll return a dummy response.
        return "Based on the query, you should assign agent 1."


@dataclass
class WeatherTool(FunctionTool[AstrAgentContext]):
    """In this example, sub agent 1 uses this tool to get weather information."""

    name: str = "weather"
    description: str = "Get weather information for a location"
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city to get weather information for.",
                },
            },
            "required": ["city"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        city = kwargs["city"]
        # Here you would implement the actual weather fetching logic.
        # For demonstration purposes, we'll return a dummy response.
        return f"The current weather in {city} is sunny with a temperature of 25°C."


@dataclass
class SubAgent1(FunctionTool[AstrAgentContext]):
    """Define a sub-agent as a function tool."""

    name: str = "subagent1_name"
    description: str = "subagent1_description"
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to call the sub-agent with.",
                },
            },
            "required": ["query"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        ctx = context.context.context
        event = context.context.event
        logger.info(f"the llm context messages: {context.messages}")
        llm_resp = await ctx.tool_loop_agent(
            event=event,
            chat_provider_id=await ctx.get_current_chat_provider_id(
                event.unified_msg_origin
            ),
            prompt=kwargs["query"],
            tools=ToolSet([WeatherTool()]),
            max_steps=30,
        )
        return llm_resp.completion_text


@dataclass
class SubAgent2(FunctionTool[AstrAgentContext]):
    """Define a sub-agent as a function tool."""

    name: str = "subagent2_name"
    description: str = "subagent2_description"
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to call the sub-agent with.",
                },
            },
            "required": ["query"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        return "I am useless :(, you shouldn't call me :("
```

然后，同样地，通过 `tool_loop_agent()` 方法调用 Agent：

```py
@filter.command("test")
async def test(self, event: AstrMessageEvent):
    umo = event.unified_msg_origin
    prov_id = await self.context.get_current_chat_provider_id(umo)
    llm_resp = await self.context.tool_loop_agent(
        event=event,
        chat_provider_id=prov_id,
        prompt="Test calling sub-agent for Beijing's weather information.",
        system_prompt=(
            "You are the main agent. Your task is to delegate tasks to sub-agents based on user queries."
            "Before delegating, use the 'assign_agent' tool to determine which sub-agent is best suited for the task."
        ),
        tools=ToolSet([SubAgent1(), SubAgent2(), AssignAgentTool()]),
        max_steps=30,
    )
    yield event.plain_result(llm_resp.completion_text)
```

## 对话管理器

### 获取会话当前的 LLM 对话历史 `get_conversation`

```py
from astrbot.core.conversation_mgr import Conversation

uid = event.unified_msg_origin
conv_mgr = self.context.conversation_manager
curr_cid = await conv_mgr.get_curr_conversation_id(uid)
conversation = await conv_mgr.get_conversation(uid, curr_cid)  # Conversation
```

::: details Conversation 类型定义

```py
@dataclass
class Conversation:
    """The conversation entity representing a chat session."""

    platform_id: str
    """The platform ID in AstrBot"""
    user_id: str
    """The user ID associated with the conversation."""
    cid: str
    """The conversation ID, in UUID format."""
    history: str = ""
    """The conversation history as a string."""
    title: str | None = ""
    """The title of the conversation. For now, it's only used in WebChat."""
    persona_id: str | None = ""
    """The persona ID associated with the conversation."""
    created_at: int = 0
    """The timestamp when the conversation was created."""
    updated_at: int = 0
    """The timestamp when the conversation was last updated."""
```

:::

### 快速添加 LLM 记录到对话 `add_message_pair`

```py
from astrbot.core.agent.message import (
    AssistantMessageSegment,
    UserMessageSegment,
    TextPart,
)

curr_cid = await conv_mgr.get_curr_conversation_id(event.unified_msg_origin)
user_msg = UserMessageSegment(content=[TextPart(text="hi")])
llm_resp = await self.context.llm_generate(
    chat_provider_id=provider_id, # 聊天模型 ID
    contexts=[user_msg], # 当未指定 prompt 时，使用 contexts 作为输入；同时指定 prompt 和 contexts 时，prompt 会被添加到 LLM 输入的最后
)
await conv_mgr.add_message_pair(
    cid=curr_cid,
    user_message=user_msg,
    assistant_message=AssistantMessageSegment(
        content=[TextPart(text=llm_resp.completion_text)]
    ),
)
```

### 主要方法

#### `new_conversation`

- __Usage__  
  在当前会话中新建一条对话，并自动切换为该对话。
- __Arguments__  
  - `unified_msg_origin: str` – 形如 `platform_name:message_type:session_id`  
  - `platform_id: str | None` – 平台标识，默认从 `unified_msg_origin` 解析  
  - `content: list[dict] | None` – 初始历史消息  
  - `title: str | None` – 对话标题  
  - `persona_id: str | None` – 绑定的 persona ID
- __Returns__  
  `str` – 新生成的 UUID 对话 ID

#### `switch_conversation`

- __Usage__  
  将会话切换到指定的对话。
- __Arguments__  
  - `unified_msg_origin: str`  
  - `conversation_id: str`
- __Returns__  
  `None`

#### `delete_conversation`

- __Usage__  
  删除会话中的某条对话；若 `conversation_id` 为 `None`，则删除当前对话。
- __Arguments__  
  - `unified_msg_origin: str`  
  - `conversation_id: str | None`
- __Returns__  
  `None`

#### `get_curr_conversation_id`

- __Usage__  
  获取当前会话正在使用的对话 ID。
- __Arguments__  
  - `unified_msg_origin: str`
- __Returns__  
  `str | None` – 当前对话 ID，不存在时返回 `None`

#### `get_conversation`

- __Usage__  
  获取指定对话的完整对象；若不存在且 `create_if_not_exists=True` 则自动创建。
- __Arguments__  
  - `unified_msg_origin: str`  
  - `conversation_id: str`  
  - `create_if_not_exists: bool = False`
- __Returns__  
  `Conversation | None`

#### `get_conversations`

- __Usage__  
  拉取用户或平台下的全部对话列表。
- __Arguments__  
  - `unified_msg_origin: str | None` – 为 `None` 时不过滤用户  
  - `platform_id: str | None`
- __Returns__  
  `List[Conversation]`

#### `update_conversation`

- __Usage__  
  更新对话的标题、历史记录或 persona_id。
- __Arguments__  
  - `unified_msg_origin: str`  
  - `conversation_id: str | None` – 为 `None` 时使用当前对话  
  - `history: list[dict] | None`  
  - `title: str | None`  
  - `persona_id: str | None`
- __Returns__  
  `None`

## 人格设定管理器

`PersonaManager` 负责统一加载、缓存并提供所有人格（Persona）的增删改查接口，同时兼容 AstrBot 4.x 之前的旧版人格格式（v3）。  
初始化时会自动从数据库读取全部人格，并生成一份 v3 兼容数据，供旧代码无缝使用。

```py
persona_mgr = self.context.persona_manager
```

### 主要方法

#### `get_persona`

- __Usage__
  获取根据人格 ID 获取人格数据。
- __Arguments__
  - `persona_id: str` – 人格 ID
- __Returns__
  `Persona` – 人格数据，若不存在则返回 None
- __Raises__
  `ValueError` – 当不存在时抛出

#### `get_all_personas`

- __Usage__  
  一次性获取数据库中所有人格。
- __Returns__  
  `list[Persona]` – 人格列表，可能为空

#### `create_persona`

- __Usage__  
  新建人格并立即写入数据库，成功后自动刷新本地缓存。
- __Arguments__  
  - `persona_id: str` – 新人格 ID（唯一）  
  - `system_prompt: str` – 系统提示词  
  - `begin_dialogs: list[str]` – 可选，开场对话（偶数条，user/assistant 交替）  
  - `tools: list[str]` – 可选，允许使用的工具列表；`None`=全部工具，`[]`=禁用全部
- __Returns__  
  `Persona` – 新建后的人格对象
- __Raises__  
  `ValueError` – 若 `persona_id` 已存在

#### `update_persona`

- __Usage__  
  更新现有人格的任意字段，并同步到数据库与缓存。
- __Arguments__  
  - `persona_id: str` – 待更新的人格 ID  
  - `system_prompt: str` – 可选，新的系统提示词  
  - `begin_dialogs: list[str]` – 可选，新的开场对话  
  - `tools: list[str]` – 可选，新的工具列表；语义同 `create_persona`
- __Returns__  
  `Persona` – 更新后的人格对象
- __Raises__  
  `ValueError` – 若 `persona_id` 不存在

#### `delete_persona`

- __Usage__  
  删除指定人格，同时清理数据库与缓存。
- __Arguments__  
  - `persona_id: str` – 待删除的人格 ID
- __Raises__  
  `Valueable` – 若 `persona_id` 不存在

#### `get_default_persona_v3`

- __Usage__  
  根据当前会话配置，获取应使用的默认人格（v3 格式）。  
  若配置未指定或指定的人格不存在，则回退到 `DEFAULT_PERSONALITY`。
- __Arguments__  
  - `umo: str | MessageSession | None` – 会话标识，用于读取用户级配置
- __Returns__  
  `Personality` – v3 格式的默认人格对象

::: details Persona / Personality 类型定义

```py

class Persona(SQLModel, table=True):
    """Persona is a set of instructions for LLMs to follow.

    It can be used to customize the behavior of LLMs.
    """

    __tablename__ = "personas"

    id: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": True})
    persona_id: str = Field(max_length=255, nullable=False)
    system_prompt: str = Field(sa_type=Text, nullable=False)
    begin_dialogs: Optional[list] = Field(default=None, sa_type=JSON)
    """a list of strings, each representing a dialog to start with"""
    tools: Optional[list] = Field(default=None, sa_type=JSON)
    """None means use ALL tools for default, empty list means no tools, otherwise a list of tool names."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": datetime.now(timezone.utc)},
    )

    __table_args__ = (
        UniqueConstraint(
            "persona_id",
            name="uix_persona_id",
        ),
    )


class Personality(TypedDict):
    """LLM 人格类。

    在 v4.0.0 版本及之后，推荐使用上面的 Persona 类。并且， mood_imitation_dialogs 字段已被废弃。
    """

    prompt: str
    name: str
    begin_dialogs: list[str]
    mood_imitation_dialogs: list[str]
    """情感模拟对话预设。在 v4.0.0 版本及之后，已被废弃。"""
    tools: list[str] | None
    """工具列表。None 表示使用所有工具，空列表表示不使用任何工具"""
```

:::


---

<a id="html-to-pic"></a>


# 文转图

> [!TIP]
> 为了方便开发，您可以使用 [AstrBot Text2Image Playground](https://t2i-playground.astrbot.app/) 在线可视化编辑和测试 HTML 模板。

## 基本

AstrBot 支持将文字渲染成图片。

```python
@filter.command("image") # 注册一个 /image 指令，接收 text 参数。
async def on_aiocqhttp(self, event: AstrMessageEvent, text: str):
    url = await self.text_to_image(text) # text_to_image() 是 Star 类的一个方法。
    # path = await self.text_to_image(text, return_url = False) # 如果你想保存图片到本地
    yield event.image_result(url)

```

![image](https://files.astrbot.app/docs/source/images/plugin/image-3.png)

## 自定义(基于 HTML)

如果你觉得上面渲染出来的图片不够美观，你可以使用自定义的 HTML 模板来渲染图片。

AstrBot 支持使用 `HTML + Jinja2` 的方式来渲染文转图模板。

```py{7}
# 自定义的 Jinja2 模板，支持 CSS
TMPL = '''
<div style="font-size: 32px;">
<h1 style="color: black">Todo List</h1>

<ul>
{% for item in items %}
    <li>{{ item }}</li>
{% endfor %}
</div>
'''

@filter.command("todo")
async def custom_t2i_tmpl(self, event: AstrMessageEvent):
    options = {} # 可选择传入渲染选项。
    url = await self.html_render(TMPL, {"items": ["吃饭", "睡觉", "玩原神"]}, options=options) # 第二个参数是 Jinja2 的渲染数据
    yield event.image_result(url)
```

返回的结果:

![image](https://files.astrbot.app/docs/source/images/plugin/fcc2dcb472a91b12899f617477adc5c7.png)

这只是一个简单的例子。得益于 HTML 和 DOM 渲染器的强大性，你可以进行更复杂和更美观的的设计。除此之外，Jinja2 支持循环、条件等语法以适应列表、字典等数据结构。你可以从网上了解更多关于 Jinja2 的知识。

**图片渲染选项(options)**：

请参考 Playwright 的 [screenshot](https://playwright.dev/python/docs/api/class-page#page-screenshot) API。

- `timeout` (float, optional): 截图超时时间.
- `type` (Literal["jpeg", "png"], optional): 截图图片类型.
- `quality` (int, optional): 截图质量，仅适用于 JPEG 格式图片.
- `omit_background` (bool, optional): 是否允许隐藏默认的白色背景，这样就可以截透明图了，仅适用于 PNG 格式
- `full_page` (bool, optional): 是否截整个页面而不是仅设置的视口大小，默认为 True.
- `clip` (dict, optional): 截图后裁切的区域。参考 Playwright screenshot API。
- `animations`: (Literal["allow", "disabled"], optional): 是否允许播放 CSS 动画.
- `caret`: (Literal["hide", "initial"], optional): 当设置为 hide 时，截图时将隐藏文本插入符号，默认为 hide.
- `scale`: (Literal["css", "device"], optional): 页面缩放设置. 当设置为 css 时，则将设备分辨率与 CSS 中的像素一一对应，在高分屏上会使得截图变小. 当设置为 device 时，则根据设备的屏幕缩放设置或当前 Playwright 的 Page/Context 中的 device_scale_factor 参数来缩放.


---

<a id="plugin-config"></a>


# 插件配置

随着插件功能的增加，可能需要定义一些配置以让用户自定义插件的行为。

AstrBot 提供了“强大”的配置解析和可视化功能。能够让用户在管理面板上直接配置插件，而不需要修改代码。

## 配置定义

要注册配置，首先需要在您的插件目录下添加一个 `_conf_schema.json` 的 json 文件。

文件内容是一个 `Schema`（模式），用于表示配置。Schema 是 json 格式的，例如上图的 Schema 是：

```json
{
  "token": {
    "description": "Bot Token",
    "type": "string"
  },
  "sub_config": {
    "description": "测试嵌套配置",
    "type": "object",
    "hint": "xxxx",
    "items": {
      "name": {
        "description": "testsub",
        "type": "string",
        "hint": "xxxx"
      },
      "id": {
        "description": "testsub",
        "type": "int",
        "hint": "xxxx"
      },
      "time": {
        "description": "testsub",
        "type": "int",
        "hint": "xxxx",
        "default": 123
      }
    }
  }
}
```

- `type`: **此项必填**。配置的类型。支持 `string`, `text`, `int`, `float`, `bool`, `object`, `list`, `dict`, `template_list`。当类型为 `text` 时，将会可视化为一个更大的可拖拽宽高的 textarea 组件，以适应大文本。
- `description`: 可选。配置的描述。建议一句话描述配置的行为。
- `hint`: 可选。配置的提示信息，表现在上图中右边的问号按钮，当鼠标悬浮在问号按钮上时显示。
- `obvious_hint`: 可选。配置的 hint 是否醒目显示。如上图的 `token`。
- `default`: 可选。配置的默认值。如果用户没有配置，将使用默认值。int 是 0，float 是 0.0，bool 是 False，string 是 ""，object 是 {}，list 是 []。
- `items`: 可选。如果配置的类型是 `object`，需要添加 `items` 字段。`items` 的内容是这个配置项的子 Schema。理论上可以无限嵌套，但是不建议过多嵌套。
- `invisible`: 可选。配置是否隐藏。默认是 `false`。如果设置为 `true`，则不会在管理面板上显示。
- `options`: 可选。一个列表，如 `"options": ["chat", "agent", "workflow"]`。提供下拉列表可选项。
- `editor_mode`: 可选。是否启用代码编辑器模式。需要 AstrBot >= `v3.5.10`, 低于这个版本不会报错，但不会生效。默认是 false。
- `editor_language`: 可选。代码编辑器的代码语言，默认为 `json`。
- `editor_theme`: 可选。代码编辑器的主题，可选值有 `vs-light`（默认）， `vs-dark`。
- `_special`: 可选。用于调用 AstrBot 提供的可视化提供商选取、人格选取、知识库选取等功能，详见下文。

### 配置项国际化（可选）

配置项的 `description`、`hint` 和下拉选项 `labels` 支持按 WebUI 语言显示，详见[插件国际化](./plugin-i18n)。

其中，如果启用了代码编辑器，效果如下图所示:

![editor_mode](https://files.astrbot.app/docs/source/images/plugin/image-6.png)

![editor_mode_fullscreen](https://files.astrbot.app/docs/source/images/plugin/image-7.png)

**_special** 字段仅 v4.0.0 之后可用。常用可填写值包括 `select_provider`, `select_provider_tts`, `select_provider_stt`, `select_persona`, `select_knowledgebase`，用于让用户快速选择在 WebUI 上已经配置好的模型提供商、人设、知识库等数据。

- `select_provider`、`select_provider_tts`、`select_provider_stt`、`select_persona` 的结果为字符串。
- `select_knowledgebase` 的结果为 `list` 类型，支持多选，建议将对应配置项的 `type` 设为 `list`，默认值设为 `[]`。

> [!NOTE]
> 此外，AstrBot Core 内部还使用了 `select_providers`、`provider_pool`、`persona_pool`、`select_plugin_set`、`t2i_template`、`get_embedding_dim`、`select_agent_runner_provider:*`（`*` 为运行器类型占位符）等 `_special` 值。这些属于内部实现，随时可能变动，请勿在插件中使用。

以 `select_provider` 为例，将呈现以下效果:

![image](https://files.astrbot.app/docs/source/images/plugin/image-select-provider.png)

### file 类型的 schema

在 v4.13.0 之后引入，允许插件定义文件上传配置项，引导用户上传插件所需的文件。

```json
{
  "demo_files": {
    "type": "file",
    "description": "Uploaded files for demo",
    "default": [], // 支持多文件上传，默认值为一个空列表
    "file_types": ["pdf", "docx"] // 允许上传的文件类型列表
  }
}
```

### dict 类型的 schema

用于可视化编辑一个 Python 的 dict 类型的配置。如 AstrBot Core 中的自定义请求体参数配置项：

```py
"custom_extra_body": {
  "description": "自定义请求体参数",
  "type": "dict",
  "items": {},
  "hint": "用于在请求时添加额外的参数，如 temperature、top_p、max_tokens 等。",
  "template_schema": { # 可选填写 template schema，当设置之后，用户可以透过 WebUI 快速编辑。
      "temperature": {
          "name": "Temperature",
          "description": "温度参数",
          "hint": "控制输出的随机性，范围通常为 0-2。值越高越随机。",
          "type": "float",
          "default": 0.6,
          "slider": {"min": 0, "max": 2, "step": 0.1},
      },
      "top_p": {
          "name": "Top-p",
          "description": "Top-p 采样",
          "hint": "核采样参数，范围通常为 0-1。控制模型考虑的概率质量。",
          "type": "float",
          "default": 1.0,
          "slider": {"min": 0, "max": 1, "step": 0.01},
      },
      "max_tokens": {
          "name": "Max Tokens",
          "description": "最大令牌数",
          "hint": "生成的最大令牌数。",
          "type": "int",
          "default": 8192,
      },
  },
}
```

### template_list 类型的 schema

> [!NOTE]
> v4.10.4 引入。更多信息请查看：[#4208](https://github.com/AstrBotDevs/AstrBot/pull/4208)

插件开发者可以在_conf_schema中按照以下格式添加模板配置项（有点类似于原有的嵌套配置）

```json
 "field_id": {
  "type": "template_list",
  "description": "Template List Field",
  "templates": {
    "template_1": {
        "name": "Template One",
        "hint":"hint",
        "items": {
          "attr_a": {
            "description": "Attribute A",
            "type": "int",
            "default": 10
          },
          "attr_b": {
            "description": "Attribute B",
            "hint": "This is a boolean attribute",
            "type": "bool",
            "default": true
          }
        }
      },
    "template_2": {
      "name": "Template Two",
      "hint":"hint",
      "items": {
        "attr_c": {
          "description": "Attribute A",
          "type": "int",
          "default": 10
        },
        "attr_d": {
          "description": "Attribute B",
          "hint": "This is a boolean attribute",
          "type": "bool",
          "default": true
        }
      }
    }
  }
}
```

保存后的 config 为

```json
"field_id": [
    {
        "__template_key": "template_1",
        "attr_a": 10,
        "attr_b": true
    },
    {
        "__template_key": "template_2",
        "attr_c": 10,
        "attr_d": true
    }
]
```

<img width="1000" alt="image" src="https://github.com/user-attachments/assets/74876d30-11a4-491b-a7a0-8ebe8d603782" />

## 在插件中使用配置

AstrBot 在载入插件时会检测插件目录下是否有 `_conf_schema.json` 文件，如果有，会自动解析配置并保存在 `data/config/<plugin_name>_config.json` 下（依照 Schema 创建的配置文件实体），并在实例化插件类时传入给 `__init__()`。

```py
from astrbot.api import AstrBotConfig

class ConfigPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig): # AstrBotConfig 继承自 Dict，拥有字典的所有方法
        super().__init__(context)
        self.config = config
        print(self.config)

        # 支持直接保存配置
        # self.config.save_config() # 保存配置
```

## 配置更新

您在发布不同版本更新 Schema 时，AstrBot 会递归检查 Schema 的配置项，自动为缺失的配置项添加默认值、移除不存在的配置项。


---

<a id="plugin-i18n"></a>

# 插件国际化

插件可以在自己的目录下提供 `.astrbot-plugin/i18n/*.json`，让 WebUI 根据当前语言显示插件名称、描述和配置项文案。

## 目录结构

```text
your_plugin/
  metadata.yaml
  _conf_schema.json
  .astrbot-plugin/
    i18n/
      zh-CN.json
      en-US.json
```

语言文件名使用 WebUI 的 locale，例如 `zh-CN.json`、`en-US.json`。文件内容必须是 JSON object。

当当前语言没有对应翻译、某个字段缺失，或语言文件不存在时，AstrBot 会回退到默认文案：

- 插件名称、卡片短描述和描述回退到 `metadata.yaml` 中的 `display_name`、`short_desc`、`desc`。
- 配置项文案回退到 `_conf_schema.json` 中的 `description`、`hint`、`labels`。
- Page 文案回退到 Page 目录名、Page 默认标题或页面代码中提供的 fallback。

## 元数据

`metadata` 用于覆盖插件在插件页展示的名称、卡片短描述和描述。

```json
{
  "metadata": {
    "display_name": "天气助手",
    "short_desc": "一句话天气查询。",
    "desc": "查询天气并提供出行建议。"
  }
}
```

## 配置项

`config` 用于覆盖 `_conf_schema.json` 中的配置文案。结构按配置项名称嵌套。

例如 `_conf_schema.json`：

```json
{
  "enable": {
    "description": "Enable",
    "type": "bool",
    "hint": "Whether to enable this plugin.",
    "default": true
  },
  "mode": {
    "description": "Mode",
    "type": "string",
    "options": ["fast", "safe"],
    "labels": ["Fast", "Safe"]
  }
}
```

对应 `.astrbot-plugin/i18n/zh-CN.json`：

```json
{
  "config": {
    "enable": {
      "description": "启用",
      "hint": "是否启用这个插件。"
    },
    "mode": {
      "description": "模式",
      "labels": ["快速", "安全"]
    }
  }
}
```

`options` 是配置保存值，不建议翻译。下拉框的展示文本请使用 `labels`。

## 插件 Pages

`pages` 用于覆盖插件 Dashboard Page 的标题、描述和页面内自定义文案。结构按 Page 目录名嵌套。

例如插件页面目录：

```text
pages/
  settings/
    index.html
```

对应 `.astrbot-plugin/i18n/zh-CN.json`：

```json
{
  "pages": {
    "settings": {
      "title": "设置",
      "description": "管理这个插件的高级设置。",
      "save": "保存",
      "reset": "重置"
    }
  }
}
```

`title` 会用于 WebUI 外壳标题和插件详情页中的 Page 组件名称，`description` 会用于插件详情页中的 Page 组件描述。其他字段由页面通过 bridge 自行读取：

```js
const bridge = window.AstrBotPluginPage;

function render() {
  document.getElementById("save").textContent = bridge.t(
    "pages.settings.save",
    "Save",
  );
}

await bridge.ready();
render();
bridge.onContext(render);
```

`onContext()` 用于响应 WebUI 语言切换；监听后通常不需要刷新 Page。

## 嵌套配置

如果 `_conf_schema.json` 中有 `object` 类型配置，翻译也按同样的字段结构继续嵌套。

```json
{
  "config": {
    "sub_config": {
      "name": {
        "description": "名称",
        "hint": "显示在消息中的名称。"
      }
    }
  }
}
```

## 模板列表

`template_list` 的模板名称和模板内字段也可以翻译。模板名称放在 `templates.<模板名>.name`，模板内字段继续往下嵌套。

```json
{
  "config": {
    "rules": {
      "description": "规则",
      "templates": {
        "default": {
          "name": "默认模板",
          "threshold": {
            "description": "阈值",
            "hint": "达到该值后触发规则。"
          }
        }
      }
    }
  }
}
```

## 完整示例

下面是一个真实配置项的英文翻译示例：

```json
{
  "metadata": {
    "display_name": "HAPI Vibe Coding Remote",
    "desc": "Connect to a HAPI service and control coding agent sessions from chat platforms."
  },
  "config": {
    "hapi_endpoint": {
      "description": "HAPI service URL",
      "hint": "Example: http://localhost:3006"
    },
    "output_level": {
      "description": "SSE delivery level",
      "hint": "silence: permission requests only; simple: plain text messages and system events; summary: recent N messages when a task completes; detail: all messages in real time",
      "labels": ["Silence", "Simple", "Summary", "Detail"]
    }
  }
}
```

## 约束

插件国际化只读取 `.astrbot-plugin/i18n` 目录。语言文件必须使用嵌套 JSON 结构，不支持点号扁平 key。


---

<a id="plugin-pages"></a>

# 插件 Pages

AstrBot 支持插件通过 `pages/` 目录暴露 Dashboard 页面。`pages/` 下的每个一级子目录都是一个独立 Page：

```text
astrbot_plugin_page_demo/
├─ main.py
└─ pages/
   ├─ bridge-demo/
   │  ├─ index.html
   │  ├─ app.js
   │  ├─ style.css
   │  └─ assets/
   │     └─ logo.svg
   └─ settings/
      └─ index.html
```

AstrBot 会扫描 `pages/<page_name>/index.html`；没有 `index.html` 的目录会被忽略。

如果只是让用户填写几个配置项，优先使用 [`_conf_schema.json`](./plugin-config.md)。插件 Pages 更适合复杂表单、Dashboard、日志、文件上传下载、SSE 和自定义交互流程。

一旦注册了 Pages，用户可以在：AstrBot WebUI 插件页中的插件卡片中，点击插件卡片进入插件详细页面，在插件详细页面中可以看到并进入注册的 Pages。

## 最小前端示例

`pages/bridge-demo/index.html`

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>Plugin Page Demo</title>
    <link rel="stylesheet" href="./style.css" />
  </head>
  <body>
    <button id="ping">Ping</button>
    <pre id="output"></pre>
    <script type="module" src="./app.js"></script>
  </body>
</html>
```

`pages/bridge-demo/app.js`

```js
const bridge = window.AstrBotPluginPage;
const output = document.getElementById("output");

const context = await bridge.ready();
output.textContent = JSON.stringify(context, null, 2);

document.getElementById("ping").addEventListener("click", async () => {
  const result = await bridge.apiGet("ping");
  output.textContent = JSON.stringify(result, null, 2);
});
```

这里不需要手动引入 bridge SDK。AstrBot 会在返回的 HTML 里自动插入 `/api/plugin/page/bridge-sdk.js`。

## 注册后端 API

前端调用 `bridge.apiGet("ping")` 时，Dashboard 会转发到：

```text
/api/plug/<plugin_name>/ping
```

因此注册 Web API 时，路由必须带上插件名作为前缀：

```python
from quart import jsonify
from astrbot.api.star import Context, Star

PLUGIN_NAME = "astrbot_plugin_page_demo"


class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        context.register_web_api(
            f"/{PLUGIN_NAME}/ping",
            self.page_ping,
            ["GET"],
            "Page ping",
        )

    async def page_ping(self):
        return jsonify({"message": "pong"})
```

## Bridge API

插件 Page 中可直接使用 `window.AstrBotPluginPage`：

- `ready()`: 等待 bridge 就绪并返回上下文
- `getContext()`: 读取当前上下文
- `getLocale()`: 读取当前 WebUI 语言
- `getI18n()`: 读取当前插件的 i18n 资源
- `t(key, fallback)`: 从插件 i18n 资源中按 key 获取文案，缺失时返回 fallback
- `onContext(handler)`: 监听上下文变化，例如 WebUI 切换语言后重新渲染页面
- `apiGet(endpoint, params)`: 发送 GET 请求
- `apiPost(endpoint, body)`: 发送 POST 请求
- `upload(endpoint, file)`: 以 `multipart/form-data` 上传单个文件
- `download(endpoint, params, filename)`: 下载后端响应
- `subscribeSSE(endpoint, handlers, params)`: 订阅 SSE
- `unsubscribeSSE(subscriptionId)`: 取消 SSE 订阅

当前 `ready()` 上下文类似：

```json
{
  "pluginName": "astrbot_plugin_page_demo",
  "displayName": "Plugin Page Demo",
  "pageName": "bridge-demo",
  "pageTitle": "Bridge Demo",
  "locale": "zh-CN",
  "i18n": {}
}
```

`endpoint` 必须是插件内相对路径，不能为空，不能包含 `\`、URL scheme、query、hash，也不能包含 `.` 或 `..` 路径片段。

## Page 国际化

插件 Page 复用插件 i18n 资源文件。给 `.astrbot-plugin/i18n/<locale>.json` 增加 `pages.<page_name>` 即可：

```json
{
  "pages": {
    "bridge-demo": {
      "title": "Bridge 演示页",
      "description": "演示插件页面如何读取 WebUI 语言和翻译资源。",
      "heading": "插件页面",
      "refresh": "重新渲染"
    }
  }
}
```

`title` 会用于 WebUI 外壳标题和插件详情页的 Page 组件名称，`description` 会用于插件详情页的 Page 组件描述。

在 Page 内部使用 `t()` 渲染文案，并用 `onContext()` 响应语言切换：

```js
const bridge = window.AstrBotPluginPage;

function render() {
  document.title = bridge.t("pages.bridge-demo.title", "Bridge Demo");
  document.getElementById("heading").textContent = bridge.t(
    "pages.bridge-demo.heading",
    "Plugin Page",
  );
  document.getElementById("locale").textContent = bridge.getLocale();
}

await bridge.ready();
render();
bridge.onContext(render);
```

切换 WebUI 语言后，Dashboard 会把新的 `locale` 和插件 i18n 资源通过 bridge 发送给 iframe；只要 Page 监听了 `onContext()`，通常不需要刷新页面。

如果你的内联脚本需要同步访问 `window.AstrBotPluginPage`，请把脚本放到外部 module 文件中，或在自己的脚本前显式引入：

```html
<script src="/api/plugin/page/bridge-sdk.js"></script>
```

## 静态资源路径规则

AstrBot 会重写相对资源路径，并自动补上短期 `asset_token`。你只需要正常写相对路径，不要自己拼接 `/api/plugin/page/content/...`。

AstrBot 会重写：

- HTML `src` 和 `href`
- CSS `url(...)`
- JavaScript `import`
- JavaScript `export ... from`
- JavaScript 动态 `import()`

建议把静态资源写成 `./style.css`、`./assets/logo.svg` 这类相对路径。不要手动追加 `asset_token`，也不要依赖 `..` 逃逸 Page 根目录。

如果你构建 SPA，建议使用 hash routing。静态资源服务按真实文件路径解析；history routing 刷新页面时需要对应路径上真的存在文件。

## 安全约束

插件 Pages 运行在受限 iframe 中：

```text
allow-scripts allow-forms allow-downloads
```

Page 不能直接访问 Dashboard cookies、LocalStorage 或同源 DOM，也不能绕过 bridge 复用 Dashboard auth。

AstrBot 还会给资源响应添加安全头，包括：

- `X-Frame-Options: SAMEORIGIN`
- `Content-Security-Policy: frame-ancestors 'self'; object-src 'none'; base-uri 'self'`
- `Cache-Control: no-store`

## 调试建议

- 新增或删除 Page 目录后重载插件
- 修改 `pages/<page_name>/` 下的大多数静态资源后，刷新 Page 即可
- 如果 Page 没出现，检查 `pages/<page_name>/index.html` 是否存在，以及插件是否启用

## 附录：Bridge API 详解

建议在页面脚本开始处保存 bridge 引用：

```js
const bridge = window.AstrBotPluginPage;
```

### `ready()`

等待父页面发送初始上下文，返回 `Promise<context>`。页面初始化时应先等待它，避免过早读取空上下文。

```js
const context = await bridge.ready();
console.log(context.pluginName, context.pageName, context.locale);
```

上下文通常包含：

```json
{
  "pluginName": "astrbot_plugin_page_demo",
  "displayName": "Plugin Page Demo",
  "pageName": "bridge-demo",
  "pageTitle": "Bridge Demo",
  "locale": "zh-CN",
  "i18n": {}
}
```

### `getContext()`

同步读取最近一次上下文。适合在 `ready()` 之后或 `onContext()` 回调中使用。

```js
function renderHeader() {
  const context = bridge.getContext();
  document.getElementById("title").textContent = context.pageTitle;
}
```

### `getLocale()`

同步读取当前 WebUI 语言。没有上下文时默认返回 `zh-CN`。

```js
document.documentElement.lang = bridge.getLocale();
```

### `getI18n()`

同步读取当前插件的完整 i18n 资源对象。一般优先用 `t()`，只有需要自定义遍历或调试时才直接读取。

```js
console.log(Object.keys(bridge.getI18n()));
```

### `t(key, fallback)`

按点分隔 key 从插件 i18n 中取文案。当前语言缺失时会尝试回退，仍缺失则返回 `fallback`。

```js
saveButton.textContent = bridge.t("pages.settings.save", "Save");
```

### `onContext(handler)`

监听上下文变化，返回取消监听函数。WebUI 切换语言时会触发该回调，所以需要响应语言切换的页面应在这里重新渲染。

```js
function render() {
  document.title = bridge.t("pages.settings.title", "Settings");
}

await bridge.ready();
render();

const off = bridge.onContext(render);

window.addEventListener("beforeunload", () => {
  off();
});
```

### `apiGet(endpoint, params)`

向插件后端发送 GET 请求，返回 `Promise<data>`。`endpoint` 是插件内相对路径，Dashboard 会转发到 `/api/plug/<plugin_name>/<endpoint>`。

```js
const stats = await bridge.apiGet("stats", { limit: 20 });
```

后端注册示例：

```python
context.register_web_api(
    f"/{PLUGIN_NAME}/stats",
    self.get_stats,
    ["GET"],
    "Get stats",
)
```

### `apiPost(endpoint, body)`

向插件后端发送 POST 请求，`body` 会作为 JSON 请求体发送，返回 `Promise<data>`。

```js
await bridge.apiPost("settings/save", {
  enabled: true,
  threshold: 0.8,
});
```

### `upload(endpoint, file)`

以 `multipart/form-data` 上传单个文件，字段名为 `file`，返回 `Promise<data>`。

```js
const input = document.querySelector("input[type=file]");
const file = input.files[0];
const result = await bridge.upload("files/import", file);
```

### `download(endpoint, params, filename)`

请求插件后端文件接口并触发浏览器下载。`params` 会作为 query string，`filename` 可选；不传时会尝试使用响应头里的文件名。

```js
await bridge.download("files/export", { format: "json" }, "export.json");
```

### `subscribeSSE(endpoint, handlers, params)`

订阅插件后端 SSE，返回 `Promise<subscriptionId>`。`handlers` 可包含 `onOpen`、`onMessage`、`onError`。

```js
const subscriptionId = await bridge.subscribeSSE(
  "events",
  {
    onOpen() {
      console.log("SSE opened");
    },
    onMessage(event) {
      console.log(event.raw, event.parsed, event.lastEventId);
    },
    onError() {
      console.warn("SSE error");
    },
  },
  { topic: "logs" },
);
```

`event.parsed` 会在消息内容是 JSON 字符串时自动解析，否则等于原始字符串。

### `unsubscribeSSE(subscriptionId)`

取消 SSE 订阅。

```js
await bridge.unsubscribeSSE(subscriptionId);
```

页面卸载时建议清理订阅：

```js
window.addEventListener("beforeunload", () => {
  bridge.unsubscribeSSE(subscriptionId);
});
```

### endpoint 规则

`apiGet`、`apiPost`、`upload`、`download`、`subscribeSSE` 的 `endpoint` 必须是插件内相对路径：

- 允许：`"stats"`、`"settings/save"`、`"files/export"`
- 不允许：空字符串、`"/stats"`、`"../stats"`、`"https://example.com"`、`"stats?x=1"`、`"stats#top"`

query 参数请通过 `params` 传递，不要拼进 `endpoint`。


---

<a id="other"></a>

# 杂项

## 获取消息平台实例

> v3.4.34 后

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test_(self, event: AstrMessageEvent):
    from astrbot.api.platform import AiocqhttpAdapter # 其他平台同理
    platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
    assert isinstance(platform, AiocqhttpAdapter)
    # platform.get_client().api.call_action()
```

## 调用 QQ 协议端 API

```py
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    if event.get_platform_name() == "aiocqhttp":
        # qq
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        assert isinstance(event, AiocqhttpMessageEvent)
        client = event.bot # 得到 client
        payloads = {
            "message_id": event.message_obj.message_id,
        }
        ret = await client.api.call_action('delete_msg', **payloads) # 调用 协议端  API
        logger.info(f"delete_msg: {ret}")
```

关于 CQHTTP API，请参考如下文档：

Napcat API 文档：<https://napcat.apifox.cn/>

Lagrange API 文档：<https://lagrange-onebot.apifox.cn/>

## 获取载入的所有插件

```py
plugins = self.context.get_all_stars() # 返回 StarMetadata 包含了插件类实例、配置等等
```

## 获取加载的所有平台

```py
from astrbot.api.platform import Platform
platforms = self.context.platform_manager.get_insts() # List[Platform]
```


---

<a id="storage"></a>

# 插件存储

## 简单 KV 存储

> [!TIP]
> 该功能需要 AstrBot 版本 >= 4.9.2。

插件可以使用 AstrBot 提供的简单 KV 存储功能来存储一些配置信息或临时数据。该存储是基于插件维度的，每个插件有独立的存储空间，互不干扰。

```py
class Main(star.Star):
    @filter.command("hello")
    async def hello(self, event: AstrMessageEvent):
        """Aloha!"""
        await self.put_kv_data("greeted", True)
        greeted = await self.get_kv_data("greeted", False)
        await self.delete_kv_data("greeted")
```


## 存储大文件规范

为了规范插件存储大文件的行为，请将大文件存储于 `data/plugin_data/{plugin_name}/` 目录下。

你可以通过以下代码获取插件数据目录：

```py
from pathlib import Path
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

plugin_data_path = Path(get_astrbot_data_path()) / "plugin_data" / self.name # self.name 为插件名称，在 v4.9.2 及以上版本可用，低于此版本请自行指定插件名称
```


---

