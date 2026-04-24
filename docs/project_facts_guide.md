# project_facts.yaml 填写指南

`softcopy/project_facts.yaml` 是正式材料的事实来源。核心原则：关键事实必须人工确认，不能从 README、Git 历史、仓库名或模型推断直接升格。

## 必须确认的字段

- `software_name_full`：软件全称
- `version`：版本号
- `development_completion_date`：开发完成日期
- `first_publication_status`：首次发表状态，必须人工确认，不能默认 `unpublished`
- `copyright_owner_type`：著作权人类型
- `copyright_owners`：著作权人列表
- `development_mode`：开发方式
- `project_type`：项目类型

## 字段状态

- `confirmed`：已人工确认，可进入正式材料
- `candidate`：候选证据，不可作为关键事实进入正式材料
- `derived`：推导结果，不可作为关键法律事实
- `needs_confirmation`：待确认
- `missing`：缺失
- `not_applicable`：确认后不适用

## 首次发表状态

`first_publication_status` 初始化时必须保持：

```yaml
value: ""
status: needs_confirmation
```

只有人工确认后，才能写成 `published` 或 `unpublished`。当它被确认为 `published` 时，`first_publication_date` 也必须是 `confirmed`。

当它被确认为 `unpublished` 时，`first_publication_date` 应写成：

```yaml
value: ""
status: not_applicable
```

但仍需保留明确的 `sources`，说明“不适用”来自人工确认，而不是工具默认。

## 来源写法

blocking 字段进入正式材料前，必须至少有一个 source：

```yaml
sources:
  - source_type: explicit_fact
    source_ref: softcopy/project_facts.yaml#/facts/version
    authority_level: B
    confidence: 1.0
```
