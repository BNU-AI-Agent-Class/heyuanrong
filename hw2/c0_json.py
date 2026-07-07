# 对照真 Claude Code：这一步 = tool_use（模型返回结构化工具调用，我们用手写 JSON 做极简版）
import io, sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from dotenv import load_dotenv; load_dotenv()                       # 1. 读取 .env 里的 API 密钥（和昨天 s3 一样）
from openrouter import OpenRouter                                   # 2. 导入 OpenRouter SDK
import os, json                                                     # 3. os 执行命令；json 解析结构化协议

MODEL = "moonshotai/kimi-k2"                                       # 3b. 模型（适配自己的 OpenRouter key）

SYSTEM = """你是一个编程助手。每次只回复一个 JSON，不要有别的文字，不要用 markdown 包裹；字符串值里别用英文双引号，要引用就用「」：
- 要执行命令时：{"tool": "bash", "args": {"cmd": "要执行的命令"}}
- 任务完成时：  {"done": "给用户的总结"}"""                             # 4. 系统提示词：把 s3 的"命令:/完成:"文本协议，升级成 JSON 协议

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client: # 5. 创建客户端
    messages = [{"role": "system", "content": SYSTEM}]             # 6. 对话历史，第一条是系统提示
    while True:                                                     # 7. 外层循环：等用户下达新任务
        messages.append({"role": "user", "content": input("\n你：")})  # 8. 用户输入存入历史
        while True:                                                 # 9. 内层循环：Agent 自主执行直到完成
            reply = client.chat.send(model=MODEL,
                                     messages=messages).choices[0].message.content  # 10. 调用模型，取回复
            messages.append({"role": "assistant", "content": reply})# 11. AI 回复存入历史
            try:
                action = json.loads(reply)                          # 12. 关键升级：把 JSON 文本解析成 Python 字典
            except Exception:
                messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
            if "done" in action:                                    # 13. 如果是完成信号 → 跳出内层循环
                print(f"[完成] {action['done']}"); break
            cmd = action["args"]["cmd"]                             # 14. 从结构化字段里取命令（不再靠字符串切割）
            print(f"[执行] {cmd}")
            result = os.popen(cmd).read()                           # 15. 执行命令
            print(f"[结果] {result}")
            messages.append({"role": "user", "content": f"命令输出：\n{result}"})  # 16. 把结果反馈给 AI
# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
