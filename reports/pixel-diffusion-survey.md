# Pixel Diffusion 多模态统一模型实现拆解与消融设计指南

> 整理时间：2026-05-15  
> 目的：把 pixel-diffusion 路线拆成**可独立改动的设计维度**，对比各家实现，为消融实验提供锚点  
> 核心样本：**HiDream-O1-Image**（HiDream AI），**Tuna-2**（Meta AI），**PixelDiT**（学术）

---

## 一、整体设计 DNA 对比表

下表是后续所有讨论的索引。每行是一个可消融的设计维度，每列是一个公开模型的具体实现选择。

| 设计维度 | HiDream-O1-Image | Tuna-2 (variant C) | PixelDiT |
|---|---|---|---|
| **Patchify 操作** | `einops.rearrange`（零参数）+ Bottleneck 双 Linear | `nn.Conv2d(stride=patch)` + RMSNorm | reshape + Linear（每像素一 token） |
| **Patch size** | **32** | **16**（默认） | **16**（patch 内再 compaction） |
| **Backbone** | Qwen3-VL-8B (vision-aware LLM) | Qwen2.5-7B (text-only LLM) | 从头训 DiT |
| **独立 Diffusion Head** | ❌ 无 | ✅ **10 层 ModulatedAttentionBlock** | ✅ **双层：Patch-DiT + Pixel-DiT** |
| **Timestep 注入** | 序列中一个特殊 `<tms_token>` | **每层 AdaLN-zero**（6-way modulation） | Patch 层 AdaLN + Pixel 层 **Pixel-wise AdaLN** |
| **输出头** | 单 Linear（零初始化） | RMSNorm + AdaLN(shift,scale) + Linear（全零初始化） | 不详（论文未细说） |
| **预测目标** | **x₀** (clean image) | **x₀** (JiT-style) | **v** (velocity) |
| **感知损失** | Flow Matching + **LPIPS + DINO** | 纯 MSE on x₀ + LM next-token | 纯 velocity MSE |
| **注意力模式** | 混合掩码（text/cond 因果，gen 全） | 标准（mask 外部传入） | 全注意力 |
| **宽高比处理** | 离散桶 snapping | **独立 `aspect_ratio_embed`**（TimestepEmbedder） | 固定方形 |
| **位置编码** | RoPE（继承 Qwen3-VL） | **3D RoPE**（自建，head_dim=64） | 2D APE |
| **理解任务掩码** | 论文未细说 | **可学 `mask_token`，ratio=0.75**（DeTok 风） | N/A（仅生成） |
| **多模态条件编码** | SigLIP-2 + Linear（编辑/参考图） | 同 patch_embed | N/A |

> **核心观察：** "Pixel Diffusion" 不是一个范式，而是一个**家族**。HiDream-O1 和 Tuna-2 都满足"像素空间"和"统一理解+生成"，但**几乎每一个设计维度的选择都不一样**。下面逐项剖析。

---

## 二、维度一：图像 → Token（Patchify）

### 2.1 HiDream-O1：零参数 rearrange + Bottleneck Linear

[pipeline.py:225](../_)

```python
PATCH_SIZE = 32

# 第一步：纯 view 操作，零参数
x = einops.rearrange(x, "C (H p1) (W p2) -> (H W) (C p1 p2)", p1=PATCH_SIZE, p2=PATCH_SIZE)
# [3, H, W] → [N_patches, 3072]

# 第二步：BottleneckPatchEmbed
class BottleneckPatchEmbed(nn.Module):
    def __init__(self, patch_size=32, in_chans=3, pca_dim=hidden//4, embed_dim=hidden):
        self.proj1 = nn.Linear(3072, hidden//4, bias=False)   # 32*32*3=3072 → 1024
        self.proj2 = nn.Linear(hidden//4, hidden, bias=True)  # 1024 → 4096
    def forward(self, x):
        return self.proj2(self.proj1(x))     # 无归一化
```

**关键特征：**
- 低秩瓶颈（hidden/4）：似 PCA 思想，省参数 + 隐式正则
- 第一层 Linear `bias=False`，第二层有 bias
- **没有 RMSNorm/LayerNorm**

