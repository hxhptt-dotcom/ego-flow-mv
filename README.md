# EGO Flow 一键出片 (`ego-flow-mv`)

Antigravity 全局插件与自动化 CLI：把**故事 / 脚本 / 分镜创意**直接丢给 AI，自动串起 **关键帧生图 (`gpt-imagecli`) -> EGO 浏览器合法驱动 Google Flow (`Omni 1.2 Flash`) -> 下载 `1080p` 分镜 -> 本地 `ffmpeg` 无缝拼接 + 混音**，端到端输出完整 `.mp4` 成片。

> 声明：本插件严格通过用户本机已登录 Google Flow（`https://flow.google.com/`）的 EGO 浏览器窗口正常交互执行，**不做任何私有 RPC 逆向，也不绕过登录或人机验证**。

## 核心特性 & 已填平的 6 个实战深坑

1. **PowerShell 引号免疫**：永远先生成 UTF-8 `.mjs` 文件，再通过 `ego-browser nodejs -e "await import('file:///...')"` 执行，彻底告别引号转义崩溃。
2. **EGO TaskSpace 无缝接管**：自动 `listTaskSpaces()` 判断 `ownership`（`user` / `agentDelegatedToUser`），按 `claimTaskSpace` / `takeOverTaskSpace` + `adopt` 复用标签，结束后在 `finally` 里调 `task.finish({ keep })` 还回控制权。
3. **选图弹窗防串图**：上传图片时拷贝为唯一随机前缀临时文件，待上传预览完成后显式点击 `[role="option"]:has-text("<唯一文件名>")` 再点 `添加到提示`，开拍前自动清理残留提示。
4. **时长滑块精确对齐**：`input[aria-label="时长"]` 为 `0..12` 映射 `3..15 秒`（`value = duration - 3`），通过聚焦发送 `ArrowLeft`/`ArrowRight` 精确步进并核对 UI 状态。
5. **`videocam` 视图卡片 diff 与 `1080p` 下载**：先切视频视图记录基线卡片数，等进度结束且卡片数 `+1` 再打开最新卡片菜单下载 `1080p`（超时自动兜底 `720p`，绝不擅自触发 50 点 `4K`）。
6. **`ffmpeg` 跨环境兼容与静音防报错**：自动探测 `libx264` 或 Windows `h264_mf`（`-b:v 18M`），对无音轨视频片段自动生成 `anullsrc` 防止 `acrossfade` 滤镜失败。

## 目录结构

```text
ego-flow-mv/
├── plugin.json
├── README.md
├── LICENSE
├── assets/logo.svg
├── rules/AGENTS.md
└── skills/ego-flow-mv/
    ├── SKILL.md
    └── scripts/
        ├── flow_ego.py
        └── stitch_mv.py
```

## 快速安装与依赖

前置条件：本机已安装 Python 3.10+、`ffmpeg`/`ffprobe`、EGO Lite（`ego-browser` 已在 `PATH` 中且在 EGO 内登录 Google Flow）。

```bash
git clone https://github.com/hxhptt-dotcom/ego-flow-mv.git ~/.gemini/config/plugins/ego-flow-mv
```

Windows PowerShell：

```powershell
git clone https://github.com/hxhptt-dotcom/ego-flow-mv.git "$env:USERPROFILE\.gemini\config\plugins\ego-flow-mv"
```

## CLI 速查

```bash
# 1. 只读检查 EGO 任务空间与已打开的 Flow 标签（不耗点数）
python skills/ego-flow-mv/scripts/flow_ego.py status --json

# 2. 单镜生成并下载 1080p
python skills/ego-flow-mv/scripts/flow_ego.py shot --start-frame frame.png --duration 11 --prompt "In a single continuous unbroken shot, no scene cuts. ... No on-screen text, no subtitles." --out shot_01.mp4 --json

# 3. 多镜全自动批跑（支持从上一镜尾帧续拍 + 结尾自动拼接）
python skills/ego-flow-mv/scripts/flow_ego.py batch --manifest manifest.json --json

# 4. 提取尾帧 / 手工拼接转场 + 配音 / BGM
python skills/ego-flow-mv/scripts/stitch_mv.py last-frame --video shot_01.mp4 --out shot_01_last.png --json
python skills/ego-flow-mv/scripts/stitch_mv.py s1.mp4 s2.mp4 --out final.mp4 --size 1080x1920 --fps 24 --transitions 0.25 --voiceover vo.mp3 --bgm bgm.mp3 --json
```
