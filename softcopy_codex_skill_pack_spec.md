# SoftCopy Codex Skill Pack 统一规范

## 0. 文档状态

- 文档角色：唯一权威规范（single source of truth）
- 生效日期：2026-04-24
- 适用对象：后续 coding、`AGENTS.md`、各个 `SKILL.md`、schemas、contracts、rules、evals、项目介绍文案
- 废止文档：
  - `softcopy_codex_skill_pack_spec (1).md`
  - `improve.md`
- 优先级规则：
  1. 本文档优先于历史规格、修订说明、零散讨论
  2. 后续实现出的 `softcopy/contracts/*.yaml`、`softcopy/rules/*.yaml`、`softcopy/schemas/*.json` 必须与本文档保持一致
  3. 若代码、README、`AGENTS.md`、`SKILL.md`、schema、rule file 与本文档冲突，以本文档为准，先修规格对应文件，再继续开发

---

## 1. 标准介绍口径

### 1.1 中文标准介绍

SoftCopy Codex Skill Pack 是一套面向 Codex 的软件著作权材料生成与校验规范和 `Skill + CLI` 工具包。它从已完成并可运行的软件项目仓库出发，分离“显式事实”“仓库证据”“草稿生成”“字段追溯”“规则校验”五个层面，目标不是自动编造可提交材料，而是稳定产出可人工复核、可追溯、可阻断校验的申请材料包。

### 1.2 English Standard Intro

SoftCopy Codex Skill Pack is a Codex-first specification and `Skill + CLI` toolkit for generating and validating software copyright application materials from a finished and runnable software repository. It does not fabricate legal facts. It separates explicit facts, repository evidence, drafting, traceability, and validation so that every formal output is reviewable and every submission-ready conclusion is rule-backed.

---

## 2. 目标与非目标

### 2.1 目标

本规范用于指导实现一套 skill pack，从代码仓库和人工确认事实出发，生成或辅助生成以下材料：

1. 软件著作权登记申请表草稿
2. 源程序鉴别材料
3. 文档鉴别材料
4. 权属/证明材料清单
5. 校验与合规报告
6. 可编辑的结构化中间产物
7. 可审计的字段追溯报告

### 2.2 非目标

本规范明确不做以下事情：

1. 不自动提交软著平台
2. 不把 README、Git 时间、仓库名、commit author 直接升格为法律事实
3. 不把论坛经验或社区文章直接写成 `ERROR`
4. 不把 scan 结果直接写成正式申请事实
5. 不在事实缺失时伪造“可直接提交”状态
6. 不只输出 PDF 而丢失结构化中间文件

---

## 3. 规范性用语

本文中的规范词含义如下：

- `MUST` / “必须”：硬性要求，违反即为规格错误
- `MUST NOT` / “禁止”：硬性禁止，违反即为规格错误
- `SHOULD` / “应当”：强建议，若偏离必须有明确理由
- `MAY` / “可以”：允许，但不是强制

---

## 4. 总体架构

本项目发布形态为 `Skill + CLI`。Codex skill pack 是交互式工作流入口，Python CLI 是迁移、演示和自动化验证入口。两者 MUST 共用 `softcopy_tool/` 中的同一套实现，不允许在各 skill 脚本中复制核心逻辑。

本项目逻辑分为两层，不允许混写。

### 4.1 Layer A：工程实现规范

负责定义：

- 目录结构
- skill 划分与职责边界
- 状态机
- 输入输出契约
- traceability 数据模型
- schemas
- evals
- CLI commands
- migration behavior

### 4.2 Layer B：规则映射层

负责定义：

- 官方规则条目
- 适用范围
- 严重度
- 阈值
- 来源元数据
- 生效条件

### 4.3 分层约束

1. 工程实现逻辑 MUST 读取 `contracts/`、`schemas/`、`rules/`，而不是把规则硬编码进 prompt 或脚本
2. 规则变化时 SHOULD 优先改 `softcopy/rules/`，而不是直接改 skill 行为
3. 若某项 `ERROR` 没有完整规则来源元数据，则该项 MUST NOT 作为 `ERROR` 生效
4. `.agents/skills/*/scripts` MUST 是 thin wrapper，调用 `softcopy_tool.workflow` 或 CLI，不得重新实现业务逻辑
5. `init` MUST 迁移 `.agents/`、`softcopy_tool/`、`softcopy/contracts/`、`softcopy/rules/`、`softcopy/schemas/`、模板 YAML 和填写指南，且默认不覆盖目标仓库已有文件

---

## 5. 全局设计原则

### 5.1 事实优先

以下字段属于关键申请事实，不得仅凭模型推断直接进入正式材料：

- `software_name_full`
- `version`
- `development_completion_date`
- `first_publication_status`
- `first_publication_date`
- `copyright_owner_type`
- `copyright_owners`
- `development_mode`
- `project_type`

### 5.2 候选证据与正式事实分离

仓库扫描器可以产生候选值，但这些值默认只属于候选证据层，不属于正式事实层。

### 5.3 正式材料必须可追溯

所有正式输出字段 MUST 能追溯到至少一个来源对象。

### 5.4 生成与校验分离

正式输出必须先 compose，再 validate。未通过 validate，禁止生成 `READY_TO_SUBMIT.flag`。