### 2.2 Tuna-2：标准 ViT 风 Conv2d + RMSNorm

[`tuna/models/vision/patch_embed.py`](../_)

```python
class SimplePatchEmbedding(nn.Module):
    def __init__(self, patch_size=16, hidden_size=1152, in_channels=3):
        # 经典 ViT patchify：kernel=stride=patch_size 的 Conv2d
        self.patch_embedding = nn.Conv2d(
            in_channels=3, out_channels=hidden_size,
            kernel_size=patch_size, stride=patch_size, bias=True,
        )
        self.norm = nn.RMSNorm(hidden_size)

    def forward(self, pixel_values):
        # (B,3,H,W) → (B,hidden,H/p,W/p) → (B,N_p,hidden)
        emb = self.patch_embedding(pixel_values)
        b, c, h, w = emb.shape
        emb = emb.reshape(b, c, h*w).transpose(1, 2)
        return self.norm(emb)               # RMSNorm 是关键差异
```

**关键特征：**
- Conv2d 等价于 Linear（kernel=stride 时），但参数布局/初始化习惯不同
- **RMSNorm 在通道维**：稳定训练，HiDream-O1 没有
- 初始化用 xavier_uniform（[tuna_2_pixel.py:167](_))

### 2.3 PixelDiT：每像素一 token + 后续 compaction

```python
# X ∈ R^(B×C×H×W) → reshape + linear → R^(B×H×W×D_pix)
# 注意：是 H*W 个 token（每像素一个），不是 N_patch 个！
```

然后在 attention 前通过 **compaction**：

```
C: R^(p²×D_pix) → R^D       # 把 p×p 像素压成 1 patch token，参与 global attn
E: R^D → R^(p²×D_pix)        # attn 完再展开回 p×p 像素
```

序列长度从 $H\!\cdot\!W$ 降到 $HW/p^2$，全局注意力代价从 $O((HW)^2)$ 降到 $O((HW/p^2)^2)$，缩小 $p^4$ 倍。这是 PixelDiT 的核心 trick。

### 2.4 消融建议（维度一）

| 实验 | 预期观察 |
|---|---|
| Conv2d vs rearrange+Linear（同 patch size，同 backbone） | 等价计算下应差异很小；测训练稳定性、收敛速度 |
| Patchify 是否加 RMSNorm | 训练前期发散概率；HiDream 不加但 ConditionEmbedding 后用了 norm，需对齐 |
| Bottleneck（hidden→hidden/4→hidden）vs 单层 Linear | 参数量 vs 表达力；估计 32×32×3=3072 维度 bottleneck 几乎无损 |
| Patch 内是否做 compaction（PixelDiT 风） | 计算量 vs 细节保真；compaction 是 pixel diffusion 在 attention 代价上的核心赌注 |

---

## 三、维度二：Patch Size 的极端分歧

各家选择差异巨大，直接决定序列长度：

| 模型 | patch_size | 1024×1024 时序列长度 |
|---|---|---|
| HiDream-O1 | 32 | (1024/32)² = **1024** tokens |
| Tuna-2 | 16 | (1024/16)² = **4096** tokens |
| PixelDiT (compacted) | 16 effective (内含 256 个 pixel-token) | 4096 global + 256 inner |
| SD3 / DiT (latent) | 2 over 8x VAE | (128/2)² = 4096 tokens |

**选择逻辑：**
- HiDream-O1 patch=32：用了 hidden=4096 的大 Qwen3-VL backbone，每 token 信息密度高，3072 维 patch 喂进去不浪费
- Tuna-2 patch=16：用了 hidden=1152 的小 hidden_size，patch=16 平衡 token 数与单 token 表达力
- 共同教训：**patch_size 必须与 hidden_size 联合考虑**，patch_size² × 3 不能远超 hidden_size，否则瓶颈太严重

### 消融建议

```
patch_size ∈ {8, 16, 24, 32, 48} × hidden_size ∈ {1152, 2048, 4096}
```
画 FID vs 训练 GPU 时间二维曲线，找帕累托前沿。**HiDream patch=32 是大模型路线**，patch=16 是小模型路线。

