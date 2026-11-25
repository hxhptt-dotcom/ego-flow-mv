# Director Brain — 导演 / 摄影 / 美术 / 声音一页纸决策大脑

> 当用户丢出一句话创意（如“拍个某某商业广告 / 科幻大片 / 皮克斯动画 / 治愈 MV / 品牌片头”）时，不再凭空脑补：按本页决策树瞬间定调，再调用 `genre-playbooks.md`、`cinema-style-atlas.md` 和 `prompt-architecture.md` 直接生成高水准分镜并驱动 `flow_ego.py` 出片。

---

## 1. 题材自动路由表（收到需求 3 秒定盘子）

| 用户意图关键词 | 匹配题材 (`genre-playbooks.md`) | 默认画幅 | 推荐镜数 & 单镜时长 | 锁脸 / 连贯策略 | 默认情绪曲线 |
|---|---|---|---|---|---|
| 广告 / 棚拍 / TVC / 品牌片 / 奢侈品 | `studio-ad` | `16:9` 或 `9:16` | 3 镜 × 8–10s（20–30s） | 产品/主角锚点图 `--ref` | 慢起→渐强→峰终 |
| 产品 / 演示 / 开箱 / 卖点 / 科技发布 | `product-demo` | `16:9` 或 `9:16` | 3–4 镜 × 6–9s（20–35s） | 产品主体统一图 + 多角度 | V 型（痛点→解决） |
| 动画 / 皮克斯 / 动漫 / 绘本 / IP 故事 | `animated-short` | `16:9` 或 `9:16` | 3–6 镜 × 8–10s | **角色三视图** + **首尾帧 Match Cut** | 五段弧线（Hook→Peak→Land） |
| 科幻 / 赛博 / 好莱坞 / 史诗 / 末日 / 巨物 | `hollywood-scifi` | `16:9`（宽银幕感） | 3–4 镜 × 9–12s（30–45s） | 锚点图 + 同色温粒子锁世界观 | 波浪递升（每浪高于前浪） |
| LOGO / 片头 / 品牌演绎 / 标识动效 | `logo-reveal` | `16:9` | 1 镜 × 5–8s | 纯 LOGO 锚点图居中 + 终帧锁定 | 单调能量上升→定格 1.5s |
| 治愈 / 校园 / MV / 旅拍 / 情感短片 / 剧情 | `healing-mv` | `9:16`（竖屏） | 2–3 镜 × 8–11s（18–30s） | 同景用 `start_from_prev_last_frame`；换场用 `--ref` | 温暖铺垫→微高潮→余韵 |

---

## 2. 编剧（Writer）— 叙事骨架与节奏纪律

### 6 种常用短片结构
1. **三段式（Three-Act）**：25% 建立世界与钩子 → 50% 冲突/递进 → 25% 解决与落版（适用 30s+ 剧情/品牌片）。
2. **问题-解决（Problem-Solution）**：20% 痛点 → 20% 放大 → 30% 产品介入 → 20% 爽感结果 → 10% 收口（适用产品演示/功能广告）。
3. **功能巡礼蒙太奇（Feature Tour）**：Hook 亮相 → 最打动人的卖点放第 1 位 → 差异化卖点 → 情感场景 → 落版（适用科技/消费品）。
4. **反转结构（Twist）**：40% 铺垫 → 20% 误导 → 30% 意外反转 → 10% 点题（适用病毒传播创意广告）。
5. **情绪递进（Emotional Escalation）**：30% 基础情绪 → 40% 层层叠加 → 20% 爆发 → 10% 余韵（适用治愈/公益/品牌精神片）。
6. **无对白微叙事（Show, Don't Tell）**：靠动作、表情、道具与光影讲完故事（最适配 Google Flow `Omni 1.2 Flash`，画面感染力最高）。

### 情绪锚点保留铁律（Narrative Anchor）
写英文提示词时，**绝不能把有戏的动作简化成干瘪动词**（例如把“他推开门愣住了，桌上咖啡还在冒热气”写成 `a man enters an empty room`）。必须保留情绪微动作：
- `freezes, stunned`（愣住） / `hesitates for a beat`（迟疑） / `suddenly turns`（猛然转身） / `slowly looks up`（缓缓抬头） / `hands trembling slightly`（微颤） / `exhales softly`（轻舒一口气） / `lingering gaze`（凝视）。

---

## 3. 摄影指导（DP）— 景别、焦段、运镜与布光

### 景别呼吸感原则
绝不通片同一个景别！短片至少要有 2–3 种景别交替（如 **极远景建立世界 → 中景推进动作 → 特写/微距释放情绪或材质**）：
- `Extreme Wide Shot`（极远景，人物 < 5%，建立巨物/世界观）
- `Wide / Establishing Shot`（全景，交待空间与环境）
- `Medium Shot`（中景，腰部以上，叙事与互动主力）
- `Medium Close-up`（中近景，胸部以上，捕捉表情与手势）
- `Close-up / Macro Insert`（特写/微距，眼神、手指动作、产品工艺纹理）

### 焦段选择
- **14–24mm 超广角**：强烈空间透视、巨物压迫感、科幻/建筑奇观（`ultra-wide 18mm lens, dramatic perspective`）。
- **35–50mm 标准定焦**：自然人眼视角、剧情叙事、生活感（`35mm film lens, natural depth`）。
- **50–85mm 中长焦**：人像、产品特写、柔和虚化、情感聚焦（`85mm portrait lens, shallow depth of field, creamy bokeh`）。
- **100mm Macro 微距**：金属拉丝、玻璃水珠、咖啡油脂、织物纹理（`100mm macro lens, razor-sharp texture detail`）。

