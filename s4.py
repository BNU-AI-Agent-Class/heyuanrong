"""s4: 把规则放进 md

目标：系统提示词不再写死。
- 新建 / 读取 agent.md
- 其他循环基本不变
"""
import io
import json
import os
import subprocess
import sys
import urllib.request

if sys.platform == "win32":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    if sys.stderr.encoding.lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)


def load_env(env_path=".env"):
    """手动加载 .env，不依赖 python-dotenv。"""
    env_file = os.path.join(os.path.dirname(__file__), env_path)
    if not os.path.exists(env_file):
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_env()

MODEL = os.getenv("MODEL", "moonshotai/kimi-k2")
BASE_URL = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")

BLOCKLIST = ("rm -rf /", "mkfs", "dd if=", "del /f /s /q", "format")


def load_prompt(path):
    """读取 markdown 提示词文件。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def chat_completion(api_key, model, messages):
    """用内置 urllib 调用 OpenAI 兼容接口。"""
    data = json.dumps({
        "model": model,
        "messages": messages,
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e

    if "choices" not in result or not result["choices"]:
        raise RuntimeError(f"返回异常：{result}")

    return result["choices"][0]["message"]["content"]


def is_dangerous(command):
    lower = command.lower()
    return any(b.lower() in lower for b in BLOCKLIST)


def run_command(command):
    """执行单条 shell 命令，返回输出。"""
    print(f"[执行命令] {command}")
    if is_dangerous(command):
        return "该命令被拒绝执行（存在安全风险）。"
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="ignore",
        )
        output = result.stdout.strip()
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr.strip()
        if not output:
            output = "（命令执行成功，无输出）"
        return output
    except subprocess.TimeoutExpired:
        return "命令执行超时。"
    except Exception as e:
        return f"执行出错：{e}"


def agent_turn(api_key, model, messages, user_input):
    """执行一轮 Agent 自主循环。返回 (updated_messages, final_reply)。"""
    messages = messages + [{"role": "user", "content": user_input}]

    while True:
        reply = chat_completion(api_key, model, messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"AI：{reply}")

        stripped = reply.strip()
        if stripped.startswith("完成:"):
            return messages, reply

        if not stripped.startswith("命令:"):
            return messages, reply

        command = stripped.split("命令:", 1)[1].strip()
        result = run_command(command)
        print(f"[执行结果]\n{result}\n")
        messages.append({"role": "user", "content": f"执行完毕，结果如下：\n{result}"})


def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[错误] 找不到 OPENROUTER_API_KEY。")
        print("请在 .env 文件中设置：OPENROUTER_API_KEY=你的密钥")
        sys.exit(1)

    prompt_path = os.path.join(os.path.dirname(__file__), "agent.md")
    if not os.path.exists(prompt_path):
        print(f"[错误] 找不到 {prompt_path}，请先创建 agent.md。")
        sys.exit(1)

    system_prompt = load_prompt(prompt_path)
    messages = [{"role": "system", "content": system_prompt}]

    print("Agent 已启动（prompt 来自 agent.md），输入任务，输入 'exit'、'quit' 或 '退出' 可结束。\n")

    while True:
        try:
            user_input = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "退出"):
            print("再见！")
            break

        try:
            messages, final = agent_turn(api_key, MODEL, messages, user_input)
            print()
        except Exception as e:
            print(f"[错误] Agent 运行失败：{e}\n")


if __name__ == "__main__":
    main()
