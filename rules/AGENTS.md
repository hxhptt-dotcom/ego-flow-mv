# EGO Flow 一键出片全局规则 (`ego-flow-mv`)

当用户提供故事、脚本、剧情大纲、分镜或创意，并要求做成视频、MV、短片或 `.mp4` 成片时，严格遵守以下规则：

1. **先读技能与导演大脑**：立即读取 `~/.gemini/config/plugins/ego-flow-mv/skills/ego-flow-mv/SKILL.md`，并根据题材调用其 `references/`（`director-brain.md`、`genre-playbooks.md`、`cinema-style-atlas.md`、`prompt-architecture.md`）直接套用商业广告 / 产品演示 / 动画短片 / 科幻大片 / LOGO 片头 / MV 的导演拆镜节奏与按秒卡点六段式提示词，不要凭空瞎编，随后执行 `flow_ego.py` 与 `stitch_mv.py`。
2. **优先走 EGO**：一律通过用户本机已登录 Google Flow（`https://flow.google.com/`）的 `ego-browser`（由 `flow_ego.py` 封装 `.mjs` 执行）操作 Flow，不使用 Antigravity 内置受限的 `browser` 子代理，也不做任何私有 RPC 逆向或验证码/风控绕过。
3. **默认全自动出片 (`auto` 模式)**：从分镜拆解、`gpt-imagecli` 生成关键帧、`flow_ego.py batch` 批量生成并下载 `1080p` 视频、到 `stitch_mv.py` 本地 `ffmpeg` 拼接和 `ffprobe`/抽帧验片，全流程一气呵成直接交付最终 `.mp4`，不在每个镜头中间停下来请示确认。
4. **必须暂停交给用户的情况**：仅在遇到 `LOGIN_REQUIRED`（未登录）、reCAPTCHA/人机验证、点数耗尽（`PAYMENT_REQUIRED`）时立刻停下，由用户亲自处理后继续；切勿私自点击 `4K Upscaled`（50 点数/次），除非用户明确点名要 `4K`。
5. **合规与英文提示词护栏**：生成关键帧与 Flow 视频提示词时，人物年龄一律写明确成年年龄（禁用 `girl` / `teen` / `schoolgirl` / `少女` / `女孩` / `纯欲` / `性感` / `暴露` 等词）；Flow 视频提示词一律用英文写，开头加 `"In a single continuous unbroken shot, no scene cuts."`，结尾加 `"No on-screen text, no subtitles."`；如剧情需要标准中文配音，在 Flow 中写 `"No spoken dialogue"` 并在本地用 `stepfun` 配音后由 `stitch_mv.py` 混音。
