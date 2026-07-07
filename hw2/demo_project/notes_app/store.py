"""store.py — 负责把笔记读写到 data/notes.json。"""
import json, os
from datetime import datetime

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "notes.json")


def _load():
    if not os.path.exists(DATA):
        return []
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def _save(notes):
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def add_note(text):
    """新增一条笔记。文本里以 # 开头的词会被当作标签。"""
    notes = _load()
    tags = [w[1:] for w in text.split() if w.startswith("#")]
    notes.append({"text": text, "tags": tags, "created": datetime.now().isoformat(timespec="seconds")})
    _save(notes)
    return len(notes)


def all_notes():
    return _load()


def find_notes(keyword):
    return [n for n in _load() if keyword in n["text"]]


def delete_note(index):
    notes = _load()
    if 0 <= index < len(notes):
        removed = notes.pop(index)
        _save(notes)
        return removed
    return None
