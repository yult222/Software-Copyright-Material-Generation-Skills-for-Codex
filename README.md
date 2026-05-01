# SoftCopy Codex Skill Pack

SoftCopy Codex Skill Pack 是一套面向 Codex 的软件著作权材料生成与校验工作流。它不是“自动编造软著材料”的大 prompt，而是 `Skill + CLI + YAML 事实源 + readiness gate`：先确认事实，再扫描代码，再生成候选材料，最后用可追溯规则阻断不可信输出。

English: SoftCopy is a Codex-first skill pack with a portable Python CLI for preparing reviewable software copyright application materials from an existing repository.

## 适合谁

- 需要从已完成、可运行的软件仓库整理软著申请材料的人
- 想把 Codex skills 迁移到多个项目里的工程团队
- 想保留 facts、feature map、manual manifest、proof checklist、traceability 和 validation 报告的使用者

## 不承诺什么

- 不自动提交登记平台
- 不替你确认著作权人、开发方式、完成日期、首次发表状态等法律事实
- 不把 README、Git 时间、仓库名或 commit author 当作正式申请事实
- 不在 validator 未通过时输出 `READY_TO_SUBMIT.flag`

## 工作流总览

当前代码中的完整顺序是：

```text
init -> scan -> intake -> feature-map -> proof-check -> manual -> application -> code-doc -> validate
```

其中 `run-all` 会自动执行：

```text
scan -> intake -> feature-map -> proof-check -> manual -> application -> code-doc -> validate
```

`init` 只用于把 SoftCopy 能力迁移到目标仓库；迁移完成后，后续命令都围绕目标仓库的 `softcopy/` 目录运行。

## 安装

前置条件：Python 3.10+。

```bash
git clone https://github.com/yult222/Software-Copyright-Material-Generation-Skills-for-Codex.git
cd Software-Copyright-Material-Generation-Skills-for-Codex
python3 -m pip install -e .
```

安装后可以使用 console script：

```bash
softcopy-tool --version
```

本文后续示例统一使用模块入口，确保在源码 checkout 中也可以直接运行：

```bash
python3 -m softcopy_tool --version
```

## Quickstart

先初始化示例项目并跑一次默认流程：

```bash
python3 -m softcopy_tool init --target examples/minimal-project
python3 -m softcopy_tool run-all --repo-root examples/minimal-project --formats md
sed -n '1,180p' examples/minimal-project/softcopy/outputs/validation/validation_report.md
```

第一次运行通常会失败，这是预期行为。默认 `project_facts.yaml` 的关键事实仍是 `needs_confirmation`，`feature_map.yaml`、`manual_manifest.yaml` 和 `ownership_evidence.yaml` 也还没有进入人工批准状态，所以 validator 会阻断正式提交态。

## 跑通 Approved Demo

示例项目提供一组已确认/已审核 fixtures。它们只用于演示完整工作流，不代表真实申请事实。

```bash
cp examples/minimal-project/docs/project_facts.confirmed.example.yaml examples/minimal-project/softcopy/project_facts.yaml
cp examples/minimal-project/docs/feature_map.approved.example.yaml examples/minimal-project/softcopy/feature_map.yaml
cp examples/minimal-project/docs/manual_manifest.approved.example.yaml examples/minimal-project/softcopy/manual_manifest.yaml
cp examples/minimal-project/docs/ownership_evidence.approved.example.yaml examples/minimal-project/softcopy/ownership_evidence.yaml

python3 -m softcopy_tool run-all --repo-root examples/minimal-project --formats md
test -f examples/minimal-project/softcopy/outputs/package/READY_TO_SUBMIT.flag
```

## 真实项目完整流程

下面是一套按当前代码行为整理出的真实项目落地流程。

### 1. 迁移 SoftCopy 到目标仓库

```bash
python3 -m softcopy_tool init --target /path/to/your/repo
```

`init` 会复制：

- `.agents/AGENTS.md`
- `.agents/skills/`
- `softcopy_tool/`
- `softcopy_support.py`
- `softcopy/contracts/`
- `softcopy/rules/`
- `softcopy/schemas/`
- `softcopy/project_facts.yaml`
- `softcopy/feature_map.yaml`
- `softcopy/manual_manifest.yaml`
- `softcopy/ownership_evidence.yaml`
- `docs/softcopy_project_facts_guide.md`

它默认不覆盖已有文件；冲突会写入：

```text
softcopy/outputs/intake/init_report.md
softcopy/outputs/intake/init_report.json
```

### 2. 扫描仓库

