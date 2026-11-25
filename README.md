# EGO Flow 一键出片 (`ego-flow-mv`)

**简体中文** | **[English](./README.en.md)**

Antigravity 全局插件与多 Agent 通用自动化 Skill：把**故事 / 脚本 / 分镜创意**直接丢给 AI，自动串起 **关键帧生图 (`gpt-imagecli`) -> EGO 浏览器合法驱动 Google Flow (`Omni 1.2 Flash`) -> 下载 `1080p` 分镜 -> 本地 `ffmpeg` 无缝拼接 + 混音**，端到端输出完整 `.mp4` 成片。

> 声明：本项目严格通过用户本机已登录 Google Flow（`https://flow.google.com/`）的 EGO 浏览器窗口正常交互执行，**不做任何私有 RPC 逆向，也不绕过登录或人机验证**。

## 🚀 一句话无脑安装（直接复制发给你的 AI Agent）

右上角点复制，直接发给你正在用的 **Antigravity / Codex / Claude Code / DSH / OpenCode**，它会自动帮你装好并自检：

### 方式 A：单 Agent 自适应口令（发给任意一个 Agent 即可）

```text
请帮我安装 https://github.com/hxhptt-dotcom/ego-flow-mv ：如果你是 Antigravity，请直接 git clone 到 ~/.gemini/config/plugins/ego-flow-mv 作为全局插件；如果你是 Codex、Claude Code、DSH 或 OpenCode，请拉取该仓库并将里面的 skills/ego-flow-mv 复制到你自己的全局 skills 目录（Codex: ~/.codex/skills/ego-flow-mv ，Claude Code: ~/.claude/skills/ego-flow-mv ，DSH: ~/.dsh/skills/ego-flow-mv ，OpenCode: ~/.config/opencode/skills/ego-flow-mv），装完运行 python scripts/flow_ego.py --help 验证安装成功。
```

### 方式 B：全家桶一键通装口令（本机装了多个 Agent 时，一句全同步）

```text
请帮我把 https://github.com/hxhptt-dotcom/ego-flow-mv 一键部署到本机所有已安装的 AI Agent：先克隆或更新到 ~/.gemini/config/plugins/ego-flow-mv（Antigravity 全局插件），再自动检测本机存在的 ~/.codex/skills、~/.claude/skills、~/.dsh/skills、~/.config/opencode/skills、~/.agents/skills 目录，把 skills/ego-flow-mv 同步进去，最后跑一次 flow_ego.py --help 检查环境（Python / ffmpeg / ego-browser）是否就绪。
```

### 各家 Agent 默认安装路径速查

| Agent | 安装形态 | 目标路径 |
| --- | --- | --- |
| **Antigravity** | 完整全局插件 | `~/.gemini/config/plugins/ego-flow-mv` |
| **Codex** | Skill 目录 | `~/.codex/skills/ego-flow-mv` |
| **Claude Code** | Skill 目录 | `~/.claude/skills/ego-flow-mv` |
| **DSH** | Skill 目录 | `~/.dsh/skills/ego-flow-mv` |
| **OpenCode** | Skill 目录 | `~/.config/opencode/skills/ego-flow-mv` |

---

## 🧠 v1.1.0 内置「导演大脑 + 38 案例技法图谱」（不用再靠 AI 硬脑补）

现在只需丢给 Agent 一句话（例如：**“按苹果风拍个耳机广告”**、**“按银翼杀手 2049 拍个科幻大片”**、**“拍个皮克斯治愈动画短片”**），插件会自动翻开内置参考库定好景别、焦段、减法布光、按秒卡点动作和声场配比：

