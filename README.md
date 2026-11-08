# BA 角色卡制作工作流

把《蔚蓝档案》的原作台词、剧情、人物关系和二创梗，整理成有来源、能继续维护、适合目标聊天平台的人设。

这是一个可复用的 **Codex 技能（Skill）**。它提供资料整理、角色塑造、平台适配和交付核查的工作流，也附带检索文本导出与文件验证脚本。适合从零制作角色卡，或给已有机器人补剧情记忆、人物关系与知识库。

**快速入口：** [技能正文](skills/ba-character-card/SKILL.md) · [平台接入说明](skills/ba-character-card/references/agent-platform-adaptation.md) · [交付与验证](skills/ba-character-card/references/handoff-and-validation.md)

## 能做什么

- **整理原作资料：** 按实际说话人归档台词，保留服装、语言、剧情阶段、老师选项、联合发言和 MomoTalk 跳转，避免把“提到角色”误当成“角色说过”。
- **制作聊天人设：** 提炼动机、经历、关系、判断习惯、生活反差和口吻，确定默认剧情阶段及与聊天对象的关系。
- **核实二创梗：** 区分原作根源、社区梗、历史版本梗和特定 AU，写清触发、回应与收束方式，避免玩梗覆盖角色本身。
- **补齐已有项目：** 对照成熟角色检查资料缺项、关系记忆、检索语料、状态规则和模块接话，沿用已有进度与来源。
- **适配聊天平台：** 按实际版本整理人格字段、角色绑定、世界书或检索资料，并区分文件生成、成功导入、实际请求与聊天效果。
- **保留可追溯交付：** 保存版本、来源与缺口，导出检索文本，核查归档及压缩包，便于后续修订。

原作原句、作者新写的对话示例和二创设定分别标记。资料覆盖范围以实际取得的来源与快照为准。

## 支持哪些平台

| 目标 | 适配重点 |
| --- | --- |
| 通用纯文本人设 | 独立的中文基础人设、剧情与关系说明、取材记录 |
| AstrBot 原生人格 | 人格内容、会话绑定、知识资料及实际请求核对 |
| AstrBot + mem_chat | 角色 profile、状态规则、会话范围、记忆与检索隔离 |
| DeepSeek Harness（DSH） | 按实际版本配置 persona 预设；区分官方入口与酒馆兼容插件 |
| SillyTavern（酒馆） | 角色字段、V2 JSON、角色世界书、触发与连续追问验证 |

具体步骤见[平台适配参考](skills/ba-character-card/references/agent-platform-adaptation.md)。DSH 示例记录了核对时的源码提交；其他版本先核对实际配置结构。

mem_chat 部分也包含成人模式相关的权限核查：总开关、群聊与私聊白名单、profile gate、状态规则和运行时提示词降级分别检查，不把情绪或关键词当成权限。

这些说明用于指导适配，**不代表已经在每个平台完成部署或长期实聊**。

## 安装

1. 下载或克隆本仓库。
2. 把 `skills/ba-character-card` 整个文件夹复制到当前环境的 Codex 技能目录，保留其中的子目录。
3. 按客户端的技能发现方式重新加载，然后使用 `$ba-character-card` 调用。

常见目录示例：

| 环境 | 技能目录示例 |
| --- | --- |
| Windows | `%USERPROFILE%\.codex\skills\ba-character-card` |
| macOS / Linux | `~/.codex/skills/ba-character-card` |

安装后，`SKILL.md` 应直接位于 `ba-character-card` 文件夹内，而不是多套一层仓库目录。自定义技能目录时，以当前环境配置为准。

仓库提供工作流、工具和模板；角色资料与目标项目由具体任务提供或按需采集。

## 怎么用

把下面示例中的角色名、路径和平台替换成自己的目标即可。已有项目可直接提供项目目录，让技能沿用归档和版本。

### 从零制作角色人设

```text
使用 $ba-character-card，为莉音制作中文聊天人设。
核实原作台词、剧情经历、人物关系和常见二创梗，区分官方事实与改编。
先交付纯文本人设、取材说明和资料缺口。
```

### 接入 AstrBot / mem_chat

```text
使用 $ba-character-card，把现有角色项目适配到 AstrBot 的 mem_chat。
先检查当前插件版本和角色配置，再整理 profile、状态规则和角色专属检索资料。
保留已有版本，说明目标会话如何绑定，并给出接入后的验收方法。
```