### 5.5 文档策略按项目类型切换

不得默认所有项目都生成 GUI 用户手册。文档策略必须根据 `project_type`、`has_gui`、`has_backend_api`、feature 形态进行切换。

### 5.6 单一规范优先

后续 coding、文案介绍、PR 说明、skill intro、README 段落，均应以本文档中的术语与状态定义为准。

---

## 6. 目录结构

```text
.gitignore
LICENSE
README.md
pyproject.toml

.agents/
  AGENTS.md
  skills/
    softcopy-intake/
      SKILL.md
      references/
    softcopy-scan-repo/
      SKILL.md
      scripts/
      references/
    softcopy-feature-map/
      SKILL.md
      references/
    softcopy-application/
      SKILL.md
      scripts/
      templates/
      references/
    softcopy-code-doc/
      SKILL.md
      scripts/
      templates/
      references/
    softcopy-manual/
      SKILL.md
      scripts/
      templates/
      references/
    softcopy-proof-check/
      SKILL.md
      references/
    softcopy-validate/
      SKILL.md
      scripts/
      references/

softcopy_tool/
  __init__.py
  __main__.py
  cli.py
  support.py
  workflow.py

softcopy/
  contracts/
    required_facts.yaml
    traceability.schema.json
  rules/
    registration_rules.yaml
    heuristics.yaml
  schemas/
    project_facts.schema.json
    feature_map.schema.json
    manual_manifest.schema.json
    ownership_evidence.schema.json
    application_fields.schema.json
  project_facts.yaml
  feature_map.yaml
  manual_manifest.yaml
  ownership_evidence.yaml
  outputs/
    # runtime generated files ignored by git;
    # only directory .gitkeep files may be tracked
    intake/
    scan/
    feature_map/
    application/
    code_doc/
    manual/
    proof_check/
    validation/
    traceability/
    package/

evals/
  trigger/
    positive_cases.yaml
    negative_cases.yaml
  contracts/
    required_facts_cases.yaml
    traceability_cases.yaml
  artifacts/
    application_draft_cases.yaml
    validation_cases.yaml

examples/
  minimal-project/
    README.md
    src/
    docs/

docs/
  project_facts_guide.md
```

### 6.1 Git 跟踪规则

1. `softcopy/outputs/**` MUST 被 `.gitignore` 忽略
2. `softcopy/outputs/**/.gitkeep` MAY 被跟踪，用于保留目录结构
3. `__pycache__/`、`*.pyc`、构建产物、本地 IDE 文件 MUST 被忽略
4. `examples/*` 下由 `init` 生成的 `.agents/`、`softcopy/`、`softcopy_tool/` 和 `softcopy_support.py` MUST 被忽略，避免读者运行 Quickstart 后污染仓库状态

### 6.2 CLI 公共接口

以下命令 MUST 可通过 `python3 -m softcopy_tool` 执行：

```text
init --target <repo>
intake --repo-root <repo>
scan --repo-root <repo>
feature-map --repo-root <repo>
proof-check --repo-root <repo>
application --repo-root <repo>
code-doc --repo-root <repo> --formats md,pdf,docx
manual --repo-root <repo> --formats md,pdf,docx
validate --repo-root <repo>
run-all --repo-root <repo> --formats md,pdf,docx
evals --repo-root <repo>
clean --repo-root <repo>
```

`run-all` 的标准顺序 MUST 为 `scan -> intake -> feature-map -> proof-check -> manual -> application -> code-doc -> validate`。`clean` MUST 只清理 `softcopy/outputs/**` 中的运行生成物，不得删除 facts、contracts、rules、schemas 或人工 review 文件。

`--formats` 默认值 MUST 为 `md`。`pdf` 和 `docx` MUST 通过 optional dependency 实现；未安装依赖时，默认 Markdown/JSON 流程仍必须可运行，显式请求 PDF/DOCX 时必须失败并给出安装指令。

---

## 7. 全局状态与数据模型

## 7.1 `field_status` 枚举

```yaml
field_status:
  - confirmed
  - candidate
  - derived
  - needs_confirmation
  - missing
  - not_applicable
```

含义如下：

- `confirmed`：已被明确人工确认，可进入正式材料
- `candidate`：来自候选证据或弱支持，不可直接进入正式材料中的关键事实
- `derived`：由代码/结构/规则推导得出，可用于描述性字段，但不可充当关键法律事实
- `needs_confirmation`：系统知道这个字段存在，但当前未获得足够确认
- `missing`：字段为空且未找到可用候选
- `not_applicable`：在当前条件下不适用

## 7.2 `draft_status` 枚举

```yaml
draft_status:
  - intake_incomplete
  - ready_for_scan
  - scan_complete
  - feature_map_pending_review
  - provisional_application_draft
  - formal_application_blocked
  - formal_application_ready
  - artifacts_pending_validation
  - package_validation_failed
  - ready_to_submit
```

## 7.3 正式态准入规则

这是本规范最重要的阻断规则。

1. 任何 `core_required_fact` 在进入 `formal_application_ready` 之前，其 `status` MUST 为 `confirmed`
2. 任何已触发的 `conditional_required_fact` 在进入 `formal_application_ready` 之前，其 `status` MUST 为 `confirmed`
3. `candidate` 和 `derived` 可以用于：
   - `repo_scan.json`
   - `module_candidates.yaml`
   - feature 提案
   - `intake_report.md`
   - `provisional_application_draft`
