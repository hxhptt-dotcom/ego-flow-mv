---
name: ego-flow-mv
description: Turn a user's story, script, plot idea, or storyboard brief into a stitched 1080p MP4 video automatically end-to-end (gpt-imagecli keyframes -> EGO browser driving Google Flow Omni 1.2 Flash -> local ffmpeg xfade+acrossfade stitching). Activate whenever the user drops a story/script/brief and wants an automated MP4 output via EGO and Google Flow.
---

# EGO Flow 一键出片流水线 (`ego-flow-mv`)

把「故事 / 脚本 / 创意」一条龙变成带配乐、转场和人声的成品 `1080p` `.mp4`。全程通过你本机已登录 Google Flow（`https://flow.google.com/`）的 **EGO 浏览器 (`ego-browser`)** 驱动网页端合法操作（**绝不做私有 RPC 逆向，也不碰任何验证码/风控绕过**）。

---

## 5 步自动转动轮子 (`Story -> MP4`)

### 1. 导演拆镜 (Director Breakdown)
收到用户的故事、分镜或创意后，拆分成 `N` 个镜头（每镜 **8–12 秒**；例如 20–35 秒短片通常 2–3 镜）：
- **开篇定调镜（Shot 1）**：先用 `gpt-imagecli` 生成第 1 张高清首帧锚点图（竖屏 `--aspect 9:16 --fit 1080x1920` 或横屏 `--aspect 16:9 --fit 1920x1080`）。
- **同场景连贯续拍镜**：在 `manifest.json` 中设置 `"start_from_prev_last_frame": true`，脚本会自动提取上一镜结尾帧作为本镜首帧，拼接转场设为 `0.2s–0.3s` `fade`。
- **换场 / 换服装 / 时间跳跃镜**：用 `gpt-imagecli --ref <shot1_anchor.png> --fit 1080x1920` 以第 1 镜锚点图锁死人物五官与身份特征生成新场景首帧，拼接转场设为 `0.5s–0.7s` `fade` 或 `fadeblack`。

### 2. 提示词与画质合规护栏 (`Omni 1.2 Flash` + 安全边界)
写关键帧和 Flow 视频提示词时，严格遵守：
1. **成人肖像合规**：人物必须明确写出成年年龄与自然写实穿搭（如 `20-year-old young Chinese woman`、`22-year-old young Chinese man`），严禁出现 `girl` / `teen` / `schoolgirl` / `少女` / `女孩` / `纯欲` / `性感` / `暴露` 等高危触发词。
2. **Flow 全英文单镜防跳切提示词**：
   - 开头固定加：`"In a single continuous unbroken shot, no scene cuts."`
   - 结尾固定加：`"No on-screen text, no subtitles."`
3. **音频与语种策略**：
   - `Omni 1.2 Flash` 对**英文歌唱 / 轻哼 / 环境音效 / 原声吉他 BGM**效果极佳；写原创英文短歌词，不要出现受版权保护的歌名或歌手名。
   - 若用户明确需要**纯正标准中文配音 / 旁白**：Flow 提示词中写 `"No spoken dialogue, natural ambient sound and soft instrumental music."`，同时在本地调用 `stepfun` 技能生成高清中文配音，再传给 `manifest.json` 的 `"voiceover"` 或 `stitch_mv.py --voiceover`。

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