---

## 四、维度三：Timestep 注入——三种截然不同的路线

### 4.1 HiDream-O1：占位符 token 替换（轻量、零侵入 backbone）

[qwen3_vl_transformers.py:1518-1523](../_)

```python
# 序列模板：[text..., <boi>, <tms_token>, <image_patches...>]
# 直接把 <tms_token> 位置的 embedding 换成 t_emb

t_emb = self.t_embedder1(timestep)              # 标量 → [B, hidden]
tms_mask = (input_ids == self.tms_token_id)     # 找到占位符位置
inputs_embeds = torch.where(tms_mask_3d, t_emb_expanded, inputs_embeds)
```

**优点：**
- 不改 backbone 结构，Qwen3-VL 直接复用，不引入额外参数
- 实现极简，1 个 token 表示完整 t 信息

**缺点：**
- 时间信号只在序列层面注入一次，依赖 attention 把信息传到所有生成 token
- 没有显式的"层级时间调制"

### 4.2 Tuna-2：每层 AdaLN-zero 调制（DiT 经典路线）

[modules_new_mm.py:317-403](_)

```python
class ModulatedAttentionBlock(nn.Module):
    def __init__(self, config, layer_idx):
        ...
        self.adaLN_modulation = nn.Sequential(
            nn.SiLU(),
            nn.Linear(hidden, 6 * hidden, bias=True),    # 6 个调制参数
        )
        nn.init.zeros_(self.adaLN_modulation[1].weight)  # 零初始化
        nn.init.zeros_(self.adaLN_modulation[1].bias)

    def forward(self, hidden_states, adaln_input, ...):
        # adaln_input = t_emb，每层独立产出 6 个 modulation 向量
        shift_msa, scale_msa, gate_msa, shift_mlp, scale_mlp, gate_mlp = (
            self.adaLN_modulation(adaln_input).chunk(6, dim=1)
        )

        # 只调制图像 token 位置（modality_positions 指定）
        # text token 的 shift/scale=0、gate=1，等价于 identity
        ...
```

**关键设计点：**
1. **6-way chunk**：shift+scale+gate × {attention, MLP} = 6 个向量
2. **零初始化**：训练初期等价于 identity，残差稳定
3. **modality-aware**：text token 不调制（保留 LLM 行为），只图像 token 走 AdaLN
4. **可选 `share_adaln`**：跨层共享 modulation 参数表，节省参数

### 4.3 PixelDiT：双层 AdaLN（语义 + 像素）

```
Patch-level DiT 块：标准 AdaLN（token 共享同一 shift/scale）
                ↓
Pixel-level DiT 块：Pixel-wise AdaLN
                    └→ s_cond 通过 Φ 映射到 p² 套独立调制参数
                    └→ 每个像素独立 shift/scale/gate
```

**Pixel-wise AdaLN 的核心：**

```python
# 标准 AdaLN：所有 patch 内像素共享同一组 (shift, scale)
shift, scale = Linear(t)            # [B, D]

# Pixel-wise AdaLN：每个像素独立
shift, scale = Linear(t).reshape(B, p*p, D)   # [B, p², D]
                                              # 同 patch 内的 p² 像素各自一套
```

这是 PixelDiT 报告里指出的关键消融发现："without it, FID >8; addition of pixel-wise AdaLN + compaction reduces FID to 2.36"。

### 4.4 消融建议（维度三）

| 实验 | 假设 |
|---|---|
| Token-as-timestep（HiDream） vs AdaLN-zero（Tuna-2） vs Pixel-wise AdaLN（PixelDiT） | AdaLN 路线收敛更快但参数多 6×；Token 路线参数省但需要更多步 |
| AdaLN-zero 是否真的需要 zero-init | 实验对比 zero-init vs Xavier；zero 应明显稳定 |
| `share_adaln`（跨层共享） vs 每层独立 | 大模型上预期共享几乎无损（PixArt-Σ 实验已验证），可作为参数效率消融 |
| 时间步映射方式：sinusoidal vs Fourier features vs learned | 通常差异小，但在 t-uniform vs t-logit normal 数据采样下可能放大 |