4. `candidate` 和 `derived` MUST NOT 作为关键申请事实写入：
   - `application_fields.json` 的关键事实字段
   - `application_draft.md` 的正式事实栏
   - `READY_TO_SUBMIT.flag`
5. validator 若发现关键事实字段在正式态仍为 `candidate`、`derived`、`needs_confirmation` 或 `missing`，必须报 `ERROR`

## 7.4 字段封装（Field Envelope）

所有会被 validator 消费的关键字段 MUST 使用统一封装，而不是裸字符串。

```json
{
  "value": "V1.0",
  "status": "confirmed",
  "blocking": true,
  "owner_skill": "softcopy-intake",
  "sources": [
    {
      "source_type": "explicit_fact",
      "source_ref": "softcopy/project_facts.yaml#/facts/version",
      "authority_level": "B",
      "confidence": 1.0
    }
  ],
  "last_updated_by": "softcopy-intake"
}
```

### 7.4.1 `source_type` 枚举

```yaml
source_type:
  - explicit_fact
  - human_review
  - repository_file
  - repo_scan
  - feature_map
  - manual_manifest
  - ownership_evidence
  - generated_template
  - rule_file
```

### 7.4.2 封装使用范围

以下文件中的 validator 关键字段 MUST 使用 envelope：

- `softcopy/project_facts.yaml`
- `softcopy/feature_map.yaml` 中会被 application/manual/code-doc 消费的功能声明字段
- `softcopy/outputs/application/application_fields.json`
- `softcopy/outputs/application/application_trace.json`
- `softcopy/outputs/code_doc/page_trace.json`
- `softcopy/outputs/manual/manual_trace.json`

### 7.4.3 Traceability 最低要求

1. 每个 `blocking: true` 的字段 MUST 至少有一个 `sources[]`
2. `source_ref` MUST 可机器定位：
   - 本地文件用 `path#/json-pointer`
   - Markdown 章节用 `path#heading-id`
   - rule 文件用 `path#/rules/<rule_id>`
3. 若正式字段缺少 `sources[]`，validator 必须报 `ERROR`

---

## 8. `required_facts.yaml` 契约

`softcopy/contracts/required_facts.yaml` 是关键事实阻断规则的唯一机器真值源。

建议结构如下：

```yaml
core_required_facts:
  - field: software_name_full
    accepted_statuses:
      formal_application_ready: [confirmed]
      ready_to_submit: [confirmed]

  - field: version
    accepted_statuses:
      formal_application_ready: [confirmed]
      ready_to_submit: [confirmed]

  - field: development_completion_date
    accepted_statuses:
      formal_application_ready: [confirmed]
      ready_to_submit: [confirmed]

  - field: first_publication_status
    accepted_statuses:
      formal_application_ready: [confirmed]
      ready_to_submit: [confirmed]

  - field: copyright_owner_type
    accepted_statuses:
      formal_application_ready: [confirmed]
      ready_to_submit: [confirmed]

  - field: copyright_owners
    accepted_statuses:
      formal_application_ready: [confirmed]
      ready_to_submit: [confirmed]

  - field: development_mode
    accepted_statuses:
      formal_application_ready: [confirmed]
      ready_to_submit: [confirmed]

  - field: project_type
    accepted_statuses:
      formal_application_ready: [confirmed]
      ready_to_submit: [confirmed]

conditional_required_facts:
  - field: first_publication_date
    when:
      field: first_publication_status
      equals: published
    accepted_statuses:
      formal_application_ready: [confirmed]
      ready_to_submit: [confirmed]

optional_facts:
  - software_name_short
  - application_scenario
  - technical_highlights
  - notes
```

### 8.1 正式决议

1. `software_name_short`：可选，不阻断
2. `first_publication_status`：正式态必需，不允许默认成 `unpublished`
3. `first_publication_date`：仅当 `first_publication_status.value = published` 且 `status = confirmed` 时变成条件必需

### 8.2 关于 `first_publication_status` 的强规则

这是对上一轮修订的最终修正。

1. `first_publication_status` MUST NOT 默认写成 `unpublished`
2. 初始化时应该写成：
   - `value: ""`
   - `status: needs_confirmation`
3. intake 可以在 `intake_report.md` 中给出候选意见，但 MUST NOT 在 `project_facts.yaml` 中把候选直接落成正式值
4. 只有在人工确认后，才允许把 `value` 写为 `published` 或 `unpublished`

### 8.3 Readiness 判定算法

validator 的判定顺序必须是：

1. 读取 `required_facts.yaml`
2. 枚举 `core_required_facts`
3. 对每个字段读取 `status`
4. 若当前阶段为 `formal_application_ready` 或 `ready_to_submit`：
   - 只接受该字段在 `accepted_statuses` 中列出的状态
   - 其余状态全部报 `ERROR`
5. 枚举 `conditional_required_facts`
6. 仅当 `when` 条件被满足时，再执行相同检查
7. 若有任一 `ERROR`，禁止创建 `READY_TO_SUBMIT.flag`

---

## 9. 关键结构化文件规范

## 9.1 `project_facts.yaml`