```bash
python3 -m softcopy_tool scan --repo-root /path/to/your/repo
```

`scan` 会读取目标仓库源码，排除 `.git`、`.agents`、`softcopy_tool`、`softcopy`、`evals`、`node_modules`、`dist`、`build`、虚拟环境等目录，然后生成：

```text
softcopy/outputs/scan/repo_scan.json
softcopy/outputs/scan/repo_scan_report.md
softcopy/outputs/scan/code_inventory.csv
softcopy/outputs/scan/route_inventory.csv
softcopy/outputs/scan/module_candidates.yaml
```

这些结果只是候选证据，不能直接替代人工确认的申请事实。

### 3. 补齐并确认核心事实

编辑：

```text
softcopy/project_facts.yaml
```

必须人工确认的核心字段包括：

- `software_name_full`
- `version`
- `development_completion_date`
- `first_publication_status`
- `copyright_owner_type`
- `copyright_owners`
- `development_mode`
- `project_type`

如果 `first_publication_status` 被确认为 `published`，还必须确认 `first_publication_date`。字段状态说明见 [docs/project_facts_guide.md](docs/project_facts_guide.md)。

随后运行 intake 报告：

```bash
python3 -m softcopy_tool intake --repo-root /path/to/your/repo
```

产物：

```text
softcopy/outputs/intake/intake_report.md
```

### 4. 生成功能候选并人工批准 Feature Map

```bash
python3 -m softcopy_tool feature-map --repo-root /path/to/your/repo
```

产物：

```text
softcopy/outputs/feature_map/feature_map.candidate.yaml
softcopy/outputs/feature_map/feature_map_report.md
```

你需要人工 review `feature_map.candidate.yaml`，把确认后的功能边界、源码路径、命令/路由、手册章节和申请表 claims 合并到：

```text
softcopy/feature_map.yaml
```

进入 ready gate 前，顶层状态必须是：

```yaml
review_status: approved
```

并且 `features` 不能为空。

### 5. 生成权属证明清单并人工批准

```bash
python3 -m softcopy_tool proof-check --repo-root /path/to/your/repo
```

产物：

```text
softcopy/outputs/proof_check/ownership_evidence.candidate.yaml
softcopy/outputs/proof_check/proof_checklist.md
softcopy/outputs/proof_check/missing_proofs.md
```

工具会根据 `project_facts.yaml` 中的 `development_mode` 生成候选证明清单。你需要把真实的证明文件状态写入：

```text
softcopy/ownership_evidence.yaml
```

进入 ready gate 前必须满足：

```yaml
evidence_status: approved
```

所有必需证明项都需要：

```yaml
provided: true
file_ref: path/or/external/ref
```

如果 `file_ref` 不是 `http://`、`https://` 或 `app://` 外部引用，validator 会检查该文件是否真实存在。

### 6. 生成手册 manifest 并人工批准

```bash
python3 -m softcopy_tool manual --repo-root /path/to/your/repo --formats md
```

产物：

```text
softcopy/outputs/manual/manual_manifest.stub.yaml
softcopy/outputs/manual/manual_outline.md
softcopy/outputs/manual/manual.md
softcopy/outputs/manual/manual_pages.json
softcopy/outputs/manual/manual_trace.json
softcopy/outputs/manual/manual_report.md
```

`manual` 会根据 feature map 生成 stub，但不会覆盖已经维护的 canonical manifest。你需要把真实章节、步骤、截图引用和预期结果整理到：

```text
softcopy/manual_manifest.yaml
```

进入 ready gate 前必须满足：

```yaml
manifest_status: approved
```

并且 `sections` 不能为空。

### 7. 生成申请表草稿

```bash
python3 -m softcopy_tool application --repo-root /path/to/your/repo
```

产物：

```text
softcopy/outputs/application/application_fields.json
softcopy/outputs/application/application_trace.json
softcopy/outputs/application/application_draft.md
softcopy/outputs/application/application_review_checklist.md
```

`application` 会根据 `project_facts.yaml`、`required_facts.yaml`、`feature_map.yaml` 和扫描结果生成草稿。当前代码会区分两种模式：

- `provisional`：核心事实未确认，或 feature map 未批准
- `formal`：formal gate 所需事实已满足，且 feature map 已批准

即使生成了 `formal` 草稿，也不代表已经 ready-to-submit；最终仍以 `validate` 结果为准。

### 8. 生成源码材料

```bash
python3 -m softcopy_tool code-doc --repo-root /path/to/your/repo --formats md
```

产物：

