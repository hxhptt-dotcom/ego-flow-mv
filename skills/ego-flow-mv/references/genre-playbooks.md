# Genre Playbooks — 6 大高频题材一键开拍剧本库

> 收到用户具体题材需求后，直接套用对应 Playbook 的分镜节奏、出图策略、Flow 提示词骨架和避坑清单，再结合 `cinema-style-atlas.md` 注入大师风格。

---

## Playbook 1：商业棚拍广告 (`studio-ad`)
**适用**：饮品、美妆、香水、数码、咖啡、腕表、鞋服、奢侈品品牌 TVC（推荐 20–30 秒，3 镜）。

- **标准 3 镜节奏（慢起 → 渐强 → 峰终）**：
  1. **Shot 1（8–10s，悬念/质感入场）**：微距材质特写或 45° 侧逆光轮廓亮相，慢推展现材质工艺（水珠滑落 / 金属高光 / 丝绸流动），背景极简暗调或品牌色渐变。
  2. **Shot 2（8–10s，交互/体验高潮）**：中景使用场景（或手部优雅交互），动作速度比日常**慢 20%** 让观众看清质感，演员眼神看产品多于看镜头；若有主角用 Shot 1 或角色参考图 `--ref` 锁死。
  3. **Shot 3（6–8s，Hero Shot 品牌定格）**：正面或 45° 英雄镜头，产品占画面 **40–60%**，一道 sculpted key light 缓缓扫过产品表面后稳稳定格 1.5–2 秒。
- **灯光与美术铁律**：
  - 减法灯光：大柔光箱主光 + 蜂巢后侧轮廓光（深色产品必加），背景道具饱和度必须低于产品色。
  - 颜色严格收敛：品牌主色 + 中性基底（黑/白/灰），accent 色 ≤ 1 个。
- **转场**：`0.35s fade` 或 `0.5s fadeblack`（奢侈品推荐 `fadeblack` 增强呼吸感）。
- **高危避坑**：严禁每 2 秒硬切；严禁在 Flow 里生成复杂中文广告大字（需要中文标语/LOGO 落版时，Flow 留干净构图、后期叠加或纯视觉收尾）。

---

## Playbook 2：产品功能演示 (`product-demo`)
**适用**：硬件数码、智能家居、App/穿戴设备、新消费品卖点拆解（推荐 20–35 秒，3–4 镜）。

- **3 套叙事公式按需选 1**：
  - **问题-解决**：Shot 1 痛点 B-roll（暗沉、凌乱、卡顿）→ Shot 2 产品闪亮介入（干净明亮、核心功能 1 展示）→ Shot 3 丝滑解决后的美好生活结果 + Hero Shot。
  - **功能巡礼**：Shot 1 Hero Shot 亮相 + 最炸裂卖点（放第 1 位！）→ Shot 2 核心交互特写（手部操作/微距结构）→ Shot 3 差异化场景实测与收口。
  - **一天生活**：早晨第一次使用 → 白天多场景高效辅助 → 傍晚轻松收尾定格。
- **功能 → 镜头映射**：
  - 外观工艺 → `45-degree Hero Shot + slow orbit`
  - 手部交互 → `Medium close-up, steady overhead or 3/4 hand interaction, slight slow-motion`
  - 材质/精密结构 → `100mm macro dolly-in, crisp edge specular highlights`
  - 轻薄/便携 → `Clean minimalist backdrop, gentle weightless floating or effortless one-hand pick-up`
- **声音设计**：高密度清脆 Foley（磁吸咔哒声、按键轻响、细腻机械阻尼）+ 干脆现代脉冲电子/极简节奏；如需中文卖点旁白，走 `stepfun` 配音 + `stitch_mv.py --voiceover`。
- **高危避坑**：绝不能所有镜头都正面拍；每镜必须换一个角度（正面 / 45° / 俯视 / 微距），功能操作给足 3–5 秒看清。

---

## Playbook 3：动画短片 / IP 连续剧 (`animated-short`)
**适用**：皮克斯/迪士尼 3D/2D 动画、吉卜力治愈动画、赛博动漫、儿童绘本、固定 IP 系列短片（推荐 25–60 秒，3–6 镜）。

- **核心杀手锏：角色三视图 + `K1..K(N+1)` 首尾帧 Match Cut**
  1. **Step A — 先画角色身份证（Character Sheet）**：开机前先用 `gpt-imagecli` 为每个主角生成一张**与最终视频同画幅**（`16:9` 或 `9:16`）的多角度角色设定图：
     > `Character turnaround reference sheet, [16:9 landscape / 9:16 vertical], [animation style, e.g., soft Pixar 3D / hand-painted Ghibli 2D], showing front view, 3/4 view, side profile, back view, and 3 expression close-ups (happy, surprised, determined) of [detailed character description with exact colors and accessories]. Consistent proportions and exact same outfit in every view, clean neutral light-gray studio background, no text, no labels, no watermark.`
  2. **Step B — 画故事关键节点 `K1..K(N+1)`**：每张关键帧都用 `gpt-imagecli --ref <char_sheet.png>` 生成，锁死主角造型与画风！其中 `K2` 既是 Shot 1 的尾帧，也是 Shot 2 的首帧（以此类推）。
  3. **Step C — Flow 首尾帧链式生成**：在 `manifest.json` 里给每镜同时填 `"start_frame": "frames/k1.png"` 与 `"end_frame": "frames/k2.png"`（`flow_ego.py` 原生支持双帧！），视频自然完成丝滑 Match Cut 演进。