`project_facts.yaml` 不再使用“裸字段 + 旁路 fact_sources”的旧设计，改为统一 envelope。

建议结构：

```yaml
filing_context:
  jurisdiction: "CN"
  office: ""

facts:
  software_name_full:
    value: ""
    status: needs_confirmation
    blocking: true
    owner_skill: softcopy-intake
    sources: []

  software_name_short:
    value: ""
    status: missing
    blocking: false
    owner_skill: softcopy-intake
    sources: []

  version:
    value: ""
    status: needs_confirmation
    blocking: true
    owner_skill: softcopy-intake
    sources: []

  development_completion_date:
    value: ""
    status: needs_confirmation
    blocking: true
    owner_skill: softcopy-intake
    sources: []

  first_publication_status:
    value: ""
    status: needs_confirmation
    blocking: true
    owner_skill: softcopy-intake
    sources: []

  first_publication_date:
    value: ""
    status: needs_confirmation
    blocking: true
    owner_skill: softcopy-intake
    sources: []

  copyright_owner_type:
    value: ""
    status: needs_confirmation
    blocking: true
    owner_skill: softcopy-intake
    sources: []

  copyright_owners:
    value: []
    status: needs_confirmation
    blocking: true
    owner_skill: softcopy-intake
    sources: []

  development_mode:
    value: ""
    status: needs_confirmation
    blocking: true
    owner_skill: softcopy-intake
    sources: []

  project_type:
    value: ""
    status: needs_confirmation
    blocking: true
    owner_skill: softcopy-intake
    sources: []

profile:
  has_gui:
    value: false
    status: derived
    blocking: false
    owner_skill: softcopy-scan-repo
    sources: []

  has_backend_api:
    value: false
    status: derived
    blocking: false
    owner_skill: softcopy-scan-repo
    sources: []

  primary_languages:
    value: []
    status: derived
    blocking: false
    owner_skill: softcopy-scan-repo
    sources: []

  entry_points:
    value: []
    status: candidate
    blocking: false
    owner_skill: softcopy-scan-repo
    sources: []

  runtime_environment:
    value:
      os: []
      database: []
      middleware: []
      browser: []
      other_dependencies: []
    status: candidate
    blocking: false
    owner_skill: softcopy-scan-repo
    sources: []

  application_scenario:
    value: ""
    status: needs_confirmation
    blocking: false
    owner_skill: softcopy-intake
    sources: []

  technical_highlights:
    value: []
    status: candidate
    blocking: false
    owner_skill: softcopy-application
    sources: []

status:
  draft_status: intake_incomplete
```

补充规则：

1. 当 `first_publication_status.status != confirmed` 时，`first_publication_date` MUST 保持 `needs_confirmation` 或 `missing`
2. 只有当 `first_publication_status.value = unpublished` 且已确认时，`first_publication_date` 才可以被规范化为 `not_applicable`
3. 只有当 `first_publication_status.value = published` 且已确认时，`first_publication_date` 才进入条件必填检查

## 9.2 `feature_map.yaml`

`feature_map.yaml` 在正式阶段是硬前置，但在 MVP 的 provisional draft 阶段不是绝对前置。

建议结构：

```yaml
review_status: pending_review
features:
  - feature_id: FEAT-001
    review_status: pending_review
    name:
      value: 用户登录与权限控制
      status: derived
      blocking: false
      owner_skill: softcopy-feature-map
      sources: []
    summary:
      value: 实现用户身份认证、会话管理与角色权限控制。
      status: derived
      blocking: false
      owner_skill: softcopy-feature-map
      sources: []
    priority: high
    source_paths:
      - backend/auth/
      - frontend/src/pages/login/
    routes_or_commands:
      - /login
      - POST /api/auth/login
    ui_pages:
      - 登录页
      - 权限管理页
    api_groups:
      - Auth API
    manual_sections:
      - SEC-001
    screenshot_ids:
      - SS-001
    application_claims:
      - 提供用户认证与权限管理功能
```

### 9.2.1 约束

1. 每个 feature MUST 至少映射到：
   - 一组源码路径
   - 一项申请表功能描述
   - 一节文档章节
2. `review_status != approved` 时：
   - application 只能输出 provisional draft
   - validator 不能给出 submission-ready 结论

## 9.3 `manual_manifest.yaml`

`manual_manifest.yaml` 是正式版文档清单文件。生成流程是半自动，不是纯手写，也不是一次性全自动。

建议结构：

```yaml
manifest_status: pending_review
doc_type: user_manual
sections:
  - section_id: SEC-001
    title: 系统登录
    goal: 指导用户完成系统登录
    prerequisites:
      - 系统已部署并运行
      - 用户已获得账号密码
    steps:
      - 打开系统首页
      - 输入账号和密码
      - 点击登录按钮
    expected_result: 进入系统首页
    screenshot_ids:
      - SS-001
    notes:
      - 若密码错误，系统会提示重新输入
screenshots:
  - screenshot_id: SS-001
    path: docs/screenshots/01-login.png
    caption: 系统登录界面
    source: real_running_ui
```

### 9.3.1 约束

1. `source` MUST 标明：
   - `real_running_ui`
   - `api_diagram`
   - `command_output`
2. `path` 为空时不得伪装为已完成
3. `manifest_status != approved` 时，manual 只能输出草稿，不能进入 ready-to-submit