```text
softcopy/outputs/code_doc/code_selection.yaml
softcopy/outputs/code_doc/code_doc.md
softcopy/outputs/code_doc/code_pages.json
softcopy/outputs/code_doc/page_trace.json
softcopy/outputs/code_doc/code_doc_report.md
```

`code-doc` 会从 `scan` 生成的 `candidate_core_files` 中选取核心文件，按每页 50 条有效代码行分页。如果总页数超过 60 页，则选择前 30 页和后 30 页。

### 9. 校验并生成提交状态

```bash
python3 -m softcopy_tool validate --repo-root /path/to/your/repo
```

产物：

```text
softcopy/outputs/validation/errors.json
softcopy/outputs/validation/warnings.json
softcopy/outputs/validation/validation_report.md
softcopy/outputs/traceability/traceability_report.md
```

只有所有 hard gate 通过时，才会生成：

```text
softcopy/outputs/package/READY_TO_SUBMIT.flag
```

如果校验失败，`READY_TO_SUBMIT.flag` 会被删除。

## 一键重跑

当 `project_facts.yaml`、`feature_map.yaml`、`manual_manifest.yaml` 和 `ownership_evidence.yaml` 已经人工维护好以后，可以使用：

```bash
python3 -m softcopy_tool run-all --repo-root /path/to/your/repo --formats md
```

`run-all` 会重建扫描、候选报告、申请草稿、手册、源码材料和校验报告。它适合在每轮人工修改 YAML 后重跑，但仍不会替你批准事实或证明材料。

## Readiness Gate

`validate` 当前检查的核心条件包括：

- 核心事实必须达到 `ready_to_submit` gate 接受的状态，默认是 `confirmed`
- `published` 场景下必须确认 `first_publication_date`
- blocking 字段必须有 `sources`
- `feature_map.yaml` 必须 `review_status: approved`
- `feature_map.yaml` 的 `features` 不能为空
- `manual_manifest.yaml` 必须 `manifest_status: approved`
- `manual_manifest.yaml` 的 `sections` 不能为空
- `ownership_evidence.yaml` 必须 `evidence_status: approved`
- 必需权属证明必须 `provided: true` 且有有效 `file_ref`
- 申请表字段必须和 `project_facts.yaml` 一致
- 正式申请的 main functions 不能只依赖 scan candidate
- active page rules 必须有完整 provenance
- 源码材料和手册材料必须满足 active page rules

默认内置的中国软件著作权页规则包括：

- 源码材料前 30 页和后 30 页；不足 60 页则全部提交
- 源码材料每页不少于 50 条有效代码行
- 文档材料前 30 页和后 30 页；不足 60 页则全部提交
- 文档材料每页不少于 30 条有效文本行
- A4 纸规则会作为 rendered/printed review 信息提示，不做机器硬校验

## 中文正式材料口径

面向申请人和提交审查的正式材料默认使用中文，包括：

- `softcopy/outputs/application/application_draft.md`：软件著作权登记申请表草稿
- `softcopy/outputs/code_doc/code_doc.md|pdf|docx`：源程序鉴别材料
- `softcopy/outputs/manual/manual.md|pdf|docx`：用户手册、接口说明文档或命令行使用说明

内部机器文件仍保留英文 key，例如 `application_fields.json`、`code_pages.json`、`manual_pages.json` 和 trace JSON，以保持 validator、schema 和 evals 稳定。源码正文保持原文，不翻译变量名、函数名、字符串或注释。

## 可选 PDF/DOCX 渲染

默认只生成 Markdown/JSON/CSV/YAML。需要 PDF/DOCX 时安装可选依赖：

```bash
python3 -m pip install '.[render]'
python3 -m softcopy_tool code-doc --repo-root /path/to/your/repo --formats md,pdf,docx
python3 -m softcopy_tool manual --repo-root /path/to/your/repo --formats md,pdf,docx
```

未安装 extras 时，默认 `--formats md` 正常运行；显式请求 `pdf` 或 `docx` 会给出依赖安装提示并失败。

DOCX 使用 A4 纵向、约 2.5cm 页边距、中文正文宋体、标题黑体、源码等宽字体、页眉显示软件名称与版本号、页脚页码。字体、字号和行距属于保守行业常用版式，不声明为官方强制格式；官方 hard gate 仍以页数、行数、事实确认和追溯校验为准。

PDF 渲染会优先使用 ReportLab 内置中文 CID 字体。也可以通过环境变量指定字体：

```bash
SOFTCOPY_CJK_FONT=/path/to/font.ttf python3 -m softcopy_tool manual --repo-root /path/to/your/repo --formats md,pdf
```

