# 对照真 Claude Code：这一步 = /compact 自动压缩（长会话把历史折叠成摘要，重开窗口）
import io, sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from dotenv import load_dotenv; load_dotenv()                       # 1. 读取 API 密钥
from openrouter import OpenRouter                                   # 2. 导入 SDK
import os, json                                                     # 3. os / json

client = OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY"))        # 4. 客户端（全局，压缩时也要用）
MODEL = "moonshotai/kimi-k2"
LIMIT = 12                                                          # 5. 阈值：历史超过这么多条就压缩（真 CC 看 token，这里简化成条数）

def bash(cmd): return os.popen(cmd).read()                         # 6. 工具：执行命令
TOOLS = {"bash": bash}

def compact(messages):                                             # 7. 关键升级：把长历史"压缩"成一条摘要
    system = messages[0]                                            #    保留系统提示
    body = "\n".join(f'{m["role"]}: {m["content"]}' for m in messages[1:])
    summary = client.chat.send(model=MODEL, messages=[             #    让模型自己总结"目前为止做了什么、进行到哪"
        {"role": "user", "content": f"用要点总结这段对话的进展和关键结论，供接力：\n{body}"}
    ]).choices[0].message.content
    print("[压缩] 历史已折叠成一条摘要，窗口重开")
    return [system, {"role": "user", "content": f"【之前进展摘要】\n{summary}"}]  # 8. 新历史 = 系统提示 + 摘要

def parse(s):                                                      # 容错解析：剥掉模型偶尔加的 ```json 包裹
    s = s.strip().strip("`").removeprefix("json").strip(); return json.loads(s[s.find("{"): s.rfind("}") + 1])
SYSTEM = """你是编程助手。每次只回复一个 JSON，不要别的文字，不要 markdown；字符串值里别用英文双引号，要引用就用「」：
{"tool": "bash", "args": {"cmd": "..."}} 或 {"done": "总结"}"""     # 9. 系统提示

messages = [{"role": "system", "content": SYSTEM}]                 # 10. 历史
while True:                                                         # 11. 外层循环
    messages.append({"role": "user", "content": input("\n你：")})
    while True:                                                     # 12. 内层循环
        if len(messages) > LIMIT:                                  # 13. 每轮先检查：太长了就压缩
            messages = compact(messages)
        reply = client.chat.send(model=MODEL, messages=messages).choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        try:                                 # 14. 解析
            action = parse(reply)
        except Exception:                              # 坏格式不崩：请模型重发（这就是加固）
            messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
        if "done" in action:
            print(f"[完成] {action['done']}"); break
        result = bash(action["args"]["cmd"])                       # 15. 执行
        print(f"[执行] {action['args']['cmd']}\n[结果] {result}")
        messages.append({"role": "user", "content": f"输出：\n{result}"})
# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
