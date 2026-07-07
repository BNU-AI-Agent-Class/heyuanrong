# 选项B：给子 agent 装一个"代码审查员"人设（改 c3）
# 对照真 Claude Code：这一步 = code-review 子 agent（派审查员去通读代码、挑毛病、只报告不修改）
# 改动：subagent() 的 system 消息从"你是子助手"改成"你是代码审查员"，主 SYSTEM 里说明何时派审查员
import io, sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from dotenv import load_dotenv; load_dotenv()
from openrouter import OpenRouter
import os, json

client = OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY"))
MODEL = "moonshotai/kimi-k2"

def read_file(path):  return open(path, encoding="utf-8").read()
def bash(cmd):        return os.popen(cmd).read()

def subagent(task):
    """派一个「代码审查员」子 agent 去独立审查代码。
    子 agent 有自己全新的 messages，探索过程不会污染主对话。
    它会通读项目代码、找出潜在 bug，只把审查报告返回给主 agent。"""
    sub = [{"role": "system", "content": """你是代码审查员。你的任务是读代码、找逻辑漏洞（空输入、越界、异常没处理等），只报告不修改。
用 JSON 干活：
- 读文件：{"tool":"read_file","args":{"path":"..."}}
- 执行命令：{"tool":"bash","args":{"cmd":"..."}}
- 报告：{"done":"你的审查结论"}

注意：
1. 先用 bash 的 ls 或 find 列出项目里有哪些文件，然后逐个用 read_file 读取。
2. 重点关注：空列表/空字典访问、数组越界、除以零、未处理的异常、类型错误。
3. 找到 bug 后，说明在哪个文件、哪一行、什么情况下会出问题。
4. 不要修改任何文件，只报告。"""},
           {"role": "user", "content": task}]
    while True:
        r = client.chat.send(model=MODEL, messages=sub).choices[0].message.content
        sub.append({"role": "assistant", "content": r})
        try: a = parse(r)
        except Exception: sub.append({"role": "user", "content": "请只回合法 JSON"}); continue
        if "done" in a: return a["done"]
        name = a.get("tool")
        args = a.get("args", {})
        if name == "read_file":
            out = read_file(args["path"])
        elif name == "bash":
            out = bash(args["cmd"])
        else:
            out = f"未知工具: {name}"
        sub.append({"role": "user", "content": f"输出：\n{out}"})

TOOLS = {"read_file": read_file, "bash": bash, "subagent": subagent}

def parse(s):
    s = s.strip().strip("`").removeprefix("json").strip(); return json.loads(s[s.find("{"): s.rfind("}") + 1])

SYSTEM = """你是主编程助手。每次只回复一个 JSON，不要别的文字，不要 markdown；字符串值里别用英文双引号，要引用就用「」：
- 读文件：{"tool": "read_file", "args": {"path": "..."}}
- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}
- 派审查员：{"tool": "subagent", "args": {"task": "一句话描述要审查的项目路径和关注点"}}
- 完成：{"done": "总结"}
当用户需要检查代码质量、找潜在 bug 时，派 subagent（代码审查员）去通读代码。
审查员会独立读文件、找问题，只把报告返回给你。你把审查结论完整转达给用户。"""

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
