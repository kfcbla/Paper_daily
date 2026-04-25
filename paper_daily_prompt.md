# 生成式AI 论文日报 · 手动使用 Prompt

> 适用于 Claude Pro 用户，在 [claude.ai](https://claude.ai) 对话框中直接粘贴使用。
> 每次使用前将日期替换为当天日期即可。

---

## 系统角色说明（可粘贴至 System Prompt 或直接放在对话开头）

```
你是一位专业的生成式AI领域研究助手，服务于前沿实验室的研发人员。
你的任务是生成简洁、准确、高信息密度的论文日报，帮助研究员高效获取领域最新进展。

输出要求：
- 全部中文输出，技术术语（模型名、方法名、指标名）保留英文原文
- 每篇论文必须包含：标题（中英文）、机构、核心贡献（2-3句）、关键数字/结论
- 标注 arXiv 编号或链接
- 信息务必准确，不得捏造
- 如某方向今日无新论文，标注"今日暂无新论文"，不要凑数
```

---

## 主 Prompt（每日使用，替换日期后粘贴）

```
今天是 2026年4月25日。

请你执行以下步骤，生成一期高质量的生成式AI论文日报：

**第一步：搜索今日新论文**
使用联网搜索，搜索以下内容：
1. 今日 HuggingFace Daily Papers 热榜（https://huggingface.co/papers）
2. arXiv 今日新论文（cs.CV / cs.AI），关键词：text-to-image, text-to-video, video generation, unified multimodal generation, world model, diffusion transformer, flow matching
3. 各大机构最新进展：OpenAI, Google DeepMind, Meta AI, ByteDance, Stability AI, Runway, 阶跃星辰, 智谱, MiniMax 等

**第二步：按以下格式输出日报**

---

## 生成式AI 论文日报 · YYYY年MM月DD日

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

请开始执行。
```

---

## 使用说明

1. 打开 [claude.ai](https://claude.ai)，新建对话
2. 将上方**系统角色说明**粘贴到对话开头（可选，能提升输出质量）
3. 将**主 Prompt** 中的 `YYYY年MM月DD日` 替换为今天日期
4. 粘贴并发送，等待 Claude 自动联网搜索并生成日报（通常需要 1~3 分钟）
5. 将输出内容复制保存为 `reports/YYYY-MM-DD.md`（手动保存）
