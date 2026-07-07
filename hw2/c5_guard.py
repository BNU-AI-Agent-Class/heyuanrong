# 对照真 Claude Code：这一步 = 危险操作确认弹窗（rm、改关键文件前先问你 y/n）
import io, sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from dotenv import load_dotenv; load_dotenv()                       # 1. 读取 API 密钥
from openrouter import OpenRouter                                   # 2. 导入 SDK
import os, json                                                     # 3. os / json

MODEL = "moonshotai/kimi-k2"
DANGER = ["rm ", "rmdir", "del ", "sudo", "mv ", "> /", "mkfs", "dd ", ":(){"]  # 4. 危险命令黑名单（真 CC 的权限系统远比这复杂）

def bash(cmd):                                                     # 5. 工具：执行命令，但先过安全门
    if any(d in cmd for d in DANGER):                             # 6. 命中危险词 → 停下来问人（这就是 Human-in-the-loop）
        if input(f"[⚠ 权限] 要执行危险命令：{cmd}\n允许吗？(y/n) ").strip().lower() != "y":
            return "用户拒绝了这条命令。"                             # 7. 人说不 → 不执行，把拒绝结果告诉 AI
    return os.popen(cmd).read()                                    # 8. 安全或已获批准 → 执行

def parse(s):                                                      # 容错解析：剥掉模型偶尔加的 ```json 包裹
    s = s.strip().strip("`").removeprefix("json").strip(); return json.loads(s[s.find("{"): s.rfind("}") + 1])
SYSTEM = """你是编程助手。每次只回复一个 JSON，不要别的文字，不要 markdown；字符串值里别用英文双引号，要引用就用「」：
{"tool": "bash", "args": {"cmd": "..."}} 或 {"done": "总结"}"""     # 9. 系统提示

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
            cmd = action["args"]["cmd"]
            print(f"[执行] {cmd}")
            result = bash(cmd)                                     # 15. 通过安全门执行
            print(f"[结果] {result}")
            messages.append({"role": "user", "content": f"输出：\n{result}"})
# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
# 恭喜：你已经从 s3 的 30 行文本 agent，长出了一个有工具箱/计划/子agent/压缩/权限门的 mini Claude Code。