---

## 五、维度四：是否需要独立 Diffusion Head？

这是 HiDream-O1 和 Tuna-2 最大的架构哲学差异。

### 5.1 HiDream-O1 路线：backbone 直出（No Diffusion Head）

```
[文本/条件/带噪 patch tokens]
        │
        ▼  Qwen3-VL-8B Transformer（全部 36 层）
[hidden_states]
        │
        ▼  FinalLayer = nn.Linear(hidden, 32*32*3)
x_pred (clean patches)
```

**核心假设：** 大 backbone + 序列化时间条件已足够，无需"专门的扩散块"。

### 5.2 Tuna-2 路线：LLM + 独立 DiT 头串联

[tuna_2_pixel.py:129-137, 283-317](../_)

```python
# 主干（无 AdaLN，标准 Qwen2.5）
outputs = self.tuna(inputs_embeds=input_embeds, attention_mask=attn_mask)
last_hidden_states = outputs.hidden_states[-1]

# 投影到 diffusion head 维度
last_hidden_states = self.diff_proj(last_hidden_states)   # 可选 MLP

# 10 层 ModulatedAttentionBlock，每层都 AdaLN-zero
for layer in self.diffusion_head_a:        # num_diffusion_layers=10
    last_hidden_states = layer(
        hidden_states=last_hidden_states,
        adaln_input=time_embeds,
        attention_mask=diffhead_attention_mask,   # 注意：独立的 attention mask！
        rope_3d=rope_3d,
        modality_positions=modality_positions,
    )[0]

# 输出头（带 AdaLN）
x0_pred = self.diffusion_head_b(last_hidden_states, time_embeds, modality_positions)
```

**核心假设：** LLM backbone 出"理解类语义特征"，再用专门的 DiT 头把它"翻译"成像素。两段独立优化。

### 5.3 PixelDiT 路线：Patch-DiT + Pixel-DiT 双层

```
Patch-level DiT (N 层)：处理 (HW/p²) 个 patch token，标准 AdaLN
                ↓ s_N (语义)
                ↓ + t (timestep)
                = s_cond
                ↓
Pixel-level DiT (M 层)：处理 p² 个 pixel token，Pixel-wise AdaLN
                       接收 s_cond 作为唯一的条件信号
```

两段不仅串联，还**职责分离**：Patch-DiT 学语义/布局，Pixel-DiT 学纹理/细节。

### 5.4 消融建议（维度四）

| 实验 | 假设 |
|---|---|
| 把 HiDream 的 Final Linear 改成 N 层 DiT 头（Tuna 风） | 应能提升细节质量；测增多少 FID/CLIP 分 |
| Diffusion head 层数扫描 0 / 4 / 8 / 16 | 找 sweet spot；Tuna-2 选 10 是个先验 |
| Diffusion head 是否要独立的 attn mask | Tuna-2 用 `diffhead_attention_mask`；可放宽到全注意力对比 |
| Patch-DiT + Pixel-DiT 双层 vs 单层 unified | 在 256×256 小图上跑，验证 PixelDiT 的双层假设是否必要 |

---

## 六、维度五：输出预测头（Final Layer）

### 6.1 HiDream-O1：单 Linear，零初始化

[qwen3_vl_transformers.py:965-979](../_)

```python
class FinalLayer(nn.Module):
    def __init__(self, hidden_size, patch_size=32, out_channels=3):
        self.linear = nn.Linear(hidden_size, 32*32*3, bias=True)
        # 零初始化
        nn.init.zeros_(self.linear.weight)
        nn.init.constant_(self.linear.bias, 0)

    def forward(self, x, adaln_input=None):
        return self.linear(x)        # adaln_input 是僵尸参数，不用
```

### 6.2 Tuna-2：RMSNorm + AdaLN + Linear（DiT 经典 FinalLayer）

[modules_new_mm.py:1227-1261](../_)

