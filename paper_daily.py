"""
生成式AI论文日报生成器
使用 Claude API + 内置 Web Search 工具，自动搜索并总结最新论文。

依赖:
    pip install anthropic

使用:
    python paper_daily.py

输出:
    reports/YYYY-MM-DD.md  (Markdown 日报文件)
    同时打印到终端
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import anthropic

# ── 配置 ────────────────────────────────────────────────────────────────────

MODEL = "claude-opus-4-6"
OUTPUT_DIR = Path("reports")

SYSTEM_PROMPT = """你是一位专业的生成式AI领域研究助手，服务于前沿实验室的研发人员。
你的任务是生成简洁、准确、高信息密度的论文日报，帮助研究员高效获取领域最新进展。

输出要求：
- 全部中文输出，技术术语（模型名、方法名、指标名）保留英文原文
- 每篇论文必须包含：标题（中英文）、机构、核心贡献（2-3句）、关键数字/结论
- 标注 arXiv 编号或链接
- 信息务必准确，不得捏造
- 如某方向今日无新论文，标注"今日暂无新论文"，不要凑数"""

USER_PROMPT_TEMPLATE = """今天是 {date}。

请你执行以下步骤，生成一期高质量的生成式AI论文日报：

**第一步：搜索今日新论文**
使用 web_search 和 web_fetch 工具，搜索以下内容：
1. 今日 HuggingFace Daily Papers 热榜（https://huggingface.co/papers）
2. arXiv 今日新论文（cs.CV / cs.AI），关键词：text-to-image, text-to-video, video generation, unified multimodal generation, world model, diffusion transformer, flow matching
3. 各大机构最新进展：OpenAI, Google DeepMind, Meta AI, ByteDance, Stability AI, Runway, 阶跃星辰, 智谱, MiniMax 等

**第二步：按以下格式输出日报**

---

## 生成式AI 论文日报 · {date}

### 今日 HuggingFace 热榜 Top 5
（每条格式：序号. **论文标题** | 机构 | 一句话贡献 | [链接]）

### 文生图（Text-to-Image）
（每篇格式如下）
**论文标题（英文）**
- 中文标题：
- 机构：
- arXiv：
- 核心贡献：
- 关键结论：

### 文生视频（Text-to-Video）
（同上格式）

### 生成统一（Unified Generation / Any-to-Any）
（同上格式）

### 世界模型（World Model）
（同上格式）

### 行业动态
- 简要列出今日重要模型发布、开源、博客、融资等

### 编辑观察
（2-3句话，点出今日最值得关注的趋势或信号）

---

请开始执行。"""

# ── 主逻辑 ───────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        print("[错误] 未找到 ANTHROPIC_API_KEY 环境变量。")
        print("请设置: export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)
    return key


def build_prompt() -> str:
    date_str = datetime.now().strftime("%Y年%m月%d日")
    return USER_PROMPT_TEMPLATE.format(date=date_str)


def save_report(content: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    filename = OUTPUT_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    filename.write_text(content, encoding="utf-8")
    return filename


def run() -> None:
    client = anthropic.Anthropic(api_key=get_api_key())

    tools = [
        {"type": "web_search_20260209", "name": "web_search"},
        {"type": "web_fetch_20260209",  "name": "web_fetch"},
    ]

    messages = [{"role": "user", "content": build_prompt()}]

    print("=" * 60)
    print("生成式AI 论文日报生成器")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print("[信息] 正在搜索最新论文，请稍候（通常需要 1-3 分钟）...\n")

    full_text_parts: list[str] = []

    # 工具调用循环：Claude 会自动搜索并在完成后生成报告
    while True:
        with client.messages.stream(
            model=MODEL,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        ) as stream:
            current_tool_name = None

            for event in stream:
                # 工具调用开始：打印进度提示
                if event.type == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool_name = block.name
                        print(f"  [搜索] 调用 {block.name}...", flush=True)

                # 流式输出正文
                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        print(delta.text, end="", flush=True)
                        full_text_parts.append(delta.text)

            response = stream.get_final_message()

        # 判断是否还有工具调用需要处理
        if response.stop_reason == "tool_use":
            # 把 assistant 消息和所有 tool_result 加回 messages，继续循环
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # server-side tool 的结果由 API 自动处理，
                    # 这里只需将 tool_use block 回传即可（不需要本地执行）
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "[工具已由服务器执行，结果已嵌入上下文]",
                    })

            messages.append({"role": "user", "content": tool_results})

        else:
            # end_turn：生成完毕
            break

    report_content = "".join(full_text_parts)

    if not report_content.strip():
        print("\n[警告] 未能获取有效报告内容，请检查 API Key 或网络连接。")
        sys.exit(1)

    # 保存文件
    output_path = save_report(report_content)
    print(f"\n\n{'=' * 60}")
    print(f"[完成] 日报已保存至：{output_path.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    run()
