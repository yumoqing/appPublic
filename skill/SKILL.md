---
name: apppublic-repo
version: 1.0.0
description: appPublic
trigger_conditions:
  - 需要理解、修改或排障 appPublic 的代码
  - 在 appPublic 里定位入口、数据表、对外契约或构建方式
---

# appPublic 仓库技能

> 由仓库实际内容生成的骨架（README/目录/模型定义/契约/构建脚本逐项取证）。新增判断与坑位请直接在下面对应小节补充。

## 定位

**appPublic**

a set of icommon modules for python development 生产级异步事件调度器。

- 远端：`https://github.com/yumoqing/appPublic.git`
- 默认分支：`main`（共 98 个提交）
- 最近提交：2026-11-03 `7290b21` chore: 忽略 init/logs 等生成物
- 规模：202 个文件；Python 104，JSON 1

## 目录结构

- `appPublic/` — Python 包源码（模块本体）（94 个文件）
- `aidocs/` — AI/开发文档（86 个文件）
- `test/` — 测试（17 个文件）
- `doc/` — 文档（1 个文件）
- 根文件：`.gitignore`、`README.md`、`pyproject.toml`、`setup.cfg`

## 构建与运行

- `pyproject.toml`：`?` v?，依赖 0 项
- Python 包 `appPublic/`：`CSVData.py`、`ExecFile.py`、`FiniteStateMachine.py`、`MiniI18N.py`、`ObjectCache.py`、`RSAutils.py`、`SQLite3Utils.py`、`Singleton.py`

## README 要点与注意（摘自 `README.md`）

- 章节：EventDispatcher

## 建议阅读顺序

1. `README.md`
2. `aidocs/`