## 9.4 `ownership_evidence.yaml`

该文件统一使用 `development_mode`，禁止再出现 `ownership_mode`。

建议结构：

```yaml
evidence_status: pending_review
development_mode: independent
required_documents:
  - doc_id: PROOF-001
    name: 身份证明
    required: true
    provided: false
    file_ref: ""
  - doc_id: PROOF-002
    name: 项目任务书
    required: false
    provided: false
    file_ref: ""
notes: ""
```

## 9.5 `application_fields.json`

`application_fields.json` 是 application 层的结构化权威产物。关键事实字段必须继续使用 envelope。

建议结构：

```json
{
  "draft_mode": "provisional",
  "software_name_full": {
    "value": "",
    "status": "needs_confirmation",
    "blocking": true,
    "owner_skill": "softcopy-application",
    "sources": []
  },
  "software_name_short": {
    "value": "",
    "status": "missing",
    "blocking": false,
    "owner_skill": "softcopy-application",
    "sources": []
  },
  "version": {
    "value": "",
    "status": "needs_confirmation",
    "blocking": true,
    "owner_skill": "softcopy-application",
    "sources": []
  },
  "development_completion_date": {
    "value": "",
    "status": "needs_confirmation",
    "blocking": true,
    "owner_skill": "softcopy-application",
    "sources": []
  },
  "first_publication_status": {
    "value": "",
    "status": "needs_confirmation",
    "blocking": true,
    "owner_skill": "softcopy-application",
    "sources": []
  },
  "copyright_owner_type": {
    "value": "",
    "status": "needs_confirmation",
    "blocking": true,
    "owner_skill": "softcopy-application",
    "sources": []
  },
  "copyright_owners": {
    "value": [],
    "status": "needs_confirmation",
    "blocking": true,
    "owner_skill": "softcopy-application",
    "sources": []
  },
  "development_mode": {
    "value": "",
    "status": "needs_confirmation",
    "blocking": true,
    "owner_skill": "softcopy-application",
    "sources": []
  },
  "project_type": {
    "value": "",
    "status": "needs_confirmation",
    "blocking": true,
    "owner_skill": "softcopy-application",
    "sources": []
  },
  "main_functions": [
    {
      "value": "",
      "status": "derived",
      "blocking": false,
      "owner_skill": "softcopy-application",
      "sources": []
    }
  ],
  "technical_highlights": [],
  "runtime_environment": {},
  "needs_confirmation": []
}
```

约束：

1. `draft_mode = formal` 时，所有 `core_required_facts` 的 `status` MUST 为 `confirmed`
2. `draft_mode = provisional` 时，未确认字段必须保留在 `needs_confirmation[]` 中
3. `main_functions` 可以是 `derived`，但必须可追溯到 `feature_map` 或 scan evidence

## 9.6 `validation_report.md`

`validation_report.md` 的最少结构如下：

1. Summary
2. Activated rules
3. Errors
4. Warnings
5. Informational notes
6. Traceability gaps
7. Submission readiness conclusion
8. Required next fixes

## 9.7 `traceability_report.md`

`softcopy/outputs/traceability/traceability_report.md` 的最少结构如下：

1. Scope of traced artifacts
2. Blocking facts and their sources
3. Application field traces
4. Code page traces
5. Manual section and screenshot traces
6. Unresolved trace gaps
7. Final traceability conclusion

若第 6 节非空，validator 不得给出 ready-to-submit。

---

## 10. 规则文件规范

## 10.1 `registration_rules.yaml` 是唯一硬规则源

validator 的 `ERROR` 规则必须来自 `softcopy/rules/registration_rules.yaml` 中处于 `active` 状态的规则。

### 10.1.1 规则结构

```yaml
rules:
  - rule_id: REG-020
    title: front_back_pages
    rule_status: draft
    severity_default: ERROR
    authority_level: A
    source_type: official
    source_name: ""
    source_ref: ""
    source_locator: ""
    jurisdiction: CN
    scope_level: national
    office_selector: []
    effective_version: ""
    effective_from: ""
    last_reviewed_at: ""
    reviewed_by: ""
    applies_to:
      - code_doc
      - manual_doc
    threshold:
      front_pages: 30
      back_pages: 30
      fallback_if_total_lt: 60
    notes: ""
```

`rule_status` 允许值：

- `draft`
- `active`
- `deprecated`

### 10.1.2 必填来源元数据

若规则要以 `ERROR` 生效，下列字段必须全部非空：

- `rule_id`
- `rule_status = active`
- `severity_default`
- `authority_level`
- `source_type`
- `source_name`
- `source_ref`
- `source_locator`
- `jurisdiction`
- `scope_level`
- `effective_version`
- `effective_from`
- `last_reviewed_at`
- `reviewed_by`

### 10.1.3 不完整来源的处理

1. 若来源元数据不完整，该规则 MUST NOT 产出 `ERROR`
2. 此时 validator 最多只能输出：
   - `WARNING`：规则存在但未完成法源配置
   - `INFO`：规则模板已定义但未激活

### 10.1.4 本地规则的激活条件

由于全国规则和地方办事指南可能混用，因此必须增加受理地选择。

规则激活逻辑如下：

1. `scope_level = national`：
   - 当 `project_facts.yaml#/filing_context/jurisdiction` 匹配时生效
