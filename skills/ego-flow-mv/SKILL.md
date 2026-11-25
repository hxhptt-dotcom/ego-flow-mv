---
name: ego-flow-mv
description: Turn a user's story, commercial brief, product pitch, sci-fi concept, animation idea, or logo reveal into a stitched 1080p MP4 video automatically end-to-end using built-in director playbooks, a 38-case cinema/ad style atlas, timed six-part prompts, gpt-imagecli keyframes/character sheets, EGO browser driving Google Flow Omni 1.2 Flash, and local ffmpeg xfade+acrossfade stitching.
---

# EGO Flow 一键出片流水线 (`ego-flow-mv`)

把「商业广告 / 产品演示 / 好莱坞科幻 / 动画短片 / LOGO 片头 / 校园治愈 MV」一句话创意一条龙变成带配乐、转场和人声的成品 `1080p` `.mp4`。全程通过你本机已登录 Google Flow（`https://flow.google.com/`）的 **EGO 浏览器 (`ego-browser`)** 驱动网页端合法操作（**绝不做私有 RPC 逆向，也不碰任何验证码/风控绕过**）。

---

## 内置导演大脑与灵感参考库 (`references/`)
接到创作需求时，按题材直接读取对应参考文档定调，无需凭空脑补：
- [references/director-brain.md](references/director-brain.md)：3 秒题材路由表 + 编剧 / 摄影（景别、焦段、减法布光）/ 美术 / 声音（60% 环境音 + 静默武器）一页纸决策大脑。
- [references/genre-playbooks.md](references/genre-playbooks.md)：6 大高频题材一键开拍剧本库（商业棚拍广告、产品演示、皮克斯风动画短片、好莱坞科幻大片、品牌 LOGO 片头、治愈系 MV）。
- [references/cinema-style-atlas.md](references/cinema-style-atlas.md)：38 个影史大片与殿堂级广告（如 *BR2049*、*Apple*、*Pixar*、*Chanel*、*花样年华*）的现成技法与英文关键词速查。
- [references/prompt-architecture.md](references/prompt-architecture.md)：Google Flow `Omni 1.2 Flash` 按秒卡点六段式英文提示词模板、第一人称 POV 锁、角色三视图公式与开机前 5 秒自检门禁。

---

## 5 步自动转动轮子 (`Idea -> MP4`)

### 1. 导演定调与拆镜 (Director Breakdown)
收到用户的一句话创意、广告需求或完整剧本后，先查 `references/director-brain.md`、`references/genre-playbooks.md` 与 `references/cinema-style-atlas.md` 锁定画幅、镜数（每镜 **5–12 秒**）、主光源动机、色板与声音路线：
- **开篇定调镜（Shot 1）**：先用 `gpt-imagecli` 生成第 1 张高清首帧锚点图（竖屏 `--aspect 9:16 --fit 1080x1920` 或横屏 `--aspect 16:9 --fit 1920x1080`）。
- **动画短片 / 固定 IP 连续剧**：先用 `gpt-imagecli` 生成同画幅**角色三视图母版（Character Sheet）**，再用 `--ref` 画出故事节点关键帧 `K1..K(N+1)`，在 `manifest.json` 中同时传 `"start_frame"` 和 `"end_frame"` 让 Flow 做丝滑 **Match Cut**。
- **同场景连贯续拍镜**：在 `manifest.json` 中设置 `"start_from_prev_last_frame": true`，脚本会自动提取上一镜结尾帧作为本镜首帧，拼接转场设为 `0.25s–0.3s` `fade`。
- **换场 / 换服装 / 时间跳跃镜**：用 `gpt-imagecli --ref <char_sheet_or_shot1.png>` 以第 1 镜锚点图锁死人物五官或产品外观生成新场景首帧，拼接转场设为 `0.5s–0.7s` `fade` 或 `fadeblack`。

### 2. 提示词与画质合规护栏 (`Omni 1.2 Flash` + 导演自检)
严格按 `references/prompt-architecture.md` 组装提示词并在开机前过 5 秒门禁：
1. **成人肖像合规**：人物必须明确写出成年年龄与自然写实穿搭（如 `21-year-old Chinese woman`、`28-year-old East Asian man`），严禁出现 `girl` / `teen` / `schoolgirl` / `少女` / `女孩` / `纯欲` / `性感` / `暴露` 等高危触发词。
2. **六段式按秒卡点 + 首尾锁死**：
   - 开头固定加：`"In a single continuous unbroken shot, no scene cuts."`
   - 动作按 `0-3s / 3-7s / 7-10s` 分段写清物理真实因果，保留情绪微动作（*freezes, hesitates, slowly lifts*），并遵循**参考图优先于文字**（不啰嗦复述首帧静态细节，多镜同一人物描述逐字复用）。
   - 结尾固定加：`"No on-screen text, no subtitles."`
