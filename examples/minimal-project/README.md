# Minimal SoftCopy Demo Project

这是一个用于演示 SoftCopy workflow 的最小项目。它故意不携带 `softcopy/` 目录；先运行 `init`，再运行 `run-all`。

```bash
python3 -m softcopy_tool init --target examples/minimal-project
python3 -m softcopy_tool run-all --repo-root examples/minimal-project
```

需要模拟“事实已确认”的状态时，可以参考 `docs/project_facts.confirmed.example.yaml` 手动替换 `softcopy/project_facts.yaml`。