2. `scope_level = local`：
   - 仅当 `project_facts.yaml#/filing_context/office` 命中 `office_selector` 时生效
3. 若地方规则存在但 `office` 未确认：
   - 不得直接报 `ERROR`
   - 应报 `WARNING`，提示受理地未确认，地方规则未激活

### 10.1.5 `authority_level` 定义

```yaml
authority_level:
  A: 官方法律/规章/办事指南，可产出 ERROR
  B: 官方平台或官方工程机制文档，可产出实现契约 ERROR
  C: 社区经验，只能产出 WARNING 或 INFO
```

## 10.2 `heuristics.yaml`

以下内容只允许进入 `heuristics.yaml`，不得直接写成 `ERROR`：

- 最后一页最好落在模块结束
- 截图重复度过高
- UI 壳层占比过高
- 文案营销味过重
- README 不应塞入 skill 主文件

---

## 11. Skill Pack 划分与职责边界

每个 skill 的 `SKILL.md` 必须包含这 6 段，且 `description` 必须同时写清：

1. what it does
2. when to use it
3. when not to use it
4. required inputs
5. required outputs
6. hard rules

## 11.1 `softcopy-intake`

- 作用：收集、核对并固化申请事实
- 触发：
  - 用户开始软著申请工作流
  - 需要从仓库生成申请材料
  - `project_facts.yaml` 不存在或关键事实未确认
- 非触发：
  - 普通代码报错解释
  - 普通 README 总结
  - 单纯代码审查
- 必写输出：
  - `softcopy/project_facts.yaml`
  - `softcopy/outputs/intake/intake_report.md`
- 硬规则：
  - 禁止把候选值直接落成关键正式事实
  - 禁止使用 Git 最后提交时间代替开发完成日期
  - 禁止默认填写 `first_publication_status = unpublished`

## 11.2 `softcopy-scan-repo`

- 作用：分析仓库，提取技术栈、入口、模块、候选路由、候选功能、候选核心文件
- 触发：
  - intake 已完成
  - 需要从仓库结构提取候选证据
- 非触发：
  - 已有明确 feature map 且无需扫描
- 必写输出：
  - `softcopy/outputs/scan/repo_scan.json`
  - `softcopy/outputs/scan/module_candidates.yaml`
  - `softcopy/outputs/scan/code_inventory.csv`
  - `softcopy/outputs/scan/route_inventory.csv`
  - `softcopy/outputs/scan/repo_scan_report.md`
- 硬规则：
  - scan 结果只能是 candidate evidence
  - 不得直接定稿关键申请事实

## 11.3 `softcopy-feature-map`

- 作用：建立功能边界，并把功能映射到代码、手册、截图、申请表描述
- 触发：
  - scan 已完成
  - 需要形成正式 feature 边界
- 非触发：
  - 只做简单申请表草稿且明确允许 provisional 模式
- 必写输出：
  - `softcopy/outputs/feature_map/feature_map.candidate.yaml`
  - `softcopy/outputs/feature_map/feature_map_report.md`
- 硬规则：
  - 常规运行不得覆盖已存在的 `softcopy/feature_map.yaml`
  - 人工确认后的候选内容才允许合并进 `softcopy/feature_map.yaml`
  - 正式阶段必须有人审通过
  - `review_status != approved` 时不得支撑 formal readiness

## 11.4 `softcopy-application`

- 作用：基于显式事实与 feature/evidence 生成申请表字段草稿与审稿清单
- 触发：
  - 已有 `project_facts.yaml`
  - 需要申请表草稿
- 非触发：
  - 产品营销介绍
  - README 总结
  - 与软著无关的材料编写
- 必写输出：
  - `softcopy/outputs/application/application_fields.json`
  - `softcopy/outputs/application/application_draft.md`
  - `softcopy/outputs/application/application_review_checklist.md`
  - `softcopy/outputs/application/application_trace.json`
- 硬规则：
  - 若关键事实未确认，只能输出 `provisional_application_draft`
  - `feature_map.yaml` 缺失时不得声称 formal
  - 关键事实字段必须来自 `confirmed` facts

## 11.5 `softcopy-code-doc`

- 作用：生成源程序鉴别材料
- 触发：
  - `feature_map.yaml` 已批准
  - 需要正式代码材料
- 非触发：
  - 只有 provisional application draft
- 必写输出：
  - `softcopy/outputs/code_doc/code_selection.yaml`
  - `softcopy/outputs/code_doc/code_doc.md`
  - `softcopy/outputs/code_doc/code_pages.json`
  - `softcopy/outputs/code_doc/code_doc_report.md`
  - `softcopy/outputs/code_doc/page_trace.json`
- 可选输出：
  - `softcopy/outputs/code_doc/code_doc.pdf`
  - `softcopy/outputs/code_doc/code_doc.docx`
- 硬规则：
  - 不优先纳入测试、第三方、生成文件、纯配置
  - 每页必须记录 `path`、`line_start`、`line_end`、`effective_line_count`、`source_ref`
  - 正式页行数规则只能由 `registration_rules.yaml` 驱动

## 11.6 `softcopy-manual`

- 作用：生成文档鉴别材料，并维护 `manual_manifest` 的半自动流程
- 触发：
  - `feature_map.yaml` 已批准
  - 需要正式文档材料
