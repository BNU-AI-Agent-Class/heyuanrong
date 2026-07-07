"""cli.py — 命令行入口。用法见 README。"""
import sys
from . import store
from .analyze import summary


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("用法: add <文本> | list | find <关键词> | delete <编号> | stats")
        return
    cmd, rest = argv[0], argv[1:]

    if cmd == "add":
        n = store.add_note(" ".join(rest))
        print(f"已添加第 {n} 条笔记。")
    elif cmd == "list":
        for i, note in enumerate(store.all_notes()):
            tags = " ".join(f"#{t}" for t in note["tags"])
            print(f"[{i}] {note['text']}   {tags}")
    elif cmd == "find":
        for note in store.find_notes(" ".join(rest)):
            print(f"- {note['text']}")
    elif cmd == "delete":
        removed = store.delete_note(int(rest[0]))
        print(f"已删除: {removed['text']}" if removed else "编号不存在。")
    elif cmd == "stats":
        print(summary())
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