### 运镜决策树（每个运镜必须有叙事动机）
- **客观凝视 / 压迫 / 精细展示** → `Static locked-off shot`（固定机位）
- **逐渐沉浸 / 紧张逼近 / 揭示主体** → `Slow deliberate dolly-in`（慢推，最有电影感）
- **孤独疏离 / 揭示宏大全貌** → `Smooth dolly-out revealing the vast environment`（缓拉）
- **展示产品/人物立体材质** → `Slow smooth 90-degree arc / orbit around subject`（环绕）
- **跟随行动 / 临场代入** → `Smooth Steadicam tracking shot`（稳跟）或 `Subtle organic handheld camera`（呼吸感微手持）
- **宏大自由 / 穿越空间** → `Sweeping aerial drone shot` / `Dynamic FPV glide`

### 减法布光铁律（最容易出电影感的秘诀）
1. **每场戏只定 1 个主光源**，且**必须有画面内的光源动机**（斜射窗光、黄金时刻低角度太阳、落地台灯、全息屏幕、头顶柔光箱），绝不乱堆无理由灯光。
2. **反差比控制**：治愈/日系/棚拍用 `1:2`–`1:4` 柔和反差；科幻/黑色电影/奢华质感用 `1:8`–`1:16` 高反差明暗对比。
3. **按材质打光**：哑光面料用大面积柔光；金属/玻璃用精确窄边高光+控反光；深色物体/黑发必加**轮廓逆光（rim light）**分离背景；透明物体用侧逆透射光。

---

## 4. 美术指导（Art Director）— 色板、空间三层与风格词库

### 情绪 → 色板与视觉成因速查
| 目标情绪 | 主色 + 辅色方向 | 直接可写的英文光影成因（Visual Cause） |
|---|---|---|
| **温暖 / 治愈 / 亲密** | 琥珀金 + 奶油白 | `warm golden-hour sunlight filtering through leaves, soft amber rim light, creamy natural highlights` |
| **压抑 / 史诗末世** | 尘橙 + 炭黑蓝 | `low-angle dusty amber light cutting through suspended haze, deep slate-blue shadows` |
| **冷峻 / 高级科技** | 钛银 + 冰蓝 + 深黑 | `cool crisp 6000K key light, brushed titanium reflections, deep dark studio backdrop` |
| **赛博 / 潮流活力** | 霓虹品红 + 电光青 + 湿黑 | `neon magenta and cyan practical reflections on rain-slicked dark asphalt, volumetric mist` |
| **奢华 / 高端广告** | 香槟金 + 曜石黑 | `dramatic low-key studio lighting, sculpted warm gold edge highlights against matte obsidian black` |
| **极简 / 苹果风科技** | 纯白/浅灰 + 单点品牌色 | `clean diffused architectural overhead lighting, pure minimalist seamless backdrop, crisp soft shadow` |
| **港风 / 怀旧文艺** | 复古绿 + 暖红琥珀 | `warm tungsten practical corridor glow, rich emerald-amber color grading, subtle 35mm film grain` |

### 空间三层布局（防止画面发平）
每个关键帧与分镜都尽量包含：
- **前景（Foreground）**：虚化的树叶/门框/玻璃反光/漂浮尘埃，制造自然景深与纵深感。
- **中景（Midground）**：主角或产品绝对视觉重心（广告产品占画面 40–60%；科幻巨物片人物 < 5%）。
- **远景（Background）**：降饱和度或大光圈虚化的环境氛围，绝不抢主体视线。

---

## 5. 声音指导（Sound Designer）— 听觉层次与静默武器

### 黄金声场配比（BR2049 法则）
**环境音 Ambience (60%) > 配乐 Music (25%) > 对白/旁白 (10%) > 关键动作拟音 Foley/SFX (5%)**。
没有环境底噪的声音是“干”的——每条 Flow 提示词都应写清具体的环境声 + 动作拟音（如咖啡机蒸汽、雨滴打窗、木地板轻响、低频电流嗡鸣、吉他拨弦）。

### 静默是情绪放大器
- **微静默（0.5–1s）**：动作转折或句间停顿，给画面呼吸。
- **冲击静默（Impact-Silence）**：巨响或爆发后骤然只剩极低环境风声/嗡鸣，高级感拉满。

### Flow 原生音轨 vs 本地 `stepfun` 中文配音决策
- **纯音乐 / 拟音 / 环境声 / 英文短吟唱 / 无对白大片**：直接交给 Google Flow `Omni 1.2 Flash` 原生生成，音画同步极佳。
- **需要字正腔圆的中文旁白 / 广告口播**：Flow 提示词写 `No spoken dialogue, crisp natural Foley and subtle ambient soundscape only.`，然后按**每 10 秒 ≤ 1 句、画面已拍出的绝不重复念**的原则写精炼旁白，用本地 `stepfun` 技能配音并交给 `stitch_mv.py --voiceover` 混音。

---

## 6. 开机前与交片前铁律（3 条零翻车守则）

1. **参考图优先于文字（Reference Image Over Text）**：人物外貌、产品外观、首帧构图已经通过 `start_frame` / `end_frame` 传给 Flow 了；Flow 视频提示词只需一句话锚定身份，把 80% 字数留给**按秒动作、运镜、光线变化、物理细节和声音**，不要啰嗦重复首帧里已经画死的东西。
2. **物理真实性自检（Physical Realism Check）**：写完每一镜动作后逐个动词核对“现实世界能这么发生吗？”——比如点灯要先打开玻璃罩再碰灯芯、喝咖啡要先抬杯再倾斜、拿手机手指自然贴合边框，杜绝穿模与反物理描写。
3. **成片必须抽帧目视验片**：永远不要没看过 `ffmpeg` 抽帧图就说“成了”；发现穿模、跳切、多手或乱码文字立刻重跑该镜。