1. **[director-brain.md](skills/ego-flow-mv/references/director-brain.md)**：3 秒题材自动路由表 + 编剧/摄影/美术/声音决策规则（60% 环境音 + 静默武器 + 物理真实性自检）。
2. **[genre-playbooks.md](skills/ego-flow-mv/references/genre-playbooks.md)**：6 大高频题材一键开拍剧本（棚拍广告 `studio-ad` / 产品演示 `product-demo` / 角色三视图+首尾帧 Match Cut 动画 `animated-short` / 科幻大片 `hollywood-scifi` / 品牌片头 `logo-reveal` / 治愈 MV `healing-mv`）。
3. **[cinema-style-atlas.md](skills/ego-flow-mv/references/cinema-style-atlas.md)**：浓缩 38 部影史与殿堂级广告（*BR2049*、*流浪地球*、*Apple*、*Pixar*、*Chanel*、*花样年华* 等）的现成镜头语言与英文视觉关键词。
4. **[prompt-architecture.md](skills/ego-flow-mv/references/prompt-architecture.md)**：专治跳切与变脸的 Google Flow `Omni 1.2 Flash` 按秒卡点六段式模板 + 人物逐字锚定规范。

---

## 核心特性 & 已填平的 6 个实战深坑

1. **PowerShell 引号免疫**：永远先生成 UTF-8 `.mjs` 文件，再通过 `ego-browser nodejs -e "await import('file:///...')"` 执行，彻底告别引号转义崩溃。
2. **EGO TaskSpace 无缝接管**：自动 `listTaskSpaces()` 判断 `ownership`（`user` / `agentDelegatedToUser`），按 `claimTaskSpace` / `takeOverTaskSpace` + `adopt` 复用标签，结束后在 `finally` 里调 `task.finish({ keep })` 还回控制权。
3. **选图弹窗防串图**：上传图片时拷贝为短前缀唯一文件（`sf_<hex>` 避免截断），待上传预览完成后显式点击 `.cdk-overlay-pane [role="option"]` 并兼容选后自动关闭弹窗，开拍前自动清理残留提示。
4. **时长滑块精确对齐**：`input[aria-label="时长"]` 为 `0..12` 映射 `3..15 秒`（`value = duration - 3`），通过聚焦发送 `ArrowLeft`/`ArrowRight` 精确步进并核对 UI 状态。
5. **`videocam` 视图卡片 diff 与 `1080p` 下载**：先切视频视图过滤掉加载占位与重复图标准确数基线卡片，等进度结束且卡片数 `+1` 再以单对象参数坐标定位最新卡片菜单下载 `1080p`（超时自动兜底 `720p`，绝不擅自触发 50 点 `4K`）。
6. **`ffmpeg` 跨环境兼容与静音防报错**：自动探测 `libx264` 或 Windows `h264_mf`（`-b:v 18M`），对无音轨视频片段自动生成 `anullsrc` 防止 `acrossfade` 滤镜失败。

## 目录结构

```text
ego-flow-mv/
├── plugin.json
├── README.md
├── README.en.md
├── LICENSE
├── assets/logo.svg
├── rules/AGENTS.md
└── skills/ego-flow-mv/
    ├── SKILL.md
    ├── references/
    │   ├── director-brain.md
    │   ├── genre-playbooks.md
    │   ├── cinema-style-atlas.md
    │   └── prompt-architecture.md
    └── scripts/
        ├── flow_ego.py
        └── stitch_mv.py
```

## 手动命令行安装与前置依赖

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

## 致谢（Open-Source Acknowledgements）

本项目的导演工作流、六段式按秒提示词规范及部分题材参考思想吸收了以下 MIT 开源项目的优秀实践并针对 Google Flow + EGO 做了全自动化改造：

- [masonmosen/muse-video-prompt-skill](https://github.com/masonmosen/muse-video-prompt-skill)（六段式按秒提示词与人物描述逐字复用纪律）
- [sonlovinbot-team/Muse-animated-short-film](https://github.com/sonlovinbot-team/Muse-animated-short-film)（角色三视图母版、`K1..K(N+1)` Match Cut 衔接与物理真实性校验）
- [LuoJiangYong/muse-video-skill](https://github.com/LuoJiangYong/muse-video-skill)（多角色虚拟剧组视角、38 案例技法索引及「参考图优先于文字」原则）
