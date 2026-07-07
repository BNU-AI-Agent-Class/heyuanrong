"""s0: 最小 API 骨架

目标：只验证"环境能跑"。
- 手动加载 .env
- 用 urllib 向模型发一次固定请求
- 打印回复
"""
import io
import json
import os
import sys
import urllib.request

# Windows 终端强制 UTF-8，避免中文乱码
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

# 默认使用 OpenRouter + Kimi，可在 .env 里覆盖 MODEL / BASE_URL
MODEL = os.getenv("MODEL", "moonshotai/kimi-k2")
BASE_URL = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")


def chat_completion(api_key, model, messages):
    """用内置 urllib 调用 OpenAI 兼容接口，无需安装 openai。"""
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

    messages = [
        {"role": "system", "content": "你是一个乐于助人的中文 AI 助手。"},
        {"role": "user", "content": "你好，请用一句话介绍自己。"},
    ]

    print(f"正在使用模型 {MODEL} 发送请求…")
    try:
        reply = chat_completion(api_key, MODEL, messages)
        print(f"模型回复：{reply}")
    except Exception as e:
        print(f"[错误] 调用失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
