# 选项A：给工具箱加一件"搜索"工具（改 c1）
# 对照真 Claude Code：这一步 = Grep 工具（在项目里按关键词搜文件内容，返回命中的文件名+行号）
# 新增：search(keyword, path) —— 遍历目录下所有文件，逐行搜索关键词，返回 "文件名:行号:该行内容"
import io, sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from dotenv import load_dotenv; load_dotenv()
from openrouter import OpenRouter
import os, json

MODEL = "moonshotai/kimi-k2"

def read_file(path):  return open(path, encoding="utf-8").read()
def write_file(path, text):
    open(path, "w", encoding="utf-8").write(text); return f"已写入 {path}"
def bash(cmd):        return os.popen(cmd).read()

def search(keyword, path="."):
    """在指定目录下搜索关键词，返回所有命中的「文件名:行号:该行内容」。
    跳过二进制文件和常见不需要搜的目录（如 .git, __pycache__）。
    最多返回 50 条命中，防止结果太长撑爆上下文。"""
    SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "logs"}
    SKIP_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".pdf", ".zip", ".exe", ".dll", ".pyc"}
    hits = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]          # 原地修改 dirs，跳过不需要的子目录
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SKIP_EXTS:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, 1):
                        if keyword in line:
                            # 用相对路径显示，更简洁
                            rel = os.path.relpath(fpath, path)
                            hits.append(f"{rel}:{lineno}: {line.rstrip()}")
                            if len(hits) >= 50:
                                hits.append("...（结果太多，只显示前50条）")
                                return "\n".join(hits)
            except (PermissionError, OSError):
                continue                                            # 读不了的文件直接跳过
    if not hits:
        return f"没有找到包含「{keyword}」的文件。"
    return "\n".join(hits)

TOOLS = {"read_file": read_file, "write_file": write_file, "bash": bash, "search": search}

def parse(s):
    s = s.strip().strip("`").removeprefix("json").strip(); return json.loads(s[s.find("{"): s.rfind("}") + 1])

SYSTEM = """你是一个编程助手。每次只回复一个 JSON，不要别的文字，不要 markdown 包裹；字符串值里别用英文双引号，要引用就用「」：
- 读文件：{"tool": "read_file", "args": {"path": "..."}}
- 写文件：{"tool": "write_file", "args": {"path": "...", "text": "..."}}
- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}
- 搜索代码：{"tool": "search", "args": {"keyword": "要搜的词", "path": "搜索目录"}}
- 完成时：{"done": "总结"}
优先用 read_file / write_file 处理文件，它们比 bash 更安全可控。
需要查找某个函数/变量在哪个文件里被使用时，用 search 工具。"""

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    messages = [{"role": "system", "content": SYSTEM}]
    while True:
        messages.append({"role": "user", "content": input("\n你：")})
        while True:
            reply = client.chat.send(model=MODEL, messages=messages).choices[0].message.content
            messages.append({"role": "assistant", "content": reply})
            try:
                action = parse(reply)
            except Exception:
                messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
            if "done" in action:
                print(f"[完成] {action['done']}"); break
            name, args = action["tool"], action["args"]
            print(f"[调用] {name}({args})")
            result = TOOLS[name](**args)
            print(f"[结果] {result}")
            messages.append({"role": "user", "content": f"工具返回：\n{result}"})
