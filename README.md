# BA 角色卡制作工作流

可复用的 Codex 技能，用于《蔚蓝档案》角色卡与聊天人设制作：从原作资料、参考卡、剧情与人物关系，到二创梗、检索语料和交付核查。

## 技能入口

[skills/ba-character-card/SKILL.md](skills/ba-character-card/SKILL.md)

典型用法：

```text
使用 $ba-character-card，为指定角色整理原作台词、参考卡和二创梗，制作适合目标平台的人设。
```

也适合已有项目的续作，例如对照成熟角色检查缺项、补人物关系、核实旧梗、生成可追溯检索文本。普通角色问答无需加载完整流程。

## 安装

把仓库里的 `skills/ba-character-card` 文件夹复制到当前环境的 Codex 技能目录（例如 `~/.codex/skills/ba-character-card`）。保留子目录，按客户端的技能发现方式重新加载后使用 `$ba-character-card`。

技能中没有机器绝对路径或固定的角色ID；由具体项目提供角色映射、数据源与目标格式。

## 工作流涵盖

- 核实主参考和备用卡，区分完整原包、公开简介、加载壳与抓取失败。
- 固定游戏数据快照与来源校验值，识别实际说话人、联合发言和服装。
- 保留多语言出处、剧情上下文、老师选项与 MomoTalk 跳转。
- 提炼默认剧情阶段、动机、经历、人物关系、口吻和生活反差。
- 核实二创素材，区分原作根源、社区梗、历史版本梗与特定AU。
- 对照成熟角色的资料层次，检查状态、人物记忆、模块接话与角色隔离。
- 保留版本、导出检索文本、核查本地保存和压缩包，并如实报告缺口。
- 按 AstrBot 原生人格 / mem_chat、DeepSeek Harness（DSH）、SillyTavern 的实际版本，适配角色提示、会话绑定和检索资料，并验证实际模型请求。

## 辅助脚本

两个脚本都只使用 Python 标准库，不联网、不调用嵌入服务、不修改运行中的机器人。

```text
python skills/ba-character-card/scripts/export_persona_rag.py --help
python skills/ba-character-card/scripts/verify_project.py --help
```

输入格式、参数与平台适配说明见[交付与验证参考](skills/ba-character-card/references/handoff-and-validation.md)。导出器需要已规范化 JSONL；它不是无需适配的数据爬虫，也不保证能直接安装任意平台角色卡。

## 平台适配

[平台适配参考](skills/ba-character-card/references/agent-platform-adaptation.md)包含 AstrBot 原生人格与 mem_chat 分支、DSH 官方 persona 预设及酒馆兼容插件分支、SillyTavern 字段映射与世界书配置，以及跨角色 / 跨会话验收。DSH 示例固定了核对时的源码提交，其他版本先核对实际 schema。

另附 [SillyTavern V2 JSON 模板](skills/ba-character-card/assets/sillytavern_v2.template.json)，供制作成品时填写；模板不含官方语料，不是成品角色卡或完整前端配置。平台说明与模板的结构检查不等于已在这些平台逐一部署或实聊。

## 验证

技能通过 skill-creator 的格式验证。脚本已使用真实角色归档及小型分支样本验证：目标发言与同伴区分、联合发言、多选标记、阶段与来源保留、MomoTalk 跳转、覆盖保护、缺失标记拒绝、摘要篡改检测，以及原始来源和 ZIP 校验。检查摘要见 [validation.json](validation.json)。

这些验证不等于角色已接入线上机器人或完成长期聊天测试。技能保留这些结果层次的区别。

## 仓库内容范围

本仓库保存通用技能和工具，不包含游戏原文全集、第三方角色卡原包、个人聊天记忆、账号配置或凭据。技能的使用不自动授权外部发布、切换机器人或写入运行数据库。
