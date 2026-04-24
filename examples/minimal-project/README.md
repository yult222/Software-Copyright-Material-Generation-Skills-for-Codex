# Minimal SoftCopy Demo Project

这是一个用于演示 SoftCopy workflow 的最小项目。它故意不携带 `softcopy/` 目录；先运行 `init`，再运行 `run-all`。

```bash
python3 -m softcopy_tool init --target examples/minimal-project
python3 -m softcopy_tool run-all --repo-root examples/minimal-project
```

需要模拟“事实已确认并已审核”的 ready 状态时，可以把以下文件复制到 `softcopy/`：

- `docs/project_facts.confirmed.example.yaml`
- `docs/feature_map.approved.example.yaml`
- `docs/manual_manifest.approved.example.yaml`
- `docs/ownership_evidence.approved.example.yaml`

`docs/proofs/owner_identity.txt` 是 demo-only 证明文件占位，不是真实身份证明。
