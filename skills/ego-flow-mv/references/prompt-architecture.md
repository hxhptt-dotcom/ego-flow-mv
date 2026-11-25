# Prompt Architecture — Omni 1.2 Flash 电影级提示词手册与锁脸规范

> 本手册融合「六段式电影提示词 + 按秒卡点动作 + 摄影术语英文映射 + 角色三视图/首尾帧锁脸」，专门针对 **Google Flow (`Omni 1.2 Flash`)** 与 **`gpt-imagecli`** 优化。

---

## 1. Google Flow (`Omni 1.2 Flash`) 标准英文提示词公式

每条送入 `flow_ego.py` 的英文提示词都按以下 **6 块骨架**组装，字数控制在 **90–160 英文词**（足够精确又不稀释注意力）：

```text
In a single continuous unbroken shot, no scene cuts.
[1. Subject & Verbatim Lock] Keep the exact [subject/character/product] from the opening frame consistent throughout (brief verbatim anchor if multi-shot; do NOT over-describe static details already visible in the reference frame).
[2. Timed Motion Beats]
- 0-3s: [initial physical state + narrative emotional anchor, e.g., hesitates for a beat, slowly lifts...]
- 3-7s: [main unfolding physical action — verified physically real]
- 7-10s: [culminating beat / subtle settling pose or smooth transition toward the closing frame]
[3. Camera & Lens] [shot scale + lens mm + motivated movement, e.g., Slow deliberate dolly-in on an 85mm lens, shallow depth of field, subtle organic breathing motion.]
[4. Lighting, Color & Atmosphere] [motivated single key light + contrast + active particles, e.g., Warm golden-hour backlight with soft rim light, drifting sunlit dust motes, subtle 35mm film texture.]
[5. Audio Layer] [Ambience 60% + Foley + Music + Dialogue rule, e.g., Soft wind rustling leaves, crisp tactile Foley of fingers on wood, warm solo acoustic guitar melody. No spoken dialogue.]
[6. Hard Negative Locks] Natural realistic proportions and hands, no face drift, no morphing, no flicker, no extra limbs. No on-screen text, no subtitles.
```

---

## 2. 三大高频变体写法

### 变体 A：首尾帧 Match Cut 镜（传入 `start_frame` + `end_frame`）
适合动画短片、品牌变形、LOGO 汇聚、超现实转场：
- 在动作段明确写出**中间物理过渡路径**，并在末尾锚定终帧状态：
  `Transition smoothly and naturally from the opening composition into the exact framing and pose of the closing frame, keeping lighting continuity and physical momentum coherent throughout.`

### 变体 B：严格第一人称 POV 镜（生活流 / 穿越过山车 / 宠物视角）
弱约束会被模型无视，必须把第一人称铁律写在独立强约束句里：
- `Strict unbroken first-person POV throughout: the camera IS the viewer's eyes. The camera holder's body, shoulders, and face NEVER enter the frame; only a natural hand or forearm may briefly appear at the lower edge when interacting with objects.`

### 变体 C：多镜连续人物锁脸纪律
1. **逐字复用人物锚点句（Verbatim Reuse）**：同一人物在 Shot 1/2/3 的英文身份描述（年龄、发型、衣着颜色材质）**一字不改原样粘贴**，同义词改写是变脸第一诱因。
2. **明确成年合规词**：一律写清成年年龄（如 `21-year-old Chinese woman`, `28-year-old East Asian man`），严禁 `girl` / `teen` / `schoolgirl` / `少女` / `女孩` / `纯欲` / `性感` / `暴露`。
3. **参考图优先于文字**：已经给了 `start_frame`，不要花 50 个词重背衣服扣子和背景楼房，用 1 句 `maintaining the exact subject, outfit, and environment from the opening frame` 锁住，把词数留给运镜、动作和声音！

---

## 3. 中文导演/摄影术语 → Flow 精准英文映射表