- **动画物理真实性铁律**：即使动画也要讲物理！角色开灯必须先拨动开关/拉开门；吹风时头发、衣角、草叶必须同向摆动；每句动作都按 `0-3s / 3-7s / 7-10s` 分段写清起承转合。
- **配音与拼接**：动画故事极适合温暖旁白——Flow 中只留丰富环境音+拟音+情绪配乐（`No spoken dialogue`），本地用 `stepfun` 生成叙事旁白并由 `stitch_mv.py --voiceover --orig-vol 0.75 --vo-vol 1.2` 混音。

---

## Playbook 4：好莱坞科幻 / 史诗大片 (`hollywood-scifi`)
**适用**：赛博朋克、太空歌剧、末日巨物工程、机甲怪兽、近未来概念片（推荐 25–45 秒，3–4 镜，强烈推荐 `16:9`）。

- **世界观自洽 3 条硬指标**：
  1. **非地球异化美感**：改变天空色彩（尘橙 / 冰灰 / 极夜星云）+ **巨物尺度对比**（人物占画面 `< 5%`，衬托千米高粗野主义建筑、行星发动机或巨型飞船）。
  2. **永远有漂浮粒子**：空气必须活着——每镜至少加入 1 种粒子层（酸雨细丝 / 火山灰烬 / 飘雪 / 逆光尘埃 / 数据光斑），配合 `volumetric god rays` 与 `atmospheric haze`。
  3. **不完美的真实磨损**：高科技配“低生活”或真实使用痕迹——金属拉丝划痕、锈迹、湿漉反光路面、带轻微扫描线与色差闪烁的全息投影（`holographic projection with faint scanlines and subtle chromatic aberration`），绝不做廉价塑料感！
- **标准 3 镜史诗结构**：
  1. **Shot 1（10–12s，建立世界观）**：极远景慢推或高空缓滑，展示巨构建筑/异星地貌 + 极小主角背影 + 漫天尘埃雨雾。
  2. **Shot 2（9–11s，近景冲突/科技交互）**：中近景角色（或载具/机甲）在单侧硬光或全息底光下触发关键动作，保留情绪微表情与强烈光影反差（`1:8`）。
  3. **Shot 3（9–11s，史诗高潮与余震）**：低角度仰拍宏大奇观展开/能量启动/巨物缓动，声音高潮后留 1.5 秒低频嗡鸣余韵。
- **声音设计**：深沉合成器低频铺底（CS-80 style analog drone）、巨物金属应力轰鸣、风声雨声、克制科技脉冲；避免廉价嘈杂配乐。

---

## Playbook 5：品牌 LOGO / 片头演绎 (`logo-reveal`)
**适用**：品牌发布会开场、频道片头、产品片尾 LOGO 质感演绎（推荐 5–8 秒，1 镜搞定）。

- **三阶段动态节奏（一镜走完）**：
  - `0-2s` **触发**：暗场中一道光束扫过 / 粒子从画外涌入 / 液态金属流动。
  - `2-5s` **成形**：材质在画面正中汇聚、旋转或凝固为清晰完整的几何徽标/符号（尽量基于用户提供的纯图形锚点图或先由 `gpt-imagecli` 精确生成的干净 LOGO 图作为 `end_frame` 锁死字形！）。
  - `5-7s` **确立定格**：最后一道高光沿边缘划过，画面稳稳保持 **1.5–2 秒静止展示**。
- **材质 → 品牌调性 → 音效速查**：
  - **磨砂/通透玻璃**：科技/高端 → 折射光扫过 + 清脆高频玻璃共鸣。
  - **抛光/拉丝金属**：权威/经典/汽车 → 镜面扫光缓慢旋转 + 低频金属共鸣。
  - **液态金属**：AI/变革/前沿 → 银色液滴融合凝固 + 流体声转低沉定型音。
  - **金色/数据粒子汇聚**：金融/云/盛典 → 粒子旋涡聚拢爆发微光 + 沙沙汇聚转低频重击。
  - **水墨晕染**：东方/文化/国潮 → 宣纸墨韵散开成形 + 轻柔笔触与古琴泛音。
- **关键技巧**：如果必须保证品牌文字 100% 不拼错，务必先用 `gpt-imagecli` 生成清晰无误的终版 LOGO 图并设为 Flow 的 `end_frame`（结束帧），让视频“汇聚到这张精确图”！

---

## Playbook 6：校园治愈 / 氛围 MV / 情感短片 (`healing-mv`)
**适用**：校园清新、旅拍 Vlog、情感回忆、轻音乐 MV、城市人文（推荐 18–30 秒，2–3 镜，竖屏 `9:16` 最佳）。

- **黄金出片配方**：
  - **Shot 1（10–11s，氛围定调）**：`gpt-imagecli` 生成 9:16 黄金时刻自然逆光首帧（成年人物明确年龄+自然穿搭），Flow 中写单镜慢推/微呼吸感运镜，细腻头发飘动、树影摇曳与自然微笑/乐器弹奏。
  - **Shot 2（8–10s，无缝续拍）**：开启 `"start_from_prev_last_frame": true`，自然推进至中近景特写（如低头拨弦、抬头逆光一笑、风吹发丝），拼接用 `0.25–0.3s fade` 无痕衔接。
  - **Shot 3（可选，换场升华）**：用 Shot 1 锚点图 `--ref` 生成傍晚/天台/街道新场景首帧，转场用 `0.5–0.6s fade`，配柔和收尾旋律。
- **声音设计**：原生木吉他、轻盈钢琴、树叶沙沙声、远处微弱蝉鸣/鸟叫/人声底噪；若需唱歌，写原创简短英文歌词（绝不写版权歌名/歌手名）。