3. **音频与语种策略**：
   - `Omni 1.2 Flash` 优先写清具体**环境音（60%）+ 动作拟音 Foley + 情绪配乐**，对英文短吟唱 / 原声乐器 / 无对白大片效果极佳；不要出现受版权保护的歌名或歌手名。
   - 若用户明确需要**纯正标准中文配音 / 广告口播 / 旁白**：Flow 提示词中写 `"No spoken dialogue, crisp natural Foley and ambient soundscape only."`，按每 10 秒 ≤ 1 句写精炼旁白并用本地 `stepfun` 技能配音，再传给 `manifest.json` 的 `"voiceover"` 或 `stitch_mv.py --voiceover`。

### 3. 一键批量跑片 (`flow_ego.py batch`)
在工作区输出目录写好 `manifest.json`：

```json
{
  "project_title": "Story-MV-Auto",
  "project_url": null,
  "space_name": "ego-flow-studio",
  "aspect": "9:16",
  "res": "720p",
  "dl_res": "1080p",
  "fps": 24,
  "size": "1080x1920",
  "transitions": "0.25,0.6",
  "transition_types": "fade,fadeblack",
  "final_out": "final_mv.mp4",
  "shots": [
    {
      "id": "shot_01",
      "start_frame": "frames/shot_01.png",
      "duration": 11,
      "prompt": "In a single continuous unbroken shot, no scene cuts. ... No on-screen text, no subtitles.",
      "out": "shots/shot_01.mp4"
    },
    {
      "id": "shot_02",
      "start_from_prev_last_frame": true,
      "duration": 8,
      "prompt": "In a single continuous unbroken shot, no scene cuts. ... No on-screen text, no subtitles.",
      "out": "shots/shot_02.mp4"
    }
  ]
}
```

直接执行一条命令跑完 EGO 操控 -> Flow 生成 -> `1080p` 下载 -> 本地拼接（支持 `--resume` 断点续跑；`<SKILL_DIR>` 为本 `SKILL.md` 所在目录，如 Antigravity 的 `~/.gemini/config/plugins/ego-flow-mv/skills/ego-flow-mv` 或 Codex/Claude/DSH/OpenCode 的各自 `skills/ego-flow-mv`）：

```bash
python "<SKILL_DIR>/scripts/flow_ego.py" batch --manifest manifest.json --json
```

### 4. 已内置封装的 EGO + Flow 实战避坑逻辑
无需每次重复手搓 `.mjs`，`flow_ego.py` 与 `stitch_mv.py` 已内置以下 6 项修复：
1. **PowerShell 引号安全**：永远先写 UTF-8 `.mjs` 文件再通过 `ego-browser nodejs -e "await import('file:///...')"` 加载。
2. **TaskSpace 接管与释放**：自动 `listTaskSpaces()` 判断 `"user"` / `"agentDelegatedToUser"`，用 `claimTaskSpace` / `takeOverTaskSpace` + `adopt`，结束自动在 `finally` 里调 `task.finish({ keep })`。
3. **选图弹窗防串图**：每次上传把参考图拷成唯一前缀临时文件名，上传完等待“正在上传/正在加载预览”消失后，显式点击 `[role="option"]:has-text("<唯一文件名>")` 再点 `添加到提示`（并且开拍前自动点 `清除提示` 清空残留）。
4. **时长滑块 0-based 偏移与按键触发**：`input[aria-label="时长"]` 范围 `0..12` 对应 `3..15 秒`（`value = duration - 3`），通过聚焦发 `ArrowLeft`/`ArrowRight` 精确步进并核对触发器显示文本。
5. **局部作用域避开导航栏重名与精准识别新成片**：先切 `videocam` 视频视图记录基线卡片数，轮询至进度消失且卡片数 `+1`，选最左上角最新卡片点 `more_vert -> 下载 -> 1080p`（超时自动兜底 `720p`，绝不擅自点 `4K` 扣 50 点）。
6. **`ffmpeg` 兼容与静音防崩溃**：无 `libx264` 时自动选用 Windows `h264_mf`（`-b:v 18M`），对无音轨镜头自动补 `anullsrc` 防止 `acrossfade` 报错。

### 5. 成片验片交付
1. 检查 `flow_ego.py batch` 返回的 `"probe"` 元数据（分辨率、帧率、音轨、总时长）。
2. 用 `ffmpeg` 从最终 `.mp4` 抽 2–3 张关键帧图片并通过 `read_file` 目视确认画质与无文字水印后，将最终 `.mp4` 可点击链接交回用户。

---

## 单镜 / 拼接独立命令速查

```bash
# 查看 EGO 当前空间与已打开的 Flow 标签（只读，不耗点数）
python flow_ego.py status --json

# 单独生成并下载 1 个镜头
python flow_ego.py shot --start-frame a.png --duration 11 --prompt "In a single continuous unbroken shot, ..." --out shot_01.mp4 --json

# 提取某镜尾帧
python stitch_mv.py last-frame --video shot_01.mp4 --out shot_01_last.png --json

# 手工拼接多镜 + 可选配音与 BGM
python stitch_mv.py s1.mp4 s2.mp4 s3.mp4 --out final.mp4 --size 1080x1920 --fps 24 --transitions 0.25,0.6 --voiceover vo.mp3 --bgm bgm.mp3 --json
```
