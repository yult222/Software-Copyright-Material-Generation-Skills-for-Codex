# SoftCopy Codex Skill Pack

SoftCopy Codex Skill Pack 是一套面向 Codex 的软件著作权材料生成与校验工具。它不是“自动编造软著材料”的大 prompt，而是一套 `Skill + CLI` 工作流：先确认事实，再扫描仓库，再生成草稿，最后用可追溯规则阻断不可信输出。

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

## Quickstart

前置条件：Python 3.10+，以及系统 Ruby（用于安全解析 YAML，避免引入 PyYAML 依赖）。

```bash
git clone https://github.com/yult222/Software-Copyright-Material-Generation-Skills-for-Codex.git
cd Software-Copyright-Material-Generation-Skills-for-Codex

python3 -m softcopy_tool init --target examples/minimal-project
python3 -m softcopy_tool run-all --repo-root examples/minimal-project
sed -n '1,160p' examples/minimal-project/softcopy/outputs/validation/validation_report.md
```

第一次运行通常会失败，这是预期行为。默认 `project_facts.yaml` 的关键事实仍是 `needs_confirmation`，validator 会阻断正式提交态。

## 跑通 Approved Demo

示例项目提供一组已确认/已审核 fixtures。它们只用于演示，不代表真实申请事实。

```bash
cp examples/minimal-project/docs/project_facts.confirmed.example.yaml examples/minimal-project/softcopy/project_facts.yaml
cp examples/minimal-project/docs/feature_map.approved.example.yaml examples/minimal-project/softcopy/feature_map.yaml
cp examples/minimal-project/docs/manual_manifest.approved.example.yaml examples/minimal-project/softcopy/manual_manifest.yaml
cp examples/minimal-project/docs/ownership_evidence.approved.example.yaml examples/minimal-project/softcopy/ownership_evidence.yaml

python3 -m softcopy_tool run-all --repo-root examples/minimal-project --formats md
test -f examples/minimal-project/softcopy/outputs/package/READY_TO_SUBMIT.flag
```

## 真实项目接入流程

1. 初始化 skill pack：

```bash
python3 -m softcopy_tool init --target /path/to/your/repo
```

2. 补齐事实：

编辑 `/path/to/your/repo/softcopy/project_facts.yaml`。必须人工确认的字段包括 `software_name_full`、`version`、`development_completion_date`、`first_publication_status`、`copyright_owner_type`、`copyright_owners`、`development_mode`、`project_type`。填写说明见 [docs/project_facts_guide.md](docs/project_facts_guide.md)。

3. 扫描、提取候选功能、人工 review：

```bash
python3 -m softcopy_tool scan --repo-root /path/to/your/repo
python3 -m softcopy_tool feature-map --repo-root /path/to/your/repo
```

检查 `softcopy/outputs/feature_map/feature_map.candidate.yaml`，把确认后的功能边界、源码路径、手册章节和申请表 claims 合并到 `softcopy/feature_map.yaml`，并设置 `review_status: approved`。

4. 生成证明清单、手册草稿、申请表、源码材料：

```bash
python3 -m softcopy_tool proof-check --repo-root /path/to/your/repo
python3 -m softcopy_tool manual --repo-root /path/to/your/repo --formats md
python3 -m softcopy_tool application --repo-root /path/to/your/repo
python3 -m softcopy_tool code-doc --repo-root /path/to/your/repo --formats md
```

`proof-check` 和 `manual` 会先生成 candidate/stub 文件，不覆盖已人工维护的 `ownership_evidence.yaml` 和 `manual_manifest.yaml`。把确认后的权属证明清单、手册章节、截图引用合并到 canonical YAML，并设置 `approved` 后再校验。

5. 校验：

```bash
python3 -m softcopy_tool validate --repo-root /path/to/your/repo
```

只有 facts、feature map、manual manifest、ownership evidence、traceability 和 active page rules 全部通过，才会生成 `softcopy/outputs/package/READY_TO_SUBMIT.flag`。

## 可选 PDF/DOCX 渲染

默认只生成 Markdown/JSON，保持零外部 Python 依赖。需要 PDF/DOCX 时安装可选依赖：

```bash
python3 -m pip install '.[render]'
python3 -m softcopy_tool code-doc --repo-root /path/to/your/repo --formats md,pdf,docx
python3 -m softcopy_tool manual --repo-root /path/to/your/repo --formats md,pdf,docx
```

未安装 extras 时，默认 `--formats md` 正常运行；显式请求 `pdf` 或 `docx` 会给出依赖安装提示并失败。

## CLI 命令

```text
python3 -m softcopy_tool init --target <repo>
python3 -m softcopy_tool intake --repo-root <repo>
python3 -m softcopy_tool scan --repo-root <repo>
python3 -m softcopy_tool feature-map --repo-root <repo>
python3 -m softcopy_tool proof-check --repo-root <repo>
python3 -m softcopy_tool application --repo-root <repo>
python3 -m softcopy_tool code-doc --repo-root <repo> --formats md,pdf,docx
python3 -m softcopy_tool manual --repo-root <repo> --formats md,pdf,docx
python3 -m softcopy_tool validate --repo-root <repo>
python3 -m softcopy_tool run-all --repo-root <repo> --formats md
python3 -m softcopy_tool evals --repo-root <repo>
python3 -m softcopy_tool clean --repo-root <repo>
```

## 错误处理

常见错误不是工具故障，而是事实或人工 review 没有进入可提交状态：

- `core_required_fact_not_confirmed`：关键事实仍不是 `confirmed`
- `feature_map_not_approved_for_readiness`：功能映射尚未人工批准
- `manual_manifest_not_approved_for_readiness`：手册 manifest 尚未人工批准
- `ownership_evidence_not_approved_for_readiness`：权属证明清单尚未批准
- `traceability_missing_source`：blocking 字段没有 `sources`
- `rule_provenance_incomplete`：硬规则缺少可审计来源，不能作为 `ERROR` 生效
- `code_doc_page_too_short` / `manual_doc_page_too_short`：分页材料没有满足 active page rule

修复顺序通常是：先补 `project_facts.yaml`，再 review `feature_map.yaml`、`manual_manifest.yaml`、`ownership_evidence.yaml`，再重新运行 `application`、`manual`、`code-doc` 和 `validate`。

## 迁移到其他仓库

`init` 会复制 `.agents/`、`softcopy_tool/`、`softcopy/contracts/`、`softcopy/rules/`、`softcopy/schemas/`、模板 facts、`.gitignore` 和 facts 填写指南。它默认不覆盖已有文件；冲突会写入 `softcopy/outputs/intake/init_report.md`。

## English Summary

SoftCopy provides a portable Codex skill pack and a Python CLI. The workflow is:

```text
init -> scan -> intake -> feature-map -> proof-check -> manual -> application -> code-doc -> validate
```

Formal readiness requires confirmed core facts, approved feature/manual/proof evidence, traceable blocking fields, active page rules with complete provenance, and generated code/manual page traces.

## License

MIT. See [LICENSE](LICENSE).