- 非触发：
  - 没有功能边界、没有截图来源的情况下直接编写正式手册
- 必写输出：
  - `softcopy/outputs/manual/manual_manifest.stub.yaml`
  - `softcopy/outputs/manual/manual_outline.md`
  - `softcopy/outputs/manual/manual.md`
  - `softcopy/outputs/manual/manual_pages.json`
  - `softcopy/outputs/manual/manual_report.md`
  - `softcopy/outputs/manual/manual_trace.json`
- 可选输出：
  - `softcopy/outputs/manual/manual.pdf`
  - `softcopy/outputs/manual/manual.docx`
- 硬规则：
  - 常规运行不得覆盖已存在的 `softcopy/manual_manifest.yaml`
  - 人工确认后的 stub 内容才允许合并进 `softcopy/manual_manifest.yaml`
  - 不得使用与真实软件无关的示意图冒充正式截图
  - `manual_manifest.yaml` 未批准时不得进入 ready-to-submit

## 11.7 `softcopy-proof-check`

- 作用：根据 `development_mode` 生成并核对证明材料清单
- 触发：
  - 需要检查权属/证明文件
- 非触发：
  - 单纯文案润色
- 必写输出：
  - `softcopy/outputs/proof_check/ownership_evidence.candidate.yaml`
  - `softcopy/outputs/proof_check/proof_checklist.md`
  - `softcopy/outputs/proof_check/missing_proofs.md`
- 硬规则：
  - 常规运行不得覆盖已存在的 `softcopy/ownership_evidence.yaml`
  - 人工确认后的候选清单才允许合并进 `softcopy/ownership_evidence.yaml`
  - 统一使用 `development_mode`
  - 不得出现 `ownership_mode`

## 11.8 `softcopy-validate`

- 作用：对材料包做事实、追溯、规则、格式、一致性校验
- 触发：
  - 已产生 application/code_doc/manual/proof_check 中的任意正式产物
- 非触发：
  - 单纯润色单个段落
- 必写输出：
  - `softcopy/outputs/validation/validation_report.md`
  - `softcopy/outputs/validation/errors.json`
  - `softcopy/outputs/validation/warnings.json`
  - `softcopy/outputs/traceability/traceability_report.md`
- 仅在通过时写：
  - `softcopy/outputs/package/READY_TO_SUBMIT.flag`
- 硬规则：
  - 关键事实不为 `confirmed` 时，禁止给出 ready-to-submit
  - 缺少 traceability 时，禁止给出 ready-to-submit
  - 未激活的规则不得直接报 `ERROR`

---

## 12. 工作流

## 12.1 从零开始

1. `softcopy-intake`
2. 生成 `project_facts.yaml`
3. `softcopy-scan-repo`
4. `softcopy-feature-map` 生成 `feature_map.candidate.yaml`
5. 人工 review 后合并到 `feature_map.yaml`
6. `softcopy-proof-check`
7. `softcopy-manual` 生成 `manual_manifest.stub.yaml`
8. 人工补齐截图路径、实际操作步骤、结果说明
9. 人工合并为正式 `manual_manifest.yaml`
10. `softcopy-application`
11. `softcopy-code-doc`
12. `softcopy-manual`
13. `softcopy-validate`
14. 仅当 validate 无 blocking error 时生成 `READY_TO_SUBMIT.flag`

## 12.2 已有部分材料时

- 已有申请表：做字段规范化、traceability 补齐、一致性校验
- 已有代码材料：做来源、页边界、规则检查
- 已有截图和手册初稿：先规范化 manifest，再生成正式 manual

## 12.3 MVP 特例

MVP 阶段允许：

- 没有 `feature_map.yaml` 时输出 `provisional_application_draft`
- 没有 PDF/DOCX 渲染器

MVP 阶段不允许：

- 没有 traceability
- 没有 `required_facts.yaml`
- 没有 `registration_rules.yaml`
- 在关键事实未确认时进入 `formal_application_ready`

---

## 13. validator 最低检查项

validator 在 MVP 就必须至少检查：

1. `required_facts.yaml` 中所有正式态必需字段是否已达到允许状态
2. 关键事实字段是否存在 `candidate` / `derived` 混入正式态
3. `software_name_full` 一致性
4. `version` 一致性
5. `development_mode` 一致性
6. `first_publication_status` 是否已确认
7. `first_publication_date` 在已发表条件下是否已确认
8. `application main functions` 是否可追溯到 feature/code/manual 证据
9. `feature_map.yaml` 在正式态是否已 `approved`
10. `manual_manifest.yaml` 在正式态是否已 `approved`
11. `ownership_evidence.yaml` 是否满足当前 `development_mode`
12. 所有 `blocking: true` 字段是否有 `sources[]`
13. `registration_rules.yaml` 中触发的 `ERROR` 规则是否具有完整来源元数据
14. 未满足上述任一项时，禁止创建 `READY_TO_SUBMIT.flag`

---

## 14. 命名冻结表

后续所有 skill、schema、JSON、YAML、validator、文档，只允许使用下列冻结字段名：

