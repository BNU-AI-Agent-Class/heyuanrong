# 选项C：防崩加强版（改 c1）——堵住两个洞
# 对照真 Claude Code：真 CC 遇到模型调用不存在的工具会告诉它"没这个工具"，而不是崩溃
# 改动1：未知工具名 → 不崩，提示"没有这个工具，可用的有：…"让模型自己纠正
# 改动2：连续失败计数器 → 超过 MAX_RETRIES 次就体面停下，不会无限循环
import io, sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from dotenv import load_dotenv; load_dotenv()
from openrouter import OpenRouter
import os, json

MODEL = "moonshotai/kimi-k2"
MAX_RETRIES = 5          # 连续失败超过这么多次就放弃（防止无限循环）

def read_file(path):  return open(path, encoding="utf-8").read()
def write_file(path, text):
    open(path, "w", encoding="utf-8").write(text); return f"已写入 {path}"
def bash(cmd):        return os.popen(cmd).read()
TOOLS = {"read_file": read_file, "write_file": write_file, "bash": bash}

def parse(s):
    s = s.strip().strip("`").removeprefix("json").strip(); return json.loads(s[s.find("{"): s.rfind("}") + 1])

SYSTEM = """你是一个编程助手。每次只回复一个 JSON，不要别的文字，不要 markdown 包裹；字符串值里别用英文双引号，要引用就用「」：
- 读文件：{"tool": "read_file", "args": {"path": "..."}}
- 写文件：{"tool": "write_file", "args": {"path": "...", "text": "..."}}
- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}
- 完成时：{"done": "总结"}
优先用 read_file / write_file 处理文件，它们比 bash 更安全可控。"""

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    messages = [{"role": "system", "content": SYSTEM}]
    while True:
        messages.append({"role": "user", "content": input("\n你：")})
        retries = 0                                              # 连续失败计数器（成功一步后清零）
        while True:
            reply = client.chat.send(model=MODEL, messages=messages).choices[0].message.content
            messages.append({"role": "assistant", "content": reply})
            try:
                action = parse(reply)
            except Exception:
                # 洞1补充：坏 JSON 不崩，提示模型重发
                retries += 1
                if retries >= MAX_RETRIES:
                    print(f"[放弃] 连续 {MAX_RETRIES} 次解析失败，停止当前任务。"); break
                messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
            if "done" in action:
                print(f"[完成] {action['done']}"); break
            name, args = action.get("tool"), action.get("args", {})
            # 洞1：未知工具名 → 不崩，友好提示
            if name not in TOOLS:
                retries += 1
                if retries >= MAX_RETRIES:
                    print(f"[放弃] 连续 {MAX_RETRIES} 次错误，停止当前任务。"); break
                available = ", ".join(TOOLS.keys())
                hint = f"没有叫「{name}」的工具，可用的有：{available}。请用正确的工具名重试。"
                print(f"[提示] {hint}")
                messages.append({"role": "user", "content": hint}); continue
            # 派发执行
            try:
                result = TOOLS[name](**args)
                print(f"[调用] {name} → {result}")
                retries = 0                                      # 成功一步 → 清零计数器
            except Exception as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    print(f"[放弃] 连续 {MAX_RETRIES} 次工具执行失败，停止当前任务。"); break
                result = f"工具执行出错：{e}。请检查参数后重试。"
                print(f"[错误] {result}")
            messages.append({"role": "user", "content": f"工具返回：\n{result}"})