```python
class FinalLayer(nn.Module):
    def __init__(self, hidden, patch_size, out_channels):
        self.norm_final = RMSNorm(hidden)
        self.linear = nn.Linear(hidden, patch_size*patch_size*out_channels, bias=True)
        self.adaLN_modulation = nn.Sequential(
            nn.SiLU(), nn.Linear(hidden, 2*hidden, bias=True),   # 输出 shift+scale
        )

    def forward(self, x, adaln_input, modality_positions):
        shift, scale = self.adaLN_modulation(adaln_input).chunk(2, dim=1)
        # 仅对图像 token 位置应用调制
        ...build shift_new, scale_new...
        x = modulate(self.norm_final(x), shift_new, scale_new)
        return self.linear(x)
```

全部参数零初始化（adaLN_modulation 最后一层、linear 都是 zeros）→ 训练初期完全 identity，残差稳定。

### 6.3 消融建议（维度五）

| 实验 | 假设 |
|---|---|
| Linear-only vs RMSNorm+AdaLN+Linear | AdaLN 路线在生成质量上应有 1-2 个 FID 改善；但 HiDream 选 Linear-only 是因为 backbone 已经够强 |
| FinalLayer 是否要零初始化 | 强烈建议是；非零初始化对训练前期非常不友好 |
| FinalLayer 之前是否要加单独的 LayerNorm/RMSNorm | Tuna 加了（隐含在 modulate 里），HiDream 没加；预期对训练稳定性有影响 |

---

## 七、维度六：预测目标——x₀ vs Velocity

### 7.1 现状：两家像素空间统一模型都选 x₀

**HiDream-O1：** 论文 3.2 节明确："a linear prediction head maps each output token back to the corresponding **clean image patch**"；代码变量名 `x_pred`。

**Tuna-2：** 代码注释 ([tuna_2_pixel.py:50](_))："Diffusion head learns to predict ``x0`` (clean pixels) via JiT-style noise scheduling"，loss 函数叫 `jit_x0_prediction_loss`。

**对比 PixelDiT：** "train the model with its velocity-matching loss: $L_{diff} = E[\|f_\theta(x_t,t,y) - v_t\|^2_2]$" — 预测 velocity。

### 7.2 为什么 pixel-space 偏好 x₀ 预测？

**像素值域有界 [-1, 1]**：x₀ 预测的输出值域明确，直接对应像素；velocity $v = x_1 - x_0$ 值域无界（在 [-2, 2] 内但分布更宽），网络需要学动态范围。

**LLM backbone 倾向 x₀：** Qwen 等 LLM 输出"概念性 token embedding"，让它输出"干净像素 patch"在语义上比"速度向量"更直接对齐。

**Loss surface 更平滑：** 在 t→0（接近干净）时，x₀ 预测的目标信噪比稳定；velocity 预测在 t→0 时 $v = x_1 - x_0 \approx x_1$（噪声主导），方差大。

### 7.3 数学等价性提醒

在 Rectified Flow 框架下，三种预测可以互转：
$$x_t = t x_1 + (1-t) x_0, \quad v = x_1 - x_0$$
$$x_1 = x_t + (1-t) v = \frac{x_t - (1-t)x_0}{t} \cdot \text{(给定 } x_0)$$

即给定模型输出 $\hat{x}_1$，可计算 $\hat{v} = (\hat{x}_1 - x_t)/(1-t)$；反之亦然。**模型预测谁，只影响 loss 的尺度和 gradient 方向，不改变可达解空间。**

### 7.4 消融建议（维度六）

| 实验 | 假设 |
|---|---|
| x₀ vs v vs ε 预测，同架构同数据 | 像素空间下 x₀ 应明显胜出（信噪比更稳定） |
| 不同 t 区间的 loss 加权（min-SNR, sigma-shift） | 像素空间分布更平坦，logit-normal 时间采样常被采用 |
| HiDream-O1 论文 4.2 节："we replace the Logit-Normal sampling strategy adopted in pre-training with uniform sampling in SFT" — 直接的消融线索 |

---

## 八、维度七：感知损失叠加（像素空间的"必修课"）

### 8.1 像素空间扩散为什么需要感知损失？

