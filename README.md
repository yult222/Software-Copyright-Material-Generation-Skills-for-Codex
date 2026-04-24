# SoftCopy Codex Skill Pack

SoftCopy Codex Skill Pack 是一套面向 Codex 的软件著作权材料生成与校验工具。它不是“自动编造软著材料”的大 prompt，而是一套 `Skill + CLI` 工作流：先确认事实，再扫描仓库，再生成草稿，最后用可追溯规则阻断不可信输出。

English: SoftCopy Codex Skill Pack is a Codex-first skill pack with a zero-dependency Python CLI for preparing reviewable software copyright application materials from an existing repository.

## 适合谁

- 需要从已完成、可运行的软件仓库整理软著申请材料的人
- 想把 Codex skills 迁移到多个项目里的工程团队
- 想保留结构化 facts、traceability 和 validation 报告，而不是只拿一份不可追溯 PDF 的使用者

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

第一次运行通常会失败，这是预期行为。默认 `project_facts.yaml` 里的关键事实仍是 `needs_confirmation`，validator 会阻断正式提交态。

## 真实项目接入流程

1. 初始化 skill pack：

```bash
python3 -m softcopy_tool init --target /path/to/your/repo
```

2. 补齐事实：

编辑 `/path/to/your/repo/softcopy/project_facts.yaml`。必须人工确认的字段包括 `software_name_full`、`version`、`development_completion_date`、`first_publication_status`、`copyright_owner_type`、`copyright_owners`、`development_mode`、`project_type`。填写说明见 [docs/project_facts_guide.md](docs/project_facts_guide.md)。

3. 扫描仓库：

```bash
python3 -m softcopy_tool scan --repo-root /path/to/your/repo
```

4. 生成功能映射并人工 review：

```bash
python3 -m softcopy_tool feature-map --repo-root /path/to/your/repo
```

检查 `/path/to/your/repo/softcopy/outputs/feature_map/feature_map.candidate.yaml`，把确认后的 feature 边界、源码路径、手册章节和申请表 claims 合并到 `/path/to/your/repo/softcopy/feature_map.yaml`。

5. 生成草稿材料：

```bash
python3 -m softcopy_tool proof-check --repo-root /path/to/your/repo
python3 -m softcopy_tool application --repo-root /path/to/your/repo
python3 -m softcopy_tool code-doc --repo-root /path/to/your/repo
python3 -m softcopy_tool manual --repo-root /path/to/your/repo
```

`proof-check` 和 `manual` 会先生成 candidate/stub 文件，不会覆盖你已经人工维护的 `ownership_evidence.yaml` 和 `manual_manifest.yaml`。把确认后的权属证明清单、手册章节、截图引用合并到 canonical YAML 后再进入正式校验。

6. 校验：

```bash
python3 -m softcopy_tool validate --repo-root /path/to/your/repo
```

查看 `softcopy/outputs/validation/validation_report.md`。只有没有 blocking error 时，工具才会生成 `softcopy/outputs/package/READY_TO_SUBMIT.flag`。

## CLI 命令

```text
python3 -m softcopy_tool init --target <repo>
python3 -m softcopy_tool intake --repo-root <repo>
python3 -m softcopy_tool scan --repo-root <repo>
python3 -m softcopy_tool feature-map --repo-root <repo>
python3 -m softcopy_tool proof-check --repo-root <repo>
python3 -m softcopy_tool application --repo-root <repo>
python3 -m softcopy_tool code-doc --repo-root <repo>
python3 -m softcopy_tool manual --repo-root <repo>
python3 -m softcopy_tool validate --repo-root <repo>
python3 -m softcopy_tool run-all --repo-root <repo>
python3 -m softcopy_tool clean --repo-root <repo>
```

## 关键文件

- `softcopy/project_facts.yaml`：人工确认的申请事实
- `softcopy/feature_map.yaml`：功能、代码、手册、截图、申请表 claims 的映射
- `softcopy/manual_manifest.yaml`：手册章节和截图清单
- `softcopy/ownership_evidence.yaml`：权属证明材料清单
- `softcopy/contracts/required_facts.yaml`：正式态事实准入契约
- `softcopy/rules/registration_rules.yaml`：可审计的规则来源和阈值
- `softcopy/outputs/**`：运行生成物，默认被 `.gitignore` 忽略

## 错误处理

常见错误不是工具故障，而是事实没有进入可提交状态：

- `core_required_fact_not_confirmed`：关键事实仍不是 `confirmed`
- `traceability_missing_source`：blocking 字段没有 `sources`
- `main_function_candidate_only`：申请表功能仍依赖候选证据
- `rule_provenance_incomplete`：硬规则缺少可审计来源，不能作为 `ERROR` 生效

修复顺序通常是：先补 `project_facts.yaml`，再 review `feature_map.yaml`，再补 traceability，最后重新运行 `application` 和 `validate`。

## 迁移到其他仓库

`init` 会复制 `.agents/`、`softcopy_tool/`、`softcopy/contracts/`、`softcopy/rules/`、`softcopy/schemas/`、模板 facts、`.gitignore` 和 facts 填写指南。它默认不覆盖已有文件；冲突会写入 `softcopy/outputs/intake/init_report.md`。

## English Summary

SoftCopy provides a portable Codex skill pack and a zero-dependency Python CLI. The workflow is:

```text
init -> scan -> intake -> feature-map -> proof-check -> manual -> application -> code-doc -> validate
```

The tool treats repository findings as candidate evidence. Formal readiness requires confirmed core facts, traceable blocking fields, approved feature/manual evidence, and active rules with reproducible provenance metadata.

## License

MIT. See [LICENSE](LICENSE).