| 语义 | 唯一字段名 |
|---|---|
| 软件全称 | `software_name_full` |
| 软件简称 | `software_name_short` |
| 版本号 | `version` |
| 开发完成日期 | `development_completion_date` |
| 首次发表状态 | `first_publication_status` |
| 首次发表日期 | `first_publication_date` |
| 权利主体类型 | `copyright_owner_type` |
| 权利主体列表 | `copyright_owners` |
| 开发方式 | `development_mode` |
| 项目类型 | `project_type` |

禁止再出现：

- `ownership_mode`
- `publication_status`
- 与上述冻结字段同义但不同名的别名字段

---

## 15. AGENTS 与 SKILL 编写规则

## 15.1 `AGENTS.md`

`AGENTS.md` 只写全局稳定规则，不写单个项目的一次性内容。至少应包括：

1. 先检查 `softcopy/project_facts.yaml`
2. 未确认的关键事实不得进入正式申请材料
3. scan 结果是候选证据，不是最终法律事实
4. 正式字段必须可追溯
5. validate 未通过前不得输出 ready-to-submit
6. 文档策略按项目类型切换

## 15.2 `SKILL.md`

每个 skill 的 `SKILL.md`：

1. MUST 保持短而聚焦
2. MUST 写明 trigger 和 non-trigger
3. MUST 写明 required outputs
4. SHOULD 把长说明移动到 `references/`
5. MUST NOT 把法规细节、长篇案例、社区经验全部堆进主文件

---

## 16. 评估与测试

每个 skill 至少要有三类测试：

1. Trigger tests
2. Contract tests
3. Artifact tests

项目 MUST 提供 `python3 -m softcopy_tool evals --repo-root <repo>`，在临时目录执行内置 demo 场景，并输出 `softcopy/outputs/validation/eval_report.md` 与 `eval_report.json`。

### 16.1 Trigger tests

必须覆盖：

- 应触发
- 不应触发

示例：

- `softcopy-intake` 不应在“解释一个代码报错”时触发
- `softcopy-application` 不应在“帮我写产品介绍”时触发
- `softcopy-validate` 不应在“帮我润色申请表文案”时直接触发 package 校验

### 16.2 Contract tests

至少覆盖：

- 核心事实缺失时是否进入 provisional/block
- `first_publication_status` 未确认时是否阻断 formal readiness
- `candidate` / `derived` 关键事实混入正式态时是否报错
- traceability 缺失时是否失败
- 地方规则在 `office` 未确认时是否不会直接变成 `ERROR`

### 16.3 Artifact tests

至少覆盖：

- 输出目录是否正确
- 输出文件名是否正确
- 是否保留 unresolved placeholders
- 是否在通过前禁止生成 `READY_TO_SUBMIT.flag`

---

## 17. 分阶段实现建议

### 17.1 Phase 1：必须先做

- `softcopy-intake`
- `softcopy-scan-repo`
- `softcopy-application`
- `softcopy-validate`
- `softcopy/contracts/required_facts.yaml`
- `softcopy/contracts/traceability.schema.json`
- `softcopy/rules/registration_rules.yaml`
- `softcopy/rules/heuristics.yaml`
- `softcopy/project_facts.yaml`
- 最小 traceability
- 最小 evals

### 17.2 Phase 2：高价值

- `softcopy-feature-map`
- `softcopy-proof-check`
- `softcopy-manual`
- `softcopy-code-doc`
- `manual_manifest.stub.yaml` 流程
- `feature_map.yaml` 审批流

### 17.3 Phase 3：成熟化

- optional PDF / DOCX 渲染器，默认 Markdown/JSON 零依赖
- 源码与手册分页规则机器校验
- `evals` runner 覆盖 trigger、contract、artifact 场景
- 更强的社区 heuristics 库
- 更细粒度的 code-doc/manual traceability

---

## 18. 禁止事项

1. 禁止把所有功能塞进一个巨型 skill
2. 禁止让模型自动决定关键权属字段
3. 禁止把 README 最后修改时间当开发完成日期
4. 禁止把仓库名直接当软件正式名称
5. 禁止把 `first_publication_status` 默认成 `unpublished`
6. 禁止在正式态接受 `candidate` / `derived` 的关键事实
7. 禁止让未激活或法源不全的规则直接报 `ERROR`
8. 禁止把地方办事规则默认套用到全部项目
9. 禁止只产 PDF、不产结构化中间文件
10. 禁止输出 ready-to-submit 而没有完整 validator 结论

---

## 19. 成功标准

只有同时满足以下条件，才视为设计成功：

1. 关键事实缺失时，系统能稳定阻断正式态而不是自动编造
2. `first_publication_status` 未确认时，不会被静默写成 `unpublished`
3. `candidate` / `derived` 关键事实不会漏进正式申请表
4. 所有正式字段都能被 traceability 报告回溯
5. 全国规则与地方规则的适用范围可审计、可切换
6. `READY_TO_SUBMIT.flag` 只会在完整通过校验时生成
7. coding、文案、skill intro、evals 都围绕同一套术语和状态工作

---

## 20. 实施切换规则

从本文档生效起：

1. 新实现 MUST 只引用本文档
2. 历史两份文档只保留“已废弃”说明，不再承载规范内容
3. 新增或修改 contracts/rules/schemas 前，应先检查是否与本文档一致
4. 若后续再做 review，默认审阅对象为本文档及其派生 contracts/rules/schemas
