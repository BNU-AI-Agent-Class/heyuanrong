"""s1: 单轮聊天

目标：用户输入一次，模型回答一次。
- 无历史，所以它"记不住"。
"""
import io
import json
import os
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


def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[错误] 找不到 OPENROUTER_API_KEY。")
        print("请在 .env 文件中设置：OPENROUTER_API_KEY=你的密钥")
        sys.exit(1)

    system_prompt = (
        "你是 Kimi，一个 helpful、幽默的中文 AI 助手。"
        "请用自然、口语化的中文和用户聊天，像朋友一样。"
    )

    user_input = input("你：").strip()
    if not user_input:
        print("输入为空，已退出。")
        return

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    try:
        reply = chat_completion(api_key, MODEL, messages)
        print(f"AI：{reply}")
    except Exception as e:
        print(f"[错误] 调用失败：{e}")


if __name__ == "__main__":
    main()
