# 格式适配、检索导出与交付核查

## 目标平台

AstrBot 原生人格、mem_chat、DSH 与 SillyTavern 的配置位置、字段映射、模板及在线验收见 [平台适配参考](agent-platform-adaptation.md)。先选用户实际使用的平台，不把一种宿主的控制协议套给另一种。

纯文本基础人设可以先单独交付。SillyTavern导入卡应核对用户要求的卡版本与字段；不能把OpenHanako代理包直接称为同格式可导入卡。

mem_chat等插件的主提示之外可能还有state_rules、focus／at／read_air提示、人物印象和persona_rag。检查当前安装版本的实际代码及说明，不能假定本次项目的路径或实现永远相同。资料已导出与线上可运行是不同结果。

人物记忆绑定正确发言人和群／角色范围；亲密倾向、信任和近期心情有不同作用。固定自称、另一个角色的状态兜底、全局角色RAG与扫描目录中的bak.txt文件都是实际应检查的点。没有角色隔离时，不把新角色资料直接混入运行中的旧库。

单独的persona_rag目录可能只按空行分块、全局导入txt／md；遵循实际加载器，正式扫描目录里仅放预期导入的内容。README是否被跳过应先核实。状态键兼容旧宿主不代表需要沿用旧角色的演出。

## export_persona_rag.py 输入

脚本只消费已规范化的本地数据，不读取游戏私有API或自动识别任意原始表。提供JSON配置，所有输入路径相对于项目根目录：

```json
{
  "character_name":"目标角色",
  "target_flag":"character_speaking",
  "joint_flag":"joint_speaking",
  "context_file":"corpus/episode_context.jsonl",
  "dialogue_file":"corpus/dialogue.jsonl",
  "momo_file":"corpus/momo_full_conversations.jsonl",
  "language_priority":["zh_tw","zh_cn_community","ja"],
  "speaker_names":{"原始别名":"中文名"},
  "stages":{"12345":"早期，非当前态度"},
  "groups":[12345],
  "extra_categories":["日常与节日语音"],
  "chunk_chars":1000
}
```

可选输入省略即可。`groups`省略时只导出上下文内确实有目标发言的组；有明确台词研究范围时才限制它。`stages`应由资料提炼而来，不靠GroupId大小猜阶段。配置中的目标标记必须是每条记录的布尔值；联合发言独立标注。

上下文最小字段：`group_id`、`order`、`texts`（语言到文本）、布尔目标标记；推荐`speaker_aliases`、`selection_group`、原始`raw.ScriptKr`与`source`。不要为了让脚本运行而把无法识别的旁白标成目标说话人。

单条日常记录：`id`、`category`、`speaker`、`texts`；可带`variant`、`cv_group`和`source`。MomoTalk另有`message_id`、`message_group_id`、`next_group_id`与`speaker`。脚本保留消息跳转，不将邻近块宣称为一条完整线性剧情。

调用：

```text
python scripts/export_persona_rag.py --root PROJECT --config character_export.json --out OUTPUT
```

默认禁止覆盖已有输出；加`--overwrite`才更新已存在的导出文件。输出目录不能与输入文件重叠。上下文围绕目标发言保留邻近行；分块保留少量重叠。教师多选、分支、原语言、出处定位和其他说话人不可删。

导出后抽查：早期与后期场景、同伴发言、两项以上的老师回复、多语言缺失回退、联合发言和MomoTalk跳转。保留原始归档，检索版只作派生资料。脚本不构建向量库、不调用付费嵌入服务、不切换机器人。

## verify_project.py 输入

```text
python scripts/verify_project.py --root PROJECT --manifest source_manifest.json --jsonl corpus/dialogue.jsonl --zip reading.zip --report verification.json
```

清单文件可有`files`列表，每项含`local_path`、`bytes`、`sha256`。`--jsonl`与`--zip`可重复。脚本逐项记录缺失、大小／摘要不符、解析失败与CRC错误；有失败返回非零状态。不会重下文件或删除资料。

这只验证可读性与保存完整性；剧情提炼、候选卡是否完整、参考是否准确、角色是否自然、在线记忆是否串人，需分别审阅或实际测试。

## 成品检查与打包

- 使用UTF-8，检查乱码、错误角色名／自称／身份、未标注作者示例和缺失引用。
- 核查年龄、生日、形态能力、默认阶段与实装日期；每种语言来源准确。
- 对照正式导出范围统计，不把上下文片段数、重复行或备选分支当独立剧情经历。
- 保留旧稿，列出新增文件、校验、未补缺口与部署状态。
- 轻量人设包和完整原始数据可以分开。ZIP做CRC核查；哈希清单避免包含自己的哈希或制造自引用。复现脚本若需要包外raw／corpus，在包内说明依赖。
- 对已通过且没有新修改的核查无需不断重跑。真正接入后再验证少量典型聊天，而非用“文件验证通过”代替运行效果。

用户要求发布工作流技能时，技能仓库只放通用指令、参数化脚本与小型必要说明。原作语料、第三方卡包、个人记忆与机器凭据不随技能发布；未得到额外指示不改仓库可见性、运行配置或授予权限。


## 立绘表情和 App 素材

立绘裁切、脸红派生、感动／害羞等情绪分类、本人 ID 白名单、历史表情持久化与源码包验证见 [表情构建参考](expression-stickers.md)。使用 `scripts/build_expression_stickers.py` 从已核实的本地原图按配方离线构建，技能本身不附原作图片或完整项目。
