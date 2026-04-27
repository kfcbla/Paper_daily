# -*- coding: utf-8 -*-
"""Deep-insight PPT for paper daily 2026-04-27."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Palette ───────────────────────────────────────────────────────────────
BG      = RGBColor(0x0D, 0x1B, 0x2A)
CARD    = RGBColor(0x12, 0x28, 0x3E)
CARD2   = RGBColor(0x0A, 0x1E, 0x30)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
GRAY    = RGBColor(0x8A, 0x9B, 0xBB)
CYAN    = RGBColor(0x00, 0xC8, 0xFF)
GOLD    = RGBColor(0xFF, 0xC2, 0x00)
GREEN   = RGBColor(0x00, 0xFF, 0xAA)
PURPLE  = RGBColor(0xBB, 0x86, 0xFC)
RED     = RGBColor(0xFF, 0x6B, 0x6B)
ORANGE  = RGBColor(0xFF, 0x9F, 0x43)

W = Inches(13.33)
H = Inches(7.5)

GRAY    = RGBColor(0x8A, 0x9B, 0xBB)

# ── Primitives ─────────────────────────────────────────────────────────────
def prs_new():
    p = Presentation()
    p.slide_width  = W
    p.slide_height = H
    return p

def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])

def bg(slide, color=BG):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color

def rect(slide, l, t, w, h, color, alpha=None):
    s = slide.shapes.add_shape(1, l, t, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    return s

def tx(slide, text, l, t, w, h, size=14, bold=False,
       color=WHITE, align=PP_ALIGN.LEFT, wrap=True):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p  = tf.paragraphs[0]
    p.alignment = align
    r  = p.add_run()
    r.text = text
    r.font.size  = Pt(size)
    r.font.bold  = bold
    r.font.color.rgb = color
    return tb

def tx_multi(slide, lines, l, t, w, h, sizes, bolds, colors, align=PP_ALIGN.LEFT):
    """lines=[(text,), ...], sizes/bolds/colors per line"""
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, text in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = align
        p.space_before = Pt(2)
        r = p.add_run()
        r.text = text
        r.font.size  = Pt(sizes[i])
        r.font.bold  = bolds[i]
        r.font.color.rgb = colors[i]
    return tb

def tag(slide, text, l, t, color_bg, color_fg=BG, w=Inches(1.4), h=Inches(0.3)):
    rect(slide, l, t, w, h, color_bg)
    tx(slide, text, l+Inches(0.07), t+Inches(0.02), w-Inches(0.14), h,
       size=10, bold=True, color=color_fg, align=PP_ALIGN.CENTER)

def bar_top(slide, color):
    rect(slide, 0, 0, W, Inches(0.07), color)

def bar_bot(slide, color):
    rect(slide, 0, H-Inches(0.07), W, Inches(0.07), color)

def section_title(slide, text, color, icon=""):
    tx(slide, icon + "  " + text if icon else text,
       Inches(0.45), Inches(0.1), Inches(12.4), Inches(0.72),
       size=27, bold=True, color=color)

def footer(slide):
    tx(slide, "Claude Code + WebSearch  ·  2026-04-27  ·  数据以原始来源为准",
       Inches(0.4), H-Inches(0.42), Inches(12.5), Inches(0.35),
       size=9, color=GRAY, align=PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 1 · Cover
# ═══════════════════════════════════════════════════════════════════════════
def s_cover(prs):
    s = blank(prs); bg(s)
    bar_top(s, CYAN); bar_bot(s, CYAN)
    rect(s, Inches(0), Inches(2.5), W, Inches(2.55), RGBColor(0x0A,0x1A,0x2C))
    tx(s, "生成式 AI 论文深度日报", Inches(0.5), Inches(2.65), Inches(12.3), Inches(1.2),
       size=52, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    tx(s, "2026 年 4 月 27 日  ·  6 篇论文深度洞察", Inches(0.5), Inches(3.75), Inches(12.3), Inches(0.65),
       size=26, color=CYAN, align=PP_ALIGN.CENTER)
    tx(s, "Text-to-Image  ·  Text-to-Video  ·  Unified Generation  ·  World Model",
       Inches(0.5), Inches(4.42), Inches(12.3), Inches(0.5),
       size=15, color=GRAY, align=PP_ALIGN.CENTER)
    tags = [
        ("Google DeepMind", CYAN), ("ByteDance", GREEN),
        ("Tencent", GOLD), ("VITA-MLLM", PURPLE),
    ]
    step = Inches(2.8)
    for i,(lab,c) in enumerate(tags):
        tag(s, lab, Inches(1.55)+i*step, Inches(5.3), c, BG, Inches(2.4), Inches(0.36))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 2 · Overview Map (논문 목록 + 분류)
# ═══════════════════════════════════════════════════════════════════════════
def s_overview(prs):
    s = blank(prs); bg(s)
    bar_top(s, GRAY)
    section_title(s, "今日论文全景", CYAN, "")
    footer(s)

    papers = [
        ("T2I", "Image Generators are\nGeneralist Vision Learners",
         "Google DeepMind", "2604.20329", CYAN,
         "何恺明 & 谢赛宁主导\n生成=预训练范式"),
        ("T2I", "Frequency-Forcing:\nSoft Frequency Guidance",
         "独立研究者", "2604.20902", GOLD,
         "扩散频率显式引导\n低频→高频生成"),
        ("T2V", "Seedance 2.0:\nWorld Complexity",
         "ByteDance Seed", "2604.14148", GREEN,
         "DiT + Causal 3D-VAE\n音视频联合生成"),
        ("T2V", "Sparse Forcing:\nSparse Attn Diffusion Video",
         "学术联合", "2604.21221", ORANGE,
         "原生可训练稀疏注意力\n自回归扩散视频"),
        ("Unified", "Omni-Diffusion:\nMasked Discrete Diffusion",
         "VITA-MLLM", "2603.06577", PURPLE,
         "首个全离散掩码扩散\nany-to-any 多模态"),
        ("World", "HY-World 2.0:\n3D World Model",
         "Tencent 混元", "2604.14268", RED,
         "四阶段3D世界生成\n开源追平 Marble"),
    ]

    cols = 3
    cw = Inches(4.15)
    ch = Inches(2.7)
    for i, (cat, title, org, arxiv, color, note) in enumerate(papers):
        col = i % cols
        row = i // cols
        l = Inches(0.25) + col * (cw + Inches(0.14))
        t = Inches(0.9) + row * (ch + Inches(0.12))
        rect(s, l, t, cw, ch, CARD)
        rect(s, l, t, Inches(0.08), ch, color)
        tag(s, cat, l+Inches(0.18), t+Inches(0.1), color, BG, Inches(0.78), Inches(0.27))
        tx(s, arxiv, l+cw-Inches(1.3), t+Inches(0.12), Inches(1.2), Inches(0.27),
           size=9, color=color, align=PP_ALIGN.RIGHT)
        tx(s, title, l+Inches(0.18), t+Inches(0.45), cw-Inches(0.3), Inches(0.85),
           size=13, bold=True, color=WHITE)
        tx(s, org, l+Inches(0.18), t+Inches(1.35), cw-Inches(0.3), Inches(0.28),
           size=10, color=GRAY)
        tx(s, note, l+Inches(0.18), t+Inches(1.68), cw-Inches(0.3), Inches(0.88),
           size=10.5, color=color)


# ═══════════════════════════════════════════════════════════════════════════
# helper: deep paper slide (3-zone layout)
# ═══════════════════════════════════════════════════════════════════════════
def paper_slide(prs, cat, color, title, zh_title, org, arxiv,
                what_lines,    # list of str — What / Core Contribution
                how_lines,     # list of str — How / Implementation
                insight_lines, # list of str — So what / Insight
                bench_lines=None):  # optional benchmark numbers
    s = blank(prs); bg(s)
    bar_top(s, color)
    footer(s)

    # header strip
    rect(s, 0, Inches(0.07), W, Inches(0.82), CARD2)
    tag(s, cat, Inches(0.3), Inches(0.18), color, BG, Inches(0.9), Inches(0.3))
    tx(s, title, Inches(1.35), Inches(0.12), Inches(9.5), Inches(0.52),
       size=16, bold=True, color=WHITE)
    tx(s, zh_title, Inches(1.35), Inches(0.54), Inches(7.5), Inches(0.3),
       size=10, color=GRAY)
    tx(s, org, Inches(9.8), Inches(0.15), Inches(3.3), Inches(0.28),
       size=10, color=color, align=PP_ALIGN.RIGHT)
    tx(s, f"arXiv: {arxiv}", Inches(9.8), Inches(0.48), Inches(3.3), Inches(0.28),
       size=10, color=GRAY, align=PP_ALIGN.RIGHT)

    # Three columns
    col_tops = Inches(1.0)
    col_h    = Inches(5.9)

    # Col 1 · What
    rect(s, Inches(0.2), col_tops, Inches(3.9), col_h, CARD)
    rect(s, Inches(0.2), col_tops, Inches(3.9), Inches(0.38), color)
    tx(s, "WHAT · 核心贡献", Inches(0.3), col_tops+Inches(0.04), Inches(3.7), Inches(0.3),
       size=11, bold=True, color=BG, align=PP_ALIGN.CENTER)
    body = "\n".join(f"• {l}" for l in what_lines)
    tx(s, body, Inches(0.32), col_tops+Inches(0.5), Inches(3.68), col_h-Inches(0.65),
       size=11, color=WHITE)

    # Col 2 · How
    rect(s, Inches(4.3), col_tops, Inches(4.7), col_h, CARD)
    rect(s, Inches(4.3), col_tops, Inches(4.7), Inches(0.38), ORANGE)
    tx(s, "HOW · 实现方法", Inches(4.4), col_tops+Inches(0.04), Inches(4.5), Inches(0.3),
       size=11, bold=True, color=BG, align=PP_ALIGN.CENTER)
    body2 = "\n".join(f"• {l}" for l in how_lines)
    tx(s, body2, Inches(4.42), col_tops+Inches(0.5), Inches(4.48), col_h-Inches(0.65),
       size=11, color=WHITE)

    # Col 3 · Insight + Bench
    rect(s, Inches(9.2), col_tops, Inches(3.9), col_h, CARD)
    rect(s, Inches(9.2), col_tops, Inches(3.9), Inches(0.38), PURPLE)
    tx(s, "INSIGHT · 深度洞察", Inches(9.3), col_tops+Inches(0.04), Inches(3.7), Inches(0.3),
       size=11, bold=True, color=BG, align=PP_ALIGN.CENTER)
    ins_text = "\n".join(f"▶ {l}" for l in insight_lines)
    tx(s, ins_text, Inches(9.32), col_tops+Inches(0.5), Inches(3.68),
       Inches(3.0) if bench_lines else col_h-Inches(0.65),
       size=11, color=WHITE)

    if bench_lines:
        rect(s, Inches(9.2), col_tops+Inches(3.65), Inches(3.9), Inches(2.25), RGBColor(0x08,0x14,0x22))
        tx(s, "BENCHMARK", Inches(9.3), col_tops+Inches(3.72), Inches(3.7), Inches(0.28),
           size=10, bold=True, color=GOLD, align=PP_ALIGN.CENTER)
        bench_text = "\n".join(bench_lines)
        tx(s, bench_text, Inches(9.32), col_tops+Inches(4.05), Inches(3.68), Inches(1.7),
           size=10.5, color=GOLD)
    return s


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 3 · Vision Banana (T2I · Google DeepMind)
# ═══════════════════════════════════════════════════════════════════════════
def s_vision_banana(prs):
    paper_slide(
        prs,
        cat="T2I", color=CYAN,
        title="Image Generators are Generalist Vision Learners",
        zh_title="图像生成模型是通用视觉学习器  ·  Vision Banana",
        org="Google DeepMind  (何恺明 & 谢赛宁)",
        arxiv="2604.20329  ·  2026-04-22",
        what_lines=[
            "首次证明：图像生成预训练对视觉表征的作用等价于 LLM 的语言预训练",
            "仅通过轻量级指令微调即可将生成模型转化为 SOTA 通用视觉模型",
            "无需修改底层架构、无需复杂多任务设计、无需判别式预训练",
            "视觉任务输出被重新参数化为 RGB 图像，感知=生成 范式成立",
        ],
        how_lines=[
            "基础模型：Nano Banana Pro (NBP)，Google 最新 SOTA 图像生成器",
            "将视觉任务输出空间映射至 RGB 图像：分割图、深度图、法线图等均以图像形式生成",
            "指令微调：在 NBP 原始训练数据中混入极少量视觉任务数据（极低比例），不破坏生成能力",
            "深度估计：使用严格可逆幂变换 (lambda=-3) 将无界深度值映射到 [0,255] RGB 空间",
            "仅对输出格式进行指令引导，不添加任何视觉理解专用网络模块",
            "推理时：给定任务描述和输入图像，模型直接生成对应格式的输出图像",
        ],
        insight_lines=[
            "何恺明+谢赛宁联合主导，信号极强：下一代视觉基础模型预训练范式将从判别式迁移至生成式",
            "表征质量来自生成训练的隐式压力：模型必须理解场景才能生成正确像素，感知能力是副产品",
            "轻量微调可迁移意味着：未来视觉 backbone 可能不再独立训练，直接从生成模型 freeze+微调",
            "对产业影响：SAM/Depth Anything 系列的独立训练路线面临被统一底座取代的压力",
        ],
        bench_lines=[
            "分割 mIoU (Cityscapes)：0.699  vs SAM3 的 0.652 (+4.7pt)",
            "深度 delta1 (metric)：0.929  vs Depth Anything V3 的 0.918",
            "T2I GenAI-Bench：53.5% win rate vs NBP",
            "图像编辑 ImgEdit：47.8% win rate vs NBP",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 4 · Frequency-Forcing (T2I)
# ═══════════════════════════════════════════════════════════════════════════
def s_freq_forcing(prs):
    paper_slide(
        prs,
        cat="T2I", color=GOLD,
        title="Frequency-Forcing: From Scaling-as-Time to Soft Frequency Guidance",
        zh_title="频率强制：从时间维度缩放到软频率引导",
        org="独立研究者  (Weitao Du)",
        arxiv="2604.20902  ·  2026-04-21",
        what_lines=[
            "指出扩散/流匹配模型的核心缺陷：所有频率在单一同步时钟下去噪，导致频率耦合竞争",
            "提出 Frequency-Forcing：在流匹配中引入显式频率生成顺序（低频→高频）",
            "提供两种实现范式：K-Flow（硬频率约束）和 Latent Forcing（软频率引导）",
            "理论基础：谱偏置 + 扩散轨迹的逆方差谱律 预测低频比高频快几个数量级学习",
        ],
        how_lines=[
            "K-Flow：将频率缩放变量 k 重解释为流时间，在变换后的幅度空间内运行轨迹，实现硬频率约束",
            "Latent Forcing：将像素流与辅助语义 latent 流通过异步时间调度耦合，像素插值路径不变",
            "异步时间调度：latent flow 先于 pixel flow 收敛，语义结构在像素细节之前形成",
            "训练时只需在标准 flow matching 框架上添加辅助 latent 目标，无需修改采样器",
            "推理时频率引导通过 latent 约束自然施加，无额外推理开销",
            "物理基础：神经网络谱偏置 + 扩散噪声的逆方差特性 = 频率分离的自然基础",
        ],
        insight_lines=[
            "频率分离是图像生成的物理规律，强制执行它能消除梯度竞争，提升收敛稳定性",
            "Latent Forcing 的软约束思路可推广：任何有层次结构（粗糙→精细）的生成任务均可适用",
            "与 Classifier-Free Guidance 类似，本质上是引入额外信号解耦生成难度",
            "潜在影响：未来 DiT 架构可能内置频率感知的时间步调度策略",
        ],
        bench_lines=None,
    )


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 5 · Seedance 2.0 (T2V · ByteDance)
# ═══════════════════════════════════════════════════════════════════════════
def s_seedance(prs):
    paper_slide(
        prs,
        cat="T2V", color=GREEN,
        title="Seedance 2.0: Advancing Video Generation for World Complexity",
        zh_title="Seedance 2.0：推动视频生成应对复杂世界",
        org="ByteDance Seed Team",
        arxiv="2604.14148  ·  2026-04",
        what_lines=[
            "首个工业级统一多模态音视频联合生成模型，覆盖文/图/视/音四种输入模态",
            "支持多模态参考输入：最多3视频+9图像+3音频，输出4-15秒、480p/720p",
            "人体动作建模的自然度、时序一致性、物理合理性达到新高度",
            "提供 Fast 加速变体，推理速度比标准版提升显著（低延迟场景专用）",
        ],
        how_lines=[
            "DiT 骨干：解耦空间层+时间层，空间层处理视觉+文本 token (MMDiT)，时间层仅处理视觉 token",
            "Causal 3D-VAE：因果卷积架构编解码器，时空联合压缩；支持图像和视频同框训练",
            "统一任务公式：将 T2I/T2V/I2V 任务用二值掩码统一，noisy input 与条件帧拼接输入",
            "Multishot MM-RoPE：视觉 token 用 3D RoPE，文本 token 用 1D RoPE，支持多镜头生成",
            "窗口分区 3D 自注意力：时间维因果链接各帧，时间层用专用窗口注意力模块",
            "推理加速：窗口注意力 + KV cache 压缩，1080p 基准推理速度提升约 10x",
        ],
        insight_lines=[
            "Seedance 2.0 是 ByteDance 在视频生成从'单模态'到'世界级多模态'的质变标志",
            "Causal 3D-VAE + MMDiT 组合已成为业界视频生成主流架构，Sora/HunyuanVideo 同路线",
            "技术报告细节有限，但架构设计与 Seedance 1.0 一脉相承，规模+数据是核心差异",
            "音视频联合生成意味着音轨不再是后处理附加，而是从 latent 空间共同建模",
        ],
        bench_lines=[
            "Doubao 日均 token 消耗：> 120 万亿",
            "专家评测 & 公开用户测试：业内领先",
            "Runway API 接入：支持关键帧控制",
            "Fast 变体：显著提速（具体数字未公开）",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 6 · Sparse Forcing (T2V)
# ═══════════════════════════════════════════════════════════════════════════
def s_sparse_forcing(prs):
    paper_slide(
        prs,
        cat="T2V", color=ORANGE,
        title="Sparse Forcing: Native Trainable Sparse Attention for Real-time Autoregressive Diffusion Video Generation",
        zh_title="稀疏强制：实时自回归扩散视频生成的原生可训练稀疏注意力",
        org="学术联合团队 (Boxun Xu, Yuming Du et al.)",
        arxiv="2604.21221  ·  2026-04-23",
        what_lines=[
            "自回归视频扩散的核心矛盾：长视频需要长 KV cache，但密集注意力代价随序列长方增长",
            "提出 Sparse Forcing：可训练的原生稀疏注意力机制，与自回归扩散视频联合训练",
            "同时解决两大问题：1）长视频质量（减少误差累积）2）实时解码延迟（稀疏计算）",
            "关键观察：自回归扩散 rollout 中，注意力集中在持久性显著视觉块子集上",
        ],
        how_lines=[
            "核心洞察：注意力形成隐式时空记忆，在 KV cache 中呈现局部块稀疏模式",
            "持久块 (Persistent Blocks)：识别跨时间步持续被高注意力的显著块，压缩保留于 cache",
            "局部窗口约束：每个位置的计算限制在动态选择的局部邻域内，窗口内精确注意力",
            "可训练稀疏性：稀疏模式不是预定义的，而是通过端到端训练学习得到",
            "memory update：持久块在生成过程中动态压缩与更新，保持全局一致性",
            "推理时：稀疏 mask 直接应用于 KV cache，无需密集计算后再剪枝",
        ],
        insight_lines=[
            "自回归视频扩散（如 Wan、CogVideoX 等）的核心工程瓶颈正是 KV cache 爆炸问题，本文给出训练级解法",
            "与 Light Forcing（后处理稀疏化）的根本区别：Sparse Forcing 是原生训练，稀疏性是模型能力而非推理技巧",
            "持久块的发现对注意力理论有意义：视频扩散中存在类似 Sink Token 的空间显著锚点",
            "路径展望：该方法可与 Flash Attention 结合，进一步压缩实时视频生成的推理开销",
        ],
        bench_lines=None,
    )


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 7 · Omni-Diffusion (Unified)
# ═══════════════════════════════════════════════════════════════════════════
def s_omni_diffusion(prs):
    paper_slide(
        prs,
        cat="Unified", color=PURPLE,
        title="Omni-Diffusion: Unified Multimodal Understanding and Generation with Masked Discrete Diffusion",
        zh_title="Omni-Diffusion：基于掩码离散扩散的统一多模态理解与生成",
        org="VITA-MLLM Lab",
        arxiv="2603.06577  ·  2026-03-06",
        what_lines=[
            "首个完全基于掩码离散扩散（非自回归）的 any-to-any 多模态语言模型",
            "统一文本、语音、图像三种模态的理解与生成，支持超二模态任务",
            "彻底放弃自回归 token 预测，用联合掩码扩散建模多模态联合分布",
            "首次将 LLaDA 等离散扩散范式扩展至真正的多模态统一生成",
        ],
        how_lines=[
            "核心框架：统一掩码离散扩散模型直接建模多模态 token 的联合分布 p(text, speech, image)",
            "三阶段渐进训练：Stage1-单模态对齐 → Stage2-双模态对齐 → Stage3-全模态联合微调",
            "衰减尾部-填充掩码策略 (Attenuated Tail-pad Masking)：解决离散扩散变长生成问题",
            "推理创新 1：位置惩罚 (Position Penalty) 约束生成顺序、提升视觉质量",
            "推理创新 2：特殊 token 预填充策略，改善语音对话任务性能",
            "并行解码：掩码扩散天然支持非自回归并行 token 生成，速度远超自回归",
        ],
        insight_lines=[
            "离散掩码扩散是继'自回归LLM'和'连续扩散模型'之后的第三条统一路线，潜力被严重低估",
            "any-to-any 的核心是联合分布建模，自回归方法需要枚举条件方向，离散扩散天然无此限制",
            "三阶段训练策略揭示多模态对齐的课程学习思路，对未来统一模型训练具有方法论参考价值",
            "位置惩罚机制说明：无序并行解码需要显式约束防止质量退化，这是离散扩散的核心工程挑战",
        ],
        bench_lines=[
            "超越或持平现有双模态+多模态系统",
            "ASR / TTS / VQA / T2I 均有竞争力",
            "语音-图像生成 & 语音视觉理解首次覆盖",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 8 · HY-World 2.0 (World Model · Tencent)
# ═══════════════════════════════════════════════════════════════════════════
def s_hy_world(prs):
    paper_slide(
        prs,
        cat="World Model", color=RED,
        title="HY-World 2.0: A Multi-Modal World Model for Reconstructing, Generating, and Simulating 3D Worlds",
        zh_title="HY-World 2.0：用于重建/生成/仿真3D世界的多模态世界模型",
        org="Tencent HY-World Team  (40+ 作者)",
        arxiv="2604.14268  ·  2026-04-15",
        what_lines=[
            "首个开源 SOTA 3D 世界模型，四模态输入（文本/单视图图像/多视图/视频）→ 可导航 3DGS 场景",
            "四阶段流水线：全景生成→轨迹规划→场景扩展→场景合成，端到端可导航3D世界",
            "引入 WorldLens 高性能 3DGS 渲染平台：IBL 光照 + 碰撞检测 + 训练-渲染协同设计",
            "全量开源：模型权重、代码、技术细节，对标并追平闭源商业模型 Marble",
        ],
        how_lines=[
            "Stage1 · HY-Pano 2.0：以文本/图像为输入生成高保真全景图，作为3D世界的语义蓝图",
            "Stage2 · WorldNav：场景解析增强的轨迹规划算法；全景点云→网格→语义掩码→导航网格→相机轨迹",
            "Stage3 · WorldStereo 2.0：关键帧空间内的可控视频模型（而非逐帧视频生成），引入一致性记忆机制；利用视频扩散先验大幅扩展可探索空间和视觉质量",
            "Stage4 · WorldMirror 2.0：将多视图关键帧合成为完整 3DGS 表征，支持实时渲染与交互",
            "WorldLens 渲染：自动 IBL 光照估计 + 高效碰撞检测 + 训练时渲染反馈闭环",
        ],
        insight_lines=[
            "关键设计选择：WorldStereo 2.0 在'关键帧空间'而非'视频帧序列'中生成，避免了视频扩散的时序误差积累",
            "视频扩散先验被迁移至3D领域：这是扩散范式从2D像素空间到3D几何空间的里程碑式跨越",
            "全景→轨迹→多视图→3DGS 的流水线代表了'渐进式几何感知'思路，与 NeRF/MVS 的经典流程一脉相承",
            "全量开源策略表明腾讯的战略意图：通过开源建立3D世界模型标准，类比 Meta 的 Llama 策略",
        ],
        bench_lines=[
            "开源 SOTA，媲美闭源 Marble",
            "多项 benchmark 最优（开源范围内）",
            "全景 / 深度 / 新视角合成均达标",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 9 · Comparison & Trend
# ═══════════════════════════════════════════════════════════════════════════
def s_compare(prs):
    s = blank(prs); bg(s)
    bar_top(s, CYAN)
    footer(s)
    section_title(s, "横向对比  ·  今日核心趋势", CYAN)

    # Left: comparison table
    rect(s, Inches(0.2), Inches(0.9), Inches(8.0), Inches(6.1), CARD)
    tx(s, "六篇论文横向对比", Inches(0.35), Inches(0.95), Inches(7.7), Inches(0.38),
       size=13, bold=True, color=CYAN, align=PP_ALIGN.CENTER)

    headers = ["论文", "范式", "核心突破", "影响"]
    col_ws  = [Inches(2.0), Inches(1.2), Inches(2.8), Inches(1.7)]
    col_ls  = [Inches(0.25), Inches(2.28), Inches(3.5), Inches(6.32)]
    row_h   = Inches(0.38)

    # header row
    rect(s, Inches(0.2), Inches(1.35), Inches(8.0), row_h, RGBColor(0x08,0x14,0x22))
    for j, (hdr, cw, cl) in enumerate(zip(headers, col_ws, col_ls)):
        tx(s, hdr, cl, Inches(1.38), cw, row_h-Inches(0.06),
           size=10, bold=True, color=GOLD, align=PP_ALIGN.CENTER)

    rows = [
        ("Vision Banana", "T2I 生成", "生成预训练=视觉通用基础", "改变视觉backbone训练范式", CYAN),
        ("Freq-Forcing", "T2I 扩散", "频率显式引导低→高", "扩散调度新思路", GOLD),
        ("Seedance 2.0", "T2V 工业", "四模态音视频联合", "ByteDance视频旗舰", GREEN),
        ("Sparse Forcing", "T2V 效率", "原生可训稀疏注意力", "实时自回归扩散", ORANGE),
        ("Omni-Diffusion", "统一生成", "离散掩码扩散any-to-any", "第三条统一路线", PURPLE),
        ("HY-World 2.0", "世界模型", "四阶段3D世界全开源", "腾讯开源Marble级竞品", RED),
    ]
    for i, (name, paradigm, breakthrough, impact, color) in enumerate(rows):
        top = Inches(1.73) + i * row_h
        if i % 2 == 1:
            rect(s, Inches(0.2), top, Inches(8.0), row_h, RGBColor(0x0E,0x1F,0x30))
        rect(s, Inches(0.2), top, Inches(0.06), row_h, color)
        data = [name, paradigm, breakthrough, impact]
        for j, (val, cw, cl) in enumerate(zip(data, col_ws, col_ls)):
            tx(s, val, cl+Inches(0.05), top+Inches(0.06), cw-Inches(0.1), row_h-Inches(0.1),
               size=10, color=color if j==0 else WHITE)

    # Right: Trends
    rect(s, Inches(8.45), Inches(0.9), Inches(4.65), Inches(6.1), CARD)
    tx(s, "今日三大趋势信号", Inches(8.6), Inches(0.95), Inches(4.3), Inches(0.38),
       size=13, bold=True, color=PURPLE, align=PP_ALIGN.CENTER)

    trends = [
        (CYAN, "生成=预训练 范式确立",
         "Vision Banana 证明：图像生成训练=视觉通用预训练。判别式 backbone 时代即将结束，未来视觉模型从生成模型直接指令微调。"),
        (RED, "世界模型跨维度",
         "HY-World 2.0 将视频扩散先验引入3D几何空间，Sparse Forcing 攻克实时自回归视频瓶颈——世界模型从2D走向可交互3D。"),
        (ORANGE, "效率竞争白热化",
         "Sparse Forcing + Frequency-Forcing 均指向同一问题：如何在不牺牲质量的前提下让扩散/流匹配更快。下一个战场是效率。"),
    ]
    for i, (color, title, body) in enumerate(trends):
        top = Inches(1.45) + i * Inches(1.85)
        rect(s, Inches(8.55), top, Inches(4.45), Inches(1.7), RGBColor(0x08,0x14,0x22))
        rect(s, Inches(8.55), top, Inches(0.07), Inches(1.7), color)
        tx(s, title, Inches(8.73), top+Inches(0.1), Inches(4.1), Inches(0.38),
           size=12, bold=True, color=color)
        tx(s, body, Inches(8.73), top+Inches(0.52), Inches(4.1), Inches(1.1),
           size=10.5, color=WHITE)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 10 · Industry & Editorial
# ═══════════════════════════════════════════════════════════════════════════
def s_industry_editorial(prs):
    s = blank(prs); bg(s)
    bar_top(s, RED)
    footer(s)
    section_title(s, "行业动态  ·  编辑观察", RED)

    news = [
        ("Anthropic", "Claude Opus 4.7", "SWE-bench Pro 64.3%，xhigh effort，$5/$25/M tokens", CYAN),
        ("OpenAI", "GPT-Rosalind", "生物/药物发现专用推理模型，BixBench 0.751 pass@1", RGBColor(0x10,0xA3,0x7F)),
        ("ByteDance", "Doubao MaaS", "日均 Token >120万亿，2026 营收目标 RMB >100亿", GREEN),
        ("Tencent", "HY-World 2.0 开源", "3D世界模型全量开源，追平闭源 Marble", RED),
        ("Runway", "Seedance 2.0 API", "关键帧控制+多模态参考，4-15秒生成", ORANGE),
        ("中国AI", "GLM-5.1 MIT协议", "最强开源 Coding 模型之一，MiniMax M2.7 在线自进化", PURPLE),
    ]

    nw = Inches(4.1)
    for i, (org, product, desc, color) in enumerate(news):
        col = i % 3
        row = i // 3
        l = Inches(0.2) + col * (nw + Inches(0.1))
        t = Inches(1.0) + row * Inches(1.55)
        rect(s, l, t, nw, Inches(1.38), CARD)
        rect(s, l, t, Inches(0.07), Inches(1.38), color)
        tx(s, org, l+Inches(0.18), t+Inches(0.1), nw-Inches(0.25), Inches(0.3),
           size=11, bold=True, color=color)
        tx(s, product, l+Inches(0.18), t+Inches(0.42), nw-Inches(0.25), Inches(0.28),
           size=10, bold=True, color=WHITE)
        tx(s, desc, l+Inches(0.18), t+Inches(0.72), nw-Inches(0.25), Inches(0.58),
           size=9.5, color=GRAY)

    # Editorial
    rect(s, Inches(0.2), Inches(4.22), Inches(12.9), Inches(2.78), CARD2)
    tx(s, "编辑观察", Inches(0.35), Inches(4.28), Inches(3.0), Inches(0.35),
       size=13, bold=True, color=CYAN)
    obs = [
        (CYAN,   "生成式预训练将取代判别式：", "Vision Banana 是转折点信号，视觉领域的'GPT 时刻'已来临，未来视觉 backbone 预训练范式将被重写。"),
        (RED,    "3D 世界模型是下一战场：",   "HY-World 2.0 + Sparse Forcing 共同指向可导航、实时、物理合理的3D世界生成——自动驾驶/具身智能的基础设施级机会。"),
        (ORANGE, "效率是隐形主战场：",        "Frequency-Forcing / Sparse Forcing 均在攻克速度瓶颈。谁先把扩散模型跑到实时，谁就掌握 Consumer 端的部署权。"),
    ]
    for i, (color, bold_text, normal_text) in enumerate(obs):
        t = Inches(4.65) + i * Inches(0.72)
        rect(s, Inches(0.25), t, Inches(0.06), Inches(0.6), color)
        tx(s, bold_text + normal_text,
           Inches(0.42), t, Inches(12.5), Inches(0.65),
           size=11, color=WHITE)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════
def main():
    prs = prs_new()
    s_cover(prs)
    s_overview(prs)
    s_vision_banana(prs)
    s_freq_forcing(prs)
    s_seedance(prs)
    s_sparse_forcing(prs)
    s_omni_diffusion(prs)
    s_hy_world(prs)
    s_compare(prs)
    s_industry_editorial(prs)

    out = r"c:\coding\Learning\reports\2026-04-27-deep.pptx"
    prs.save(out)
    print(f"Saved: {out}  ({len(prs.slides)} slides)")

if __name__ == "__main__":
    main()