像素 MSE 易陷"模糊均值解"——尤其在多模态分布下，模型倾向输出多个 mode 的平均。Latent diffusion 不需要这个补丁，因为 VAE decoder 自带感知先验（KL+LPIPS 训练）。

### 8.2 现状

| 模型 | 主 loss | 感知 loss | 其他 loss |
|---|---|---|---|
| HiDream-O1 | Flow Matching (x₀ MSE 等价) | **LPIPS + DINO** | - |
| Tuna-2 | JiT x₀ MSE | ❌ 无 | + LM next-token (用于理解任务) |
| PixelDiT | velocity MSE | ❌ 无 | - |
| Simple Diffusion | 纯 MSE + EDM 加权 | ❌ 无 | 靠改 noise schedule |

**注意：** HiDream-O1 paper 只一笔带过"perceptual DINO loss"，未公开版本/权重/层。源码 inference-only，训练代码未释放。要复现需自己定。**建议起点：DINOv2 ViT-B/14，倒数第二层 feature 做 MSE。**

### 8.3 消融建议（维度七）

| 实验 | 配置 |
|---|---|
| 纯 MSE 基线 | 仅 flow matching loss |
| + LPIPS（AlexNet 路径） | 权重 0.1 起 |
| + DINOv2 feature loss | 权重 0.05 起；ViT-B vs ViT-L 对比 |
| + GAN loss（如 PatchGAN）激进路线 | 看是否优于感知 |
| **关键观察点：** 文字渲染清晰度、皮肤纹理、毛发细节——这些是模糊均值的高发区 |

---

## 九、维度八：注意力掩码模式

### 9.1 HiDream-O1：硬编码混合掩码

[qwen3_vl_transformers.py:1580-1589](../_)

```python
# token_types: 0=text/condition，1=generation
causal = torch.triu(torch.full((N,N), -inf), diagonal=1)  # 上三角因果
gen_positions = token_types[b].bool()
causal[gen_positions, :] = 0    # 生成 token 行整行解锁
```

**结果：** 文本/条件 token 是因果（保留 LLM 行为）；生成 token 是全注意力（DiT 行为）。**Hybrid Unified Attention** 是 HiDream 论文 3.3 节的核心卖点。

### 9.2 Tuna-2：mask 外部传入，可配置

[tuna_2_pixel.py:286-287](_):

```python
if diffhead_attention_mask is None:
    diffhead_attention_mask = attention_mask   # 默认与 LLM 共用
```

Tuna-2 在源码层面**没有强制混合规则**，给训练 pipeline 决定。从经验推测：训练时图像 token 之间双向，对文本/条件因果。

### 9.3 消融建议（维度八）

| 实验 | 假设 |
|---|---|
| Full vs Causal vs Hybrid（HiDream 风） | Hybrid 应在统一任务上明显胜出 |
| 是否需要 modality-specific mask | 对于纯 T2I 任务，hybrid 收益可能不显著 |
| 编辑/IP 任务下，参考图 token 之间是否双向 | 实测可能比因果好 |

---

## 十、维度九：理解任务支持（Mask Token 与多任务调度）

### 10.1 Tuna-2 的 DeTok 风掩码学习

[tuna_2_pixel.py:142-151](_):

```python
self.enable_mask_token = enable_mask_token       # 开关
self.masked_image_ratio = masked_image_ratio     # 默认 0.75
if self.enable_mask_token:
    scale = hidden_size ** -0.5
    self.mask_token = nn.Parameter(scale * torch.randn(1, 1, hidden_size))
```

训练时：随机选 75% 的图像 patch 替换为 `mask_token`，模型还得预测 x₀ → 强迫从局部像素 + 文本上下文重建全图，副作用是学到强视觉表征。

### 10.2 HiDream-O1：无显式 mask token

代码中没有掩码模块（inference repo）。论文也没强调 mask-based pretraining。HiDream-O1 的理解能力主要来自 **Qwen3-VL-8B 的预训练**，pixel diffusion 训练阶段不再单独做 mask 任务。

### 10.3 多任务采样比例

