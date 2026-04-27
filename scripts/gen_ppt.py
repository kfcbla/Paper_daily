"""Generate PPT from paper daily report 2026-04-27."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Palette ──────────────────────────────────────────────────────────────
BG_DARK   = RGBColor(0x0D, 0x1B, 0x2A)   # 深蓝底
ACCENT    = RGBColor(0x00, 0xC8, 0xFF)   # 青蓝高亮
GOLD      = RGBColor(0xFF, 0xC2, 0x00)   # 金色强调
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
GRAY      = RGBColor(0xB0, 0xBE, 0xCC)
CARD_BG   = RGBColor(0x14, 0x2A, 0x3E)   # 卡片背景

W = Inches(13.33)   # 宽屏 16:9
H = Inches(7.5)

def new_prs():
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    return prs

def blank_slide(prs):
    layout = prs.slide_layouts[6]   # completely blank
    return prs.slides.add_slide(layout)

def fill_bg(slide, color=BG_DARK):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_rect(slide, left, top, width, height, color, alpha=None):
    shape = slide.shapes.add_shape(1, left, top, width, height)   # MSO_SHAPE_TYPE.RECTANGLE = 1
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape

def add_text(slide, text, left, top, width, height,
             font_size=18, bold=False, color=WHITE,
             align=PP_ALIGN.LEFT, word_wrap=True):
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf  = txb.text_frame
    tf.word_wrap = word_wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(font_size)
    run.font.bold  = bold
    run.font.color.rgb = color
    return txb

def add_label(slide, text, left, top, width=Inches(2), height=Inches(0.35),
              bg=ACCENT, fg=BG_DARK, font_size=11):
    add_rect(slide, left, top, width, height, bg)
    add_text(slide, text, left + Inches(0.08), top + Inches(0.02),
             width - Inches(0.16), height, font_size=font_size,
             bold=True, color=fg, align=PP_ALIGN.CENTER)

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 1 · Cover
# ═══════════════════════════════════════════════════════════════════════════
def slide_cover(prs):
    s = blank_slide(prs)
    fill_bg(s)
    # accent bar top
    add_rect(s, 0, 0, W, Inches(0.08), ACCENT)
    # accent bar bottom
    add_rect(s, 0, H - Inches(0.08), W, Inches(0.08), ACCENT)

    # main title
    add_text(s, "生成式 AI 论文日报", Inches(1), Inches(1.6), Inches(11.3), Inches(1.5),
             font_size=54, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    # date
    add_text(s, "2026 年 4 月 27 日", Inches(1), Inches(3.1), Inches(11.3), Inches(0.9),
             font_size=32, bold=False, color=ACCENT, align=PP_ALIGN.CENTER)
    # sub
    add_text(s, "Text-to-Image · Text-to-Video · Unified Generation · World Model · 行业动态",
             Inches(1), Inches(3.9), Inches(11.3), Inches(0.6),
             font_size=16, color=GRAY, align=PP_ALIGN.CENTER)
    # source note
    add_text(s, "数据来源：HuggingFace Daily Papers · arXiv cs.CV/cs.AI · 各机构官方渠道",
             Inches(1), Inches(5.8), Inches(11.3), Inches(0.5),
             font_size=12, color=GRAY, align=PP_ALIGN.CENTER)
    return s

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 2 · HuggingFace 热榜 Top 5
# ═══════════════════════════════════════════════════════════════════════════
def slide_hf_top5(prs):
    s = blank_slide(prs)
    fill_bg(s)
    add_rect(s, 0, 0, W, Inches(0.08), ACCENT)

    # title
    add_text(s, "🔥  今日 HuggingFace 热榜 Top 5",
             Inches(0.5), Inches(0.15), Inches(12), Inches(0.7),
             font_size=28, bold=True, color=ACCENT)

    items = [
        ("1", "Seedance 2.0",
         "ByteDance Seed | 统一多模态音视频联合生成，支持文/图/视/音四模态，人体动作自然度大幅提升",
         "arXiv 2604.14148"),
        ("2", "HY-World 2.0",
         "Tencent 混元 | 四阶段流水线生成可导航高保真 3D 世界，开源性能媲美闭源 Marble",
         "arXiv 2604.14268"),
        ("3", "Image Generators are Generalist Vision Learners",
         "图像生成训练具有类 LLM 预训练效果，表征可零样本迁移至下游视觉任务达 SOTA",
         "arXiv 2604.20329"),
        ("4", "Sparse Forcing",
         "可训练稀疏注意力与自回归扩散原生结合，同步提升长视频质量与解码速度",
         "arXiv 2604.21221"),
        ("5", "Claude Code Agent Architecture Survey",
         "以 Claude Code 为参照系统梳理 AI Agent 设计空间，HuggingFace 日榜 305 upvotes",
         "—"),
    ]

    row_h = Inches(1.05)
    for i, (num, title, desc, link) in enumerate(items):
        top = Inches(0.95) + i * row_h
        # card
        add_rect(s, Inches(0.35), top, Inches(12.6), Inches(0.92), CARD_BG)
        # number badge
        add_rect(s, Inches(0.35), top, Inches(0.45), Inches(0.92), ACCENT)
        add_text(s, num, Inches(0.35), top + Inches(0.18), Inches(0.45), Inches(0.55),
                 font_size=20, bold=True, color=BG_DARK, align=PP_ALIGN.CENTER)
        # title
        add_text(s, title, Inches(0.88), top + Inches(0.04), Inches(9.5), Inches(0.38),
                 font_size=15, bold=True, color=WHITE)
        # desc
        add_text(s, desc, Inches(0.88), top + Inches(0.42), Inches(9.5), Inches(0.46),
                 font_size=11, color=GRAY)
        # link
        add_text(s, link, Inches(10.55), top + Inches(0.28), Inches(2.3), Inches(0.38),
                 font_size=10, color=ACCENT, align=PP_ALIGN.RIGHT)
    return s

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 3 · 文生图
# ═══════════════════════════════════════════════════════════════════════════
def slide_t2i(prs):
    s = blank_slide(prs)
    fill_bg(s)
    add_rect(s, 0, 0, W, Inches(0.08), GOLD)

    add_text(s, "🎨  文生图（Text-to-Image）",
             Inches(0.5), Inches(0.15), Inches(12), Inches(0.7),
             font_size=28, bold=True, color=GOLD)

    papers = [
        {
            "title": "Image Generators are Generalist Vision Learners",
            "zh": "图像生成模型是通用视觉学习器",
            "org": "未具体披露",
            "arxiv": "2604.20329（2026-04-22）",
            "contrib": "证明图像生成训练对视觉表征具有类 LLM 预训练效果；习得特征可零样本/少样本迁移至多种下游视觉任务，无需任务特定微调。",
            "key": "'生成即预训练'范式在视觉领域成立；生成-理解统一不仅是能力融合，更是表征效率的根本提升。",
        },
        {
            "title": "Frequency-Forcing: From Scaling-as-Time to Soft Frequency Guidance",
            "zh": "频率强制：从时间维度缩放到软频率引导",
            "org": "未具体披露",
            "arxiv": "2604.20902（2026-04-21）",
            "contrib": "将扩散/流匹配去噪过程重新解释为频率引导过程，先低频后高频，提出'软频率引导'机制替代传统时间步缩放。",
            "key": "显式频率控制相比隐式时间步调度在生成质量与可控性上均有提升，为扩散模型加速提供新思路。",
        },
    ]

    for i, p in enumerate(papers):
        top = Inches(1.0) + i * Inches(2.9)
        add_rect(s, Inches(0.35), top, Inches(12.6), Inches(2.65), CARD_BG)
        add_label(s, "论文", Inches(0.5), top + Inches(0.12), Inches(0.8), Inches(0.3), GOLD, BG_DARK, 10)
        add_text(s, p["title"], Inches(1.4), top + Inches(0.1), Inches(11.2), Inches(0.42),
                 font_size=14, bold=True, color=WHITE)
        add_text(s, f"中文：{p['zh']}　　机构：{p['org']}　　arXiv：{p['arxiv']}",
                 Inches(0.5), top + Inches(0.55), Inches(12.4), Inches(0.3),
                 font_size=10, color=GRAY)
        add_text(s, f"▶ 核心贡献：{p['contrib']}",
                 Inches(0.5), top + Inches(0.88), Inches(12.4), Inches(0.65),
                 font_size=11, color=WHITE)
        add_text(s, f"✦ 关键结论：{p['key']}",
                 Inches(0.5), top + Inches(1.58), Inches(12.4), Inches(0.85),
                 font_size=11, color=ACCENT)
    return s

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 4 · 文生视频
# ═══════════════════════════════════════════════════════════════════════════
def slide_t2v(prs):
    s = blank_slide(prs)
    fill_bg(s)
    add_rect(s, 0, 0, W, Inches(0.08), RGBColor(0x00, 0xFF, 0xAA))

    add_text(s, "🎬  文生视频（Text-to-Video）",
             Inches(0.5), Inches(0.15), Inches(12), Inches(0.7),
             font_size=28, bold=True, color=RGBColor(0x00, 0xFF, 0xAA))

    COLOR = RGBColor(0x00, 0xFF, 0xAA)
    papers = [
        {
            "title": "Seedance 2.0: Advancing Video Generation for World Complexity",
            "zh": "Seedance 2.0：推动视频生成应对复杂世界",
            "org": "ByteDance Seed Team",
            "arxiv": "2604.14148",
            "contrib": "原生多模态音视频联合模型，支持文/图/视/音四模态；最多参考3段视频+9张图+3段音频，生成4-15s、480p/720p；含加速版 Fast variant。",
            "key": "人体动作建模自然度、时序一致性、物理合理性相比前代显著提升；专家评测与公开用户测试均达业内领先。",
        },
        {
            "title": "Sparse Forcing: Native Trainable Sparse Attention for Real-time Autoregressive Diffusion Video Generation",
            "zh": "稀疏强制：实时自回归扩散视频生成的原生可训练稀疏注意力",
            "org": "未具体披露",
            "arxiv": "2604.21221",
            "contrib": "Sparse Forcing 训练-推理范式，将可训练稀疏注意力与自回归扩散原生集成，提升长序列质量同时降低解码延迟。",
            "key": "同时解决自回归视频扩散的效率与长视频质量痛点，为实时视频生成提供可行工程路径。",
        },
    ]

    for i, p in enumerate(papers):
        top = Inches(1.0) + i * Inches(2.9)
        add_rect(s, Inches(0.35), top, Inches(12.6), Inches(2.65), CARD_BG)
        add_label(s, "论文", Inches(0.5), top + Inches(0.12), Inches(0.8), Inches(0.3),
                  COLOR, BG_DARK, 10)
        add_text(s, p["title"], Inches(1.4), top + Inches(0.1), Inches(11.2), Inches(0.42),
                 font_size=13, bold=True, color=WHITE)
        add_text(s, f"中文：{p['zh']}　　机构：{p['org']}　　arXiv：{p['arxiv']}",
                 Inches(0.5), top + Inches(0.55), Inches(12.4), Inches(0.3),
                 font_size=10, color=GRAY)
        add_text(s, f"▶ 核心贡献：{p['contrib']}",
                 Inches(0.5), top + Inches(0.88), Inches(12.4), Inches(0.65),
                 font_size=11, color=WHITE)
        add_text(s, f"✦ 关键结论：{p['key']}",
                 Inches(0.5), top + Inches(1.58), Inches(12.4), Inches(0.85),
                 font_size=11, color=COLOR)
    return s

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 5 · 生成统一 & 世界模型
# ═══════════════════════════════════════════════════════════════════════════
def slide_unified_world(prs):
    s = blank_slide(prs)
    fill_bg(s)
    add_rect(s, 0, 0, W, Inches(0.08), RGBColor(0xBB, 0x86, 0xFC))

    add_text(s, "🌐  生成统一 · 世界模型",
             Inches(0.5), Inches(0.15), Inches(12), Inches(0.7),
             font_size=28, bold=True, color=RGBColor(0xBB, 0x86, 0xFC))

    PURPLE = RGBColor(0xBB, 0x86, 0xFC)

    # Left: Unified
    add_rect(s, Inches(0.3), Inches(1.0), Inches(6.1), Inches(5.9), CARD_BG)
    add_label(s, "生成统一", Inches(0.45), Inches(1.12), Inches(1.5), Inches(0.32),
              PURPLE, BG_DARK, 10)
    add_text(s, "Omni-Diffusion",
             Inches(0.45), Inches(1.52), Inches(5.8), Inches(0.42),
             font_size=14, bold=True, color=WHITE)
    add_text(s, "Unified Multimodal Understanding and\nGeneration with Masked Discrete Diffusion",
             Inches(0.45), Inches(1.92), Inches(5.8), Inches(0.55),
             font_size=11, color=GRAY)
    add_text(s, "arXiv：2603.06577",
             Inches(0.45), Inches(2.5), Inches(5.8), Inches(0.3),
             font_size=10, color=PURPLE)
    add_text(s, "▶ 首个完全基于掩码离散扩散的任意到任意多模态语言模型，统一文本/语音/图像的理解与生成；彻底放弃自回归架构，通过掩码扩散实现并行解码。",
             Inches(0.45), Inches(2.85), Inches(5.8), Inches(1.3),
             font_size=11, color=WHITE)
    add_text(s, "✦ 离散掩码扩散可替代自回归成为统一多模态生成的底层范式，在速度与质量上兼顾。",
             Inches(0.45), Inches(4.25), Inches(5.8), Inches(0.9),
             font_size=11, color=PURPLE)

    # Right: World Model
    add_rect(s, Inches(6.6), Inches(1.0), Inches(6.4), Inches(5.9), CARD_BG)
    add_label(s, "世界模型", Inches(6.75), Inches(1.12), Inches(1.5), Inches(0.32),
              GOLD, BG_DARK, 10)
    add_text(s, "HY-World 2.0",
             Inches(6.75), Inches(1.52), Inches(6.0), Inches(0.42),
             font_size=14, bold=True, color=WHITE)
    add_text(s, "Multi-Modal World Model for Reconstructing,\nGenerating, and Simulating 3D Worlds",
             Inches(6.75), Inches(1.92), Inches(6.0), Inches(0.55),
             font_size=11, color=GRAY)
    add_text(s, "Tencent 混元  ·  arXiv 2604.14268  ·  40+ 作者",
             Inches(6.75), Inches(2.5), Inches(6.0), Inches(0.3),
             font_size=10, color=GOLD)
    add_text(s, "▶ 四阶段流水线：HY-Pano 2.0（全景生成）→ WorldNav（轨迹规划）→ WorldStereo 2.0（视频扩散场景扩展）→ WorldMirror 2.0（场景合成）；WorldLens 3DGS 渲染平台支持 IBL 光照 & 碰撞检测。",
             Inches(6.75), Inches(2.85), Inches(6.0), Inches(1.5),
             font_size=11, color=WHITE)
    add_text(s, "✦ 开源阵营 SOTA，可比肩闭源 Marble；模型权重+代码+技术细节全量开源。",
             Inches(6.75), Inches(4.42), Inches(6.0), Inches(0.7),
             font_size=11, color=GOLD)
    return s

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 6 · 行业动态
# ═══════════════════════════════════════════════════════════════════════════
def slide_industry(prs):
    s = blank_slide(prs)
    fill_bg(s)
    add_rect(s, 0, 0, W, Inches(0.08), RGBColor(0xFF, 0x6B, 0x6B))

    add_text(s, "📡  行业动态",
             Inches(0.5), Inches(0.15), Inches(12), Inches(0.7),
             font_size=28, bold=True, color=RGBColor(0xFF, 0x6B, 0x6B))

    news = [
        ("Anthropic", "Claude Opus 4.7 发布：SWE-bench Verified 87.6%，SWE-bench Pro 64.3%，CursorBench 70%；新增 xhigh effort 级别；定价维持 $5/$25 per M tokens。", ACCENT),
        ("OpenAI", "GPT-Rosalind 发布：首款专为生物学/药物发现/转化医学构建的前沿推理模型，BixBench pass@1 = 0.751，超越 GPT-5.4 / Grok 4.2 / Gemini 3.1 Pro。", RGBColor(0x10, 0xA3, 0x7F)),
        ("ByteDance", "Seedance 2.0 技术论文正式发布（arXiv:2604.14148）；Doubao 日均 token 消耗突破 120 万亿；MaaS 2026 营收目标超 RMB 100 亿。", RGBColor(0xFF, 0x6B, 0x6B)),
        ("Tencent 混元", "HY-World 2.0 全量开源，3D 世界生成能力追平闭源 Marble；模型权重+代码一并开放。", GOLD),
        ("Runway", "通过 Runway API 提供 Seedance 2.0 接入；支持关键帧控制+多模态参考输入+音频生成，生成时长 4-15 秒。", RGBColor(0xBB, 0x86, 0xFC)),
        ("中国AI综合", "GLM-5.1（MIT 协议）持续被认为最强开源 Coding 模型；MiniMax M2.7 自进化机制进入生产验证阶段；中美差距持续收窄。", GRAY),
    ]

    cols = [(Inches(0.3), Inches(6.55)), (Inches(6.85), Inches(6.1))]
    rows_per_col = 3

    for i, (org, text, color) in enumerate(news):
        col = i // rows_per_col
        row = i % rows_per_col
        left = cols[col][0]
        width = cols[col][1]
        top = Inches(1.0) + row * Inches(2.05)

        add_rect(s, left, top, width, Inches(1.88), CARD_BG)
        add_rect(s, left, top, Inches(0.07), Inches(1.88), color)
        add_text(s, org, left + Inches(0.18), top + Inches(0.1), width - Inches(0.25), Inches(0.38),
                 font_size=13, bold=True, color=color)
        add_text(s, text, left + Inches(0.18), top + Inches(0.5), width - Inches(0.25), Inches(1.28),
                 font_size=10.5, color=WHITE)
    return s

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 7 · 编辑观察
# ═══════════════════════════════════════════════════════════════════════════
def slide_editorial(prs):
    s = blank_slide(prs)
    fill_bg(s)
    add_rect(s, 0, 0, W, Inches(0.08), ACCENT)

    add_text(s, "💡  编辑观察",
             Inches(0.5), Inches(0.15), Inches(12), Inches(0.7),
             font_size=28, bold=True, color=ACCENT)

    observations = [
        ("世界模型跨维度跃迁",
         "HY-World 2.0 代表腾讯在3D世界生成的全量开源押注，WorldStereo 2.0 将视频扩散先验引入3D场景扩展——是扩散范式从2D平面走向可导航3D空间的里程碑。",
         GOLD),
        ("生成式预训练范式重写",
         "'Image Generators are Generalist Vision Learners'揭示生成训练的表征价值，预示未来大型视觉基础模型的预训练策略将从判别式全面迁移至生成式。",
         ACCENT),
        ("Agentic Coding 计量标尺升级",
         "Claude Opus 4.7 在 SWE-bench Pro 达到 64.3%，进一步确认 Agentic Coding 能力的竞争标尺已从单次任务正确率升级至复杂工程项目级别。",
         RGBColor(0xBB, 0x86, 0xFC)),
    ]

    for i, (title, body, color) in enumerate(observations):
        top = Inches(1.05) + i * Inches(2.0)
        add_rect(s, Inches(0.3), top, Inches(12.7), Inches(1.78), CARD_BG)
        add_rect(s, Inches(0.3), top, Inches(0.1), Inches(1.78), color)
        # number
        add_text(s, str(i + 1), Inches(0.5), top + Inches(0.4), Inches(0.6), Inches(0.8),
                 font_size=32, bold=True, color=color, align=PP_ALIGN.CENTER)
        add_text(s, title, Inches(1.25), top + Inches(0.18), Inches(11.5), Inches(0.45),
                 font_size=16, bold=True, color=color)
        add_text(s, body, Inches(1.25), top + Inches(0.65), Inches(11.5), Inches(1.0),
                 font_size=12, color=WHITE)

    # footer
    add_text(s, "本日报由 Claude Code + WebSearch 自动生成，数据以原始来源为准，请核实关键数字后引用。",
             Inches(0.5), Inches(7.05), Inches(12.3), Inches(0.35),
             font_size=10, color=GRAY, align=PP_ALIGN.CENTER)
    return s

# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════
def main():
    prs = new_prs()
    slide_cover(prs)
    slide_hf_top5(prs)
    slide_t2i(prs)
    slide_t2v(prs)
    slide_unified_world(prs)
    slide_industry(prs)
    slide_editorial(prs)

    out = r"c:\coding\Learning\reports\2026-04-27.pptx"
    prs.save(out)
    print(f"Saved: {out}")

if __name__ == "__main__":
    main()