| 中文构想 | 直接写入 Flow 提示词的精准英文 |
|---|---|
| 慢推（电影沉浸感） | `slow deliberate dolly-in toward the subject` |
| 缓拉（揭示宏大环境） | `smooth steady dolly-out revealing the expansive environment` |
| 环绕展示（产品/英雄） | `smooth slow 90-degree arc orbit around the subject` |
| 平行横移跟拍 | `smooth lateral tracking shot moving alongside the subject` |
| 呼吸感微手持 | `subtle organic handheld camera with natural human breathing` |
| 固定凝视机位 | `locked-off static tripod shot with rock-steady framing` |
| 低角度巨物仰拍 | `dramatic low-angle shot looking upward, emphasizing monumental scale` |
| 俯视桌面/顶拍 | `clean top-down overhead flat-lay perspective` |
| 升格/轻微慢动作 | `graceful slight slow-motion (60fps cinematic feel) capturing fine detail` |
| 浅景深大虚化 | `85mm lens, shallow depth of field, creamy foreground and background bokeh` |
| 丁达尔体积光 | `volumetric god rays piercing through light atmospheric haze` |
| 减法硬光轮廓光 | `sculpted single directional key light with crisp rim light separating subject from dark shadows` |
| 微距工艺特写 | `extreme macro close-up revealing fine brushed texture, specular highlights, and micro-details` |
| 韦斯安德森对称 | `strictly centered symmetrical framing, pastel curated palette, flat storybook staging` |
| 王家卫港风慢快门 | `rich warm tungsten and emerald shadows, intimate frame-within-a-frame composition, nostalgic 35mm grain` |

---

## 4. `gpt-imagecli` 关键帧与角色三视图出图公式

### 4.1 角色三视图母版（拍动画 / 多场剧情片先出这一张）
```text
Character turnaround reference sheet, [16:9 landscape / 9:16 vertical] aspect ratio, [exact art style].
Subject: [explicit adult age or stylized creature, exact hair, eyes, clothing pieces, colors, signature accessory].
Layout: clean horizontal lineup showing front view, three-quarter view, side profile, and back view, plus three small expression close-ups (warm smile, focused, surprised).
Identical proportions, outfit, and colors across every view. Plain soft neutral light-gray studio backdrop, evenly lit, ultra-crisp details, no text, no labels, no watermarks.
```

### 4.2 商业/电影/MV 首帧锚点图公式
```text
[Subject & explicit adult age / product & material], [exact pose or state], [spatial layers: soft foreground element, sharp midground hero, atmospheric background], [composition: rule of thirds / centered symmetry / low-angle], [motivated single key light + rim light + color palette], [lens & style: 85mm cinema still / commercial studio photography / Pixar-grade 3D render], [16:9 / 9:16], photorealistic / high-craft detail, no text, no subtitles, no watermarks.
```
- **换场锁脸调用**：生成 Shot 2/3 的新场景首帧时，一律传 `--ref <char_sheet_or_shot1.png>`，并在提示词开头加 `Keep the exact same person/character identity, face, and proportions from the reference image.`

---

## 5. 导演开机前 5 秒自检门禁（防废片、省点数）

在执行 `flow_ego.py batch` 之前，快速默检 5 项：
1. **单镜时长合理吗？** 每镜是否严格在 `5–12s`，按秒卡点动作是否不会在 8 秒内硬塞 6 个事件？
2. **物理真实吗？** 每个动作动词是否符合真实物理因果，无穿模/瞬移？
3. **起止护栏齐了吗？** 每条 Flow 提示词是否都以 `"In a single continuous unbroken shot, no scene cuts."` 开头，以 `"No on-screen text, no subtitles."` 结尾？
4. **合规词干净吗？** 是否清除了所有未成年/擦边敏感词以及版权歌曲名？
5. **音画路线清晰吗？** 要中文配音的镜头是否写了 `"No spoken dialogue"` 并准备好了 `stepfun` 配音；不要旁白的镜头是否写清了具体的环境音与拟音？