- **Tuna-2 (paper):** Stage 1 预训练，生成:理解 = **7:3**
- **HiDream-O1 (paper):** T2I + LM + MMU 联合，比例未公开
- **建议起点：** 7:3 偏生成是经验最优，理解过多会拖慢生成收敛

### 10.4 消融建议（维度九）

| 实验 | 假设 |
|---|---|
| mask_ratio ∈ {0, 0.25, 0.5, 0.75, 0.9} | 75% 是 MAE/DeTok 经验最优；过高过低都退化 |
| mask token vs zero replacement vs 截断 | 学习 token 应明显胜出 |
| 生成:理解比例 {9:1, 7:3, 5:5, 3:7} | 7:3 应在多模态 benchmark 上达到最优 |
| 理解任务是否参与扩散 loss（混 mode） vs 独立 LM loss | Tuna-2 用独立，HiDream 共享统一架构 |

---

## 十一、维度十：分辨率与宽高比策略

### 11.1 HiDream-O1：离散桶 snapping + 三阶段 progressive

```python
# pipeline.py
w, h = find_closest_resolution(width, height)   # 把任意输入 snap 到训练桶
```
预定义桶：512/1024 系列 × 8 个比例（1:1, 7:9, 9:7, 3:7, 7:3 等）。三阶段训练分辨率：**512→1024→2048**。

### 11.2 Tuna-2：独立可学的 aspect_ratio_embed

[tuna_2_pixel.py:115-116, 127-128](_):

```python
if add_aspect_ratio_embeds:
    self.aspect_ratio_embed = TimestepEmbedder(diffusion_head_hidden_size)
    self.ar_embed_proj = nn.Linear(diffusion_head_hidden_size, hidden_size)
```

宽高比被当成一个**独立的标量条件**，用和 timestep 一样的正弦+MLP 嵌入。可以支持任意比例而不是离散桶。

### 11.3 消融建议（维度十）

| 实验 | 假设 |
|---|---|
| 离散桶 vs aspect_ratio_embed | aspect_ratio_embed 应在分布外比例上明显泛化更好 |
| 三阶段 progressive vs 单阶段直接 1024 | Progressive 应明显省 30%+ 计算；HiDream 显式三段验证过 |
| Aspect ratio 注入位置：作为 token vs AdaLN 输入 | 与 timestep 注入路线绑定 |

---

## 十二、维度十一：位置编码

### 12.1 HiDream-O1：RoPE（继承自 Qwen3-VL）

```python
# 完全复用 backbone 的位置编码，无额外改动
position_ids = ...   # 标准 1D RoPE indexing
```

### 12.2 Tuna-2：3D RoPE（自建）

[tuna_2_pixel.py:382-386](_):

```python
rope_3d = build_rope(
    latent_shape=[T, h, w],         # (time, height, width)
    patch_size=16,
    attention_head_dim=64,
)
```

T=1 时退化为 2D，T>1 时支持视频。**头维度 64** 是大 LLM 中较小的选择，意味着 head 数较多。

### 12.3 消融建议（维度十一）

| 实验 | 假设 |
|---|---|
| 1D RoPE vs 2D RoPE vs 2D APE | 2D 应明显胜出对空间一致性 |
| RoPE base scaling（不同分辨率） | 在 progressive 训练下，base 需随分辨率调整避免外推问题 |

---

## 十三、消融实验设计建议（实操指南）

### 13.1 推荐的**最小复刻基线**配置

如果你要在中等规模（512×512，1B-3B 参数）验证 pixel diffusion 路线，**推荐起点**（混合 HiDream 和 Tuna-2 的优点）：

```
Backbone:           Qwen2.5-3B-Instruct 或 Qwen3-1.7B
Patchify:           Conv2d(stride=16) + RMSNorm  ← Tuna-2 风
Patch size:         16
Hidden size:        2048
Timestep:           token 替换（HiDream 风）+ FinalLayer 处 AdaLN（Tuna-2 风）
Diffusion head:     4 层 ModulatedAttentionBlock（折中 Tuna-2 的 10 层）
Output:             RMSNorm + AdaLN(shift,scale) + Linear（全零初始化）
Prediction:         x₀ (clean image)
Loss:               x₀ MSE + LPIPS(0.1) + LM next-token
Attention:          Hybrid（text 因果，gen 双向）
Aspect ratio:       aspect_ratio_embed
Position:           2D RoPE
Mask token:         enable, ratio=0.5（保守起点）
Data ratio:         7 generation : 3 understanding
Resolution:         256 → 512 progressive
```