### 制作酒馆角色卡

```text
使用 $ba-character-card，根据现有归档制作 SillyTavern V2 JSON 角色卡。
包含核心人设、开场、标明为新写的对话示例，以及人物关系和剧情世界书。
保留来源说明，检查角色卡字段与世界书结构。
```

### 适配 DSH

```text
使用 $ba-character-card，把现有纯文本人设适配到 DSH。
先核对我安装的版本与 persona 入口，保留所需工具和记忆模块，
生成对应配置及测试步骤，说明哪些只完成文件检查、哪些已实际验证。
```

### 继续完善已有角色

```text
使用 $ba-character-card，review 当前角色项目，对照已有成熟角色检查缺项。
重点看剧情阶段、人物关系、原作口吻、二创梗和检索语料。
先复用现有来源和归档，列出差异并补齐，不重复大规模采集。
```

为了减少返工，任务里可以附上：**角色及服装版本、目标平台与版本、已有项目目录、主参考、默认剧情阶段、与聊天对象的关系、希望交付的格式**。需要部署或在线测试时，再说明目标会话与范围。

没有指定格式时，先制作独立的中文纯文本基础人设和取材说明。普通角色问答无需加载完整制作流程。

## 会得到什么

按任务范围交付，通常包括：

| 内容 | 用途 |
| --- | --- |
| 基础人设与平台文件 | 核心身份、口吻、动机、关系、开场及目标平台所需字段 |
| 剧情与人物关系资料 | 保留阶段与上下文，方便持续补充和纠错 |
| 检索文本或世界书 | 按人物、事件、设定和相关梗整理可检索条目 |
| 来源清单与取材说明 | 区分原作、第三方参考、二创和新写内容 |
| 验证记录与缺口 | 说明已保存、已导出、已导入或已实测的范围，以及仍缺的内容 |

长篇原始资料和轻量阅读包可分开保存；修订时保留旧版本。具体交付结构见[交付与验证参考](skills/ba-character-card/references/handoff-and-validation.md)。

## 仓库导航

```text
skills/ba-character-card/
├── SKILL.md                              # 技能入口与制作流程
├── agents/openai.yaml                    # 技能展示信息
├── references/
│   ├── sources-and-corpus.md             # 来源采集与原作归档
│   ├── persona-and-memes.md              # 人格提炼、关系与二创梗
│   ├── agent-platform-adaptation.md      # AstrBot / mem_chat / DSH / 酒馆
│   └── handoff-and-validation.md         # 导出、交付与核查
├── scripts/
│   ├── export_persona_rag.py             # 规范化 JSONL → 检索文本
│   └── verify_project.py                # 来源、JSONL 与 ZIP 验证
└── assets/
    └── sillytavern_v2.template.json      # 待填写的 V2 JSON 模板
```

[SillyTavern 模板](skills/ba-character-card/assets/sillytavern_v2.template.json)不含官方语料，供制作成品时填写；它不是成品角色卡、PNG 图片卡或完整前端配置。

## 辅助脚本与验证

两个脚本都只使用 Python 标准库，不联网、不调用嵌入服务、不修改运行中的机器人。可在仓库根目录查看参数：

```sh
python skills/ba-character-card/scripts/export_persona_rag.py --help
python skills/ba-character-card/scripts/verify_project.py --help
```

导出器的输入是**已经规范化的 JSONL**，格式与参数见[交付与验证参考](skills/ba-character-card/references/handoff-and-validation.md)。它不负责自动抓取任意游戏数据、建立向量库或完成平台导入。

已有验证记录见 [validation.json](validation.json)：技能通过格式验证；脚本使用真实角色归档及小型分支样本检查了说话人区分、联合发言、多选标记、阶段与来源保留、MomoTalk 跳转、覆盖保护、缺失标记拒绝、摘要篡改检测，以及原始来源和 ZIP 校验。

这些结果说明本地文件处理与完整性检查的覆盖范围，不替代剧情理解评估、线上部署验收或长期聊天测试。

## 内容与使用范围

本仓库保存通用技能、脚本和必要模板，不包含游戏原文全集、第三方角色卡原包、个人聊天记忆、账号配置或凭据。使用第三方资料时保留来源，并遵循对应资料的使用条件。

制作资料、生成草稿与切换运行中的机器人分别处理。技能的使用不自动授权外部发布、发送消息、修改运行数据库或切换角色；已有明确授权时，按授权范围完成工作。
