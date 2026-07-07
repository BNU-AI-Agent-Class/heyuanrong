# 对照真 Claude Code：这一步 = Task / 子 agent（派子任务去探索，只拿回摘要，保持主上下文干净）
import io, sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from dotenv import load_dotenv; load_dotenv()                       # 1. 读取 API 密钥
from openrouter import OpenRouter                                   # 2. 导入 SDK
import os, json                                                     # 3. os / json

client = OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY"))        # 4. 客户端设为全局，主/子 agent 共用
MODEL = "moonshotai/kimi-k2"

def read_file(path):  return open(path, encoding="utf-8").read()   # 5. 工具：读文件
def bash(cmd):        return os.popen(cmd).read()                  # 6. 工具：执行命令
def subagent(task):                                                # 7. 工具：派一个"子智能体"独立完成一件事
    sub = [{"role": "system", "content": "你是子助手，用 JSON 干活："        #    关键：子 agent 有自己全新的 messages
            '{"tool":"bash","args":{"cmd":"..."}} 或 {"done":"结论"}'},   #    ——它的探索过程不会污染主对话
           {"role": "user", "content": task}]
    while True:                                                     # 8. 子 agent 自己的内层循环
        r = client.chat.send(model=MODEL, messages=sub).choices[0].message.content
        sub.append({"role": "assistant", "content": r})
        try: a = parse(r)                                          # 子 agent 也加固：坏格式就重发
        except Exception: sub.append({"role": "user", "content": "请只回合法 JSON"}); continue
        if "done" in a: return a["done"]                           # 9. 子 agent 只把最终结论返回给主 agent（摘要）
        out = bash(a["args"]["cmd"])
        sub.append({"role": "user", "content": f"输出：\n{out}"})
TOOLS = {"read_file": read_file, "bash": bash, "subagent": subagent}  # 10. 工具箱

def parse(s):                                                      # 容错解析：剥掉模型偶尔加的 ```json 包裹
    s = s.strip().strip("`").removeprefix("json").strip(); return json.loads(s[s.find("{"): s.rfind("}") + 1])
SYSTEM = """你是主编程助手。每次只回复一个 JSON，不要别的文字，不要 markdown；字符串值里别用英文双引号，要引用就用「」：
- 读文件：{"tool": "read_file", "args": {"path": "..."}}
- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}
- 派子助手：{"tool": "subagent", "args": {"task": "一句话描述要它独立完成的子任务"}}
- 完成：{"done": "总结"}
遇到需要大量探索的子任务（如"统计整个项目有多少行代码"），交给 subagent，只拿回结论，保持自己上下文干净。"""  # 11. 何时用子 agent

messages = [{"role": "system", "content": SYSTEM}]                 # 12. 主 agent 的历史
while True:                                                         # 13. 外层循环
    messages.append({"role": "user", "content": input("\n你：")})
    while True:                                                     # 14. 内层循环
        reply = client.chat.send(model=MODEL, messages=messages).choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        try:                                 # 15. 解析
            action = parse(reply)
        except Exception:                                  # 坏格式不崩：请模型重发（加固）
            messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
        if "done" in action:
            print(f"[完成] {action['done']}"); break
        name, args = action["tool"], action["args"]
        print(f"[调用] {name}({args})")
        result = TOOLS[name](**args)                               # 16. 派发（subagent 也是一个工具，只是它内部又跑了一个循环）
        print(f"[结果] {result}")
        messages.append({"role": "user", "content": f"工具返回：\n{result}"})
# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