### 13.2 推荐的**消融实验优先级**

按"信号 / 代价"比排序：

1. **预测目标（x₀ vs v）** —— 改一行 loss，影响巨大，最先做
2. **AdaLN-zero vs token-only timestep** —— 验证 backbone 是否够强
3. **感知损失叠加（LPIPS / DINO）** —— 找出像素空间模糊问题的解法
4. **Diffusion head 层数（0 / 4 / 10）** —— 决定参数预算分配
5. **Mask ratio（0 / 0.5 / 0.75）** —— 决定理解能力上限
6. **Patch size（16 vs 24 vs 32）** —— 计算-质量平衡
7. **混合注意力 vs 全 causal** —— 决定能否真正"统一"
8. **Aspect ratio 处理（桶 vs embed）** —— 决定真实场景部署的灵活性

### 13.3 推荐的**评估指标组合**

像素空间扩散需要分开测：
- **整体生成质量：** FID, CLIP-Score, T2I-CompBench（用 PartiPrompts/Geneval）
- **细节保真：** 高频内容（文字渲染 OCR 准确率，OCR-Bench-Image-Gen）、皮肤/毛发纹理（人工评分或 LPIPS@high-freq）
- **理解能力：** MMBench, MME, MMMU
- **推理代价：** 单图 256/512/1024 分辨率的 FLOPs 和 latency

### 13.4 实验流程建议

```
Phase 0  在小数据集（COCO+LAION-Pop subset）跑通基线，<= 100 GPU-day
Phase 1  做维度 1-3 的核心消融（patchify, patch_size, timestep）
Phase 2  做维度 4-6（diffusion head, output head, prediction target）
Phase 3  做维度 7-9（loss, mask, attention）
Phase 4  最优配置 scale up 到 7B+ 验证 scaling
```

---

## 十四、待回答的开放问题（论文未披露的细节）

下列细节在公开论文/代码中均缺失，建议你在消融时也作为开放问题对照实验设计：

1. **HiDream-O1 的 DINO loss：** 用哪个版本（DINOv2 / DINOv3）、哪个变体（ViT-B/L）、哪一层 feature？
2. **HiDream-O1 的训练 batch 内任务比例：** T2I/LM/MMU 三者具体多少
3. **Tuna-2 的实际生产 hidden_size 和 num_diffusion_layers：** README 提到模型权重去掉了部分层，原始配置未明
4. **是否使用 Min-SNR / Logit-Normal 时间采样：** HiDream 论文 4.2 节提到在 SFT 阶段从 Logit-Normal 切回 Uniform，但没给具体参数
5. **Tuna-2 的 image_latent_dim=16 是否真的就是 3：** 默认值可疑，需翻 config 文件

---

## 参考文献

| 论文 | 机构 | arXiv | 代码可用性 |
|------|------|-------|----------|
| HiDream-O1-Image | HiDream AI | [2605.11061](https://arxiv.org/abs/2605.11061) | 仅 inference |
| Tuna-2: Pixel Embeddings Beat Vision Encoders | Meta AI | [2604.24763](https://arxiv.org/abs/2604.24763) | **全套训练+推理** |
| Tuna (predecessor) | Meta AI | [2512.02014](https://arxiv.org/abs/2512.02014) | 同上仓库 |
| PixelDiT: Pixel-Space Diffusion Transformers | - | [2511.20645](https://arxiv.org/abs/2511.20645) | - |
| DiP: Taming Diffusion Models in Pixel Space | - | [2511.18822](https://arxiv.org/abs/2511.18822) | - |
| DINOv3 | Meta AI | [2508.10104](https://arxiv.org/abs/2508.10104) | ✅ |
| Show-o2 (Tuna 的代码基础) | - | - | ✅（Tuna 仓库内） |
