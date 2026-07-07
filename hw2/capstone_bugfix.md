# Capstone 加分题：修复 demo_project 的 analyze.py bug

## Bug 复现

把 `data/notes.json` 换成全不带 `#标签` 的版本，跑 `python -m notes_app.cli stats`：

```
IndexError: list index out of range
```

## 原因

`analyze.py` 的 `summary()` 函数第 19 行：

```python
top_tag = counts[0][0]   # 当 counts 为空列表时，counts[0] 越界
```

`counts` 来自 `tag_counts()`，当所有笔记都没有标签时，`Counter` 是空的，`most_common()` 返回 `[]`，`counts[0]` 就会 `IndexError`。

## 修复

在访问 `counts[0]` 之前加一个空检查：

```python
# 修复前：
top_tag = counts[0][0]

# 修复后：
if not counts:
    lines = [
        f"共有 {len(notes)} 条笔记。",
        "还没有任何标签。",
    ]
    return "\n".join(lines)
top_tag = counts[0][0]
```

## Diff

```diff
--- a/notes_app/analyze.py
+++ b/notes_app/analyze.py
@@ -14,8 +14,14 @@
 def summary():
     """生成一段统计摘要。"""
     notes = all_notes()
     counts = tag_counts()
-    # BUG: 当没有任何带标签的笔记时,counts 是空列表,counts[0] 会抛 IndexError。
-    top_tag = counts[0][0]
+    # FIX: 当没有任何带标签的笔记时,counts 是空列表。
+    # 原代码直接 counts[0][0] 会抛 IndexError。
+    # 修复：先检查 counts 是否为空，空则给出友好提示。
+    if not counts:
+        lines = [
+            f"共有 {len(notes)} 条笔记。",
+            "还没有任何标签。",
+        ]
+        return "\n".join(lines)
+    top_tag = counts[0][0]
     lines = [
         f"共有 {len(notes)} 条笔记。",
```

## 修复后验证

```bash
# 空标签时不再崩溃：
python -m notes_app.cli stats
# 输出：
# 共有 3 条笔记。
# 还没有任何标签。
```

## 和 mini Claude Code 的关系

这个 bug 可以用 mini Claude Code 的任意一版来修：
1. 让它跑 `python -m notes_app.cli stats` 看到报错
2. 让它用 `read_file` 读 `analyze.py`
3. 让它说出"为什么会崩"（counts 为空时 counts[0] 越界）
4. 让它用 `write_file` 写回修复后的代码

最像真 Claude Code 的一步：第2步用 `read_file` 精确读取文件而不是 `cat`——这就是 c1 工具箱的意义。
最不像的一步：没有自动测试环节，真 CC 会跑一遍测试确认没改坏。
还差的机制：多 agent 协作（c3）——可以先派审查员定位 bug，再让主 agent 修。
