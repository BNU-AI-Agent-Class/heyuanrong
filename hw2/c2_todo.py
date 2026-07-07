# 对照真 Claude Code：这一步 = TodoWrite（让模型把计划写进一个能反复更新的工具）
import io, sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from dotenv import load_dotenv; load_dotenv()                       # 1. 读取 API 密钥
from openrouter import OpenRouter                                   # 2. 导入 SDK
import os, json                                                     # 3. os / json

MODEL = "moonshotai/kimi-k2"

TODOS = []                                                          # 4. 全局任务清单（就是 Claude Code 里的 TodoWrite）
def read_file(path):  return open(path, encoding="utf-8").read()   # 5. 工具：读文件
def write_file(path, text):
    open(path, "w", encoding="utf-8").write(text); return f"已写入 {path}"
def bash(cmd):        return os.popen(cmd).read()                  # 6. 工具：执行命令
def todo_write(items):                                             # 7. 工具：更新任务清单
    global TODOS; TODOS = items                                     #    items 形如 [{"task":"...","done":false}, ...]
    board = "\n".join(f"  {'☑' if t['done'] else '☐'} {t['task']}" for t in TODOS)
    print(f"[计划]\n{board}"); return "清单已更新"                    #    打印带勾选框的清单，让"思考"可见
TOOLS = {"read_file": read_file, "write_file": write_file, "bash": bash, "todo_write": todo_write}  # 8. 工具箱

def parse(s):                                                      # 容错解析：剥掉模型偶尔加的 ```json 包裹
    s = s.strip().strip("`").removeprefix("json").strip(); return json.loads(s[s.find("{"): s.rfind("}") + 1])
SYSTEM = """你是一个编程助手。每次只回复一个 JSON，不要别的文字，不要 markdown；字符串值里别用英文双引号，要引用就用「」：
- 规划：{"tool": "todo_write", "args": {"items": [{"task": "步骤A", "done": false}, ...]}}
- 读文件：{"tool": "read_file", "args": {"path": "..."}}
- 写文件：{"tool": "write_file", "args": {"path": "...", "text": "..."}}
- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}
- 完成：{"done": "总结"}
接到多步任务时，先用 todo_write 列出计划；每完成一步就用 todo_write 更新勾选状态。"""  # 9. 要求"先列计划再动手"

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client: # 10. 客户端
    messages = [{"role": "system", "content": SYSTEM}]             # 11. 历史
    while True:                                                     # 12. 外层循环
        messages.append({"role": "user", "content": input("\n你：")})
        while True:                                                 # 13. 内层循环
            reply = client.chat.send(model=MODEL,
                                     messages=messages).choices[0].message.content
            messages.append({"role": "assistant", "content": reply})
            try:                              # 14. 解析
                action = parse(reply)
            except Exception:                              # 坏格式不崩：请模型重发（这就是加固）
                messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
            if "done" in action:
                print(f"[完成] {action['done']}"); break
            name, args = action["tool"], action["args"]
            result = TOOLS[name](**args)                            # 15. 派发（todo_write 也是一个普通工具！）
            if name != "todo_write": print(f"[调用] {name} → {result}")
            messages.append({"role": "user", "content": f"工具返回：\n{result}"})
# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