## 输出目录索引

```text
softcopy/outputs/intake/       init 与事实 intake 报告
softcopy/outputs/scan/         仓库扫描、代码清单、路由清单、模块候选
softcopy/outputs/feature_map/  功能候选与 feature map 报告
softcopy/outputs/proof_check/  权属证明候选清单
softcopy/outputs/manual/       手册草稿、分页、trace
softcopy/outputs/application/  申请表字段、草稿、trace、review checklist
softcopy/outputs/code_doc/     源码材料、分页、trace
softcopy/outputs/validation/   错误、警告、校验报告、eval 报告
softcopy/outputs/traceability/ 可追溯报告
softcopy/outputs/package/      READY_TO_SUBMIT.flag
```

## CLI 命令

```text
python3 -m softcopy_tool init --target <repo>
python3 -m softcopy_tool scan --repo-root <repo>
python3 -m softcopy_tool intake --repo-root <repo>
python3 -m softcopy_tool feature-map --repo-root <repo>
python3 -m softcopy_tool proof-check --repo-root <repo>
python3 -m softcopy_tool manual --repo-root <repo> --formats md,pdf,docx
python3 -m softcopy_tool application --repo-root <repo>
python3 -m softcopy_tool code-doc --repo-root <repo> --formats md,pdf,docx
python3 -m softcopy_tool validate --repo-root <repo>
python3 -m softcopy_tool run-all --repo-root <repo> --formats md
python3 -m softcopy_tool evals --repo-root <repo>
python3 -m softcopy_tool clean --repo-root <repo>
```

安装后的 console script 等价入口：

```text
softcopy-tool <command> ...
```

## 测试与内置 Evals

运行单元测试：

```bash
python3 -m unittest discover -s tests -q
```

运行 SoftCopy 内置 evals：

```bash
python3 -m softcopy_tool evals --repo-root .
sed -n '1,200p' softcopy/outputs/validation/eval_report.md
```

当前 evals 覆盖：

- 默认事实未确认时必须失败
- approved demo 必须生成 ready flag
- 核心事实状态不满足时必须阻断
- 已发表场景必须要求首次发表日期
- formal gate 与 ready gate 可使用不同 accepted statuses
- active rule provenance 不完整时降级为 warning
- manual manifest 未批准时必须阻断

## 常见错误处理

常见错误不是工具故障，而是事实或人工 review 没有进入可提交状态：

- `core_required_fact_not_confirmed`：关键事实仍不是 ready gate 接受的状态
- `conditional_required_fact_not_confirmed`：条件字段触发后没有确认，例如已发表但未确认首次发表日期
- `traceability_missing_source`：blocking 字段没有 `sources`
- `main_function_not_traceable`：申请表主要功能缺少证据来源
- `feature_map_not_approved_for_readiness`：功能映射尚未人工批准
- `feature_map_empty_for_readiness`：功能映射为空
- `manual_manifest_not_approved_for_readiness`：手册 manifest 尚未人工批准
- `manual_manifest_empty_for_readiness`：手册章节为空
- `ownership_evidence_not_approved_for_readiness`：权属证明清单尚未批准
- `required_ownership_document_missing`：必需证明未标记为已提供
- `required_ownership_document_file_ref_missing`：必需证明缺少文件引用
- `required_ownership_document_file_not_found`：本地证明文件不存在
- `rule_provenance_incomplete`：active 规则缺少可审计来源，不能作为 hard rule 生效
- `code_doc_pages_missing` / `manual_doc_pages_missing`：未生成分页材料
- `code_doc_page_too_short` / `manual_doc_page_too_short`：分页材料没有满足 active page rule

推荐修复顺序：

```text
project_facts.yaml
-> feature_map.yaml
-> ownership_evidence.yaml
-> manual_manifest.yaml
-> application/manual/code-doc
-> validate
```

## 清理输出

```bash
python3 -m softcopy_tool clean --repo-root /path/to/your/repo
```

`clean` 会清理 `softcopy/outputs/` 下的生成物，并保留 `.gitkeep`。

## English Summary

SoftCopy provides a portable Codex skill pack and Python CLI. The workflow is:

```text
init -> scan -> intake -> feature-map -> proof-check -> manual -> application -> code-doc -> validate
```

Formal readiness requires confirmed core facts, approved feature/manual/proof evidence, traceable blocking fields, active page rules with complete provenance, and generated code/manual page traces.

## License

MIT. See [LICENSE](LICENSE).
