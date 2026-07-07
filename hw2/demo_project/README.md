# notes_app — 一个玩具笔记本 CLI（教学靶子项目）

> 这是给 Day2 用的**练习靶子**:c0–c5 的"复杂例子"和作业,都在这个小项目上跑。
> 它长得像一个真实的小项目(多个文件、有 README、有 TODO、有一个藏起来的 bug)。

## 是什么

一个命令行小工具,把笔记存进 `data/notes.json`,支持增/查/删/统计。

## 怎么跑

```bash
cd demo_project
python -m notes_app.cli add "买牛奶"
python -m notes_app.cli add "读论文 #research"
python -m notes_app.cli list
python -m notes_app.cli find research
python -m notes_app.cli stats
```

## 文件结构

```
demo_project/
├── README.md          # 你正在看的
├── TODO.md            # 几条待办(c2 计划 / 作业会用)
├── notes_app/
│   ├── __init__.py
│   ├── cli.py         # 命令行入口:解析参数、分发
│   ├── store.py       # 读写 data/notes.json
│   └── analyze.py     # 统计功能(⚠ 这里藏着一个 bug)
├── data/
│   └── notes.json     # 笔记数据(玩具数据,无隐私)
└── logs/
    ├── 2026-07-04.log
    └── 2026-07-05.log
```

## 已知问题

`stats` 命令在**没有任何带标签的笔记**时会出错。第一个用 mini Claude Code 找到并修好它的人,请举手。🐛

---
*纯玩具数据,无真实隐私。MIT License｜郑先隽,北师大心理学部*
