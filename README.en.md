# EGO Flow Story-to-MP4 (`ego-flow-mv`)

**[简体中文](./README.md)** | **English**

An Antigravity global plugin and multi-agent automation skill/CLI that turns a **story, script, or storyboard idea** directly into a finished **`1080p` `.mp4`** video end-to-end: **keyframe generation (`gpt-imagecli`) -> EGO Browser driving Google Flow (`Omni 1.2 Flash`) -> `1080p` clip download -> local `ffmpeg` seamless `xfade` + audio stitching**.

> Notice: This project operates strictly through your legitimately signed-in Google Flow (`https://flow.google.com/`) session inside EGO Browser. **No private RPC reverse-engineering and no auth or CAPTCHA bypasses.**

## 🚀 Zero-Friction Install (Copy & Paste One Sentence to Your AI Agent)

Click the copy icon on either block below and send it straight to **Antigravity / Codex / Claude Code / DSH / OpenCode** — your agent will install and verify everything automatically:

### Option A: Single-Agent Auto-Detect Prompt (Works for Any Agent)

```text
Please install https://github.com/hxhptt-dotcom/ego-flow-mv for me: if you are Antigravity, git clone it directly to ~/.gemini/config/plugins/ego-flow-mv as a global plugin; if you are Codex, Claude Code, DSH, or OpenCode, clone or fetch the repo and copy skills/ego-flow-mv into your own global skills directory (Codex: ~/.codex/skills/ego-flow-mv, Claude Code: ~/.claude/skills/ego-flow-mv, DSH: ~/.dsh/skills/ego-flow-mv, OpenCode: ~/.config/opencode/skills/ego-flow-mv), then run python scripts/flow_ego.py --help to verify the setup.
```

### Option B: Install Across All Local Agents at Once

```text
Please deploy https://github.com/hxhptt-dotcom/ego-flow-mv to every AI coding agent installed on my machine: first clone or update ~/.gemini/config/plugins/ego-flow-mv (Antigravity global plugin), then detect which of ~/.codex/skills, ~/.claude/skills, ~/.dsh/skills, ~/.config/opencode/skills, and ~/.agents/skills exist locally and sync skills/ego-flow-mv into each of them, and finally run python scripts/flow_ego.py --help to verify Python, ffmpeg, and ego-browser are ready.
```

### Default Target Paths by Agent

| Agent | Format | Target Path |
| --- | --- | --- |
| **Antigravity** | Full Global Plugin | `~/.gemini/config/plugins/ego-flow-mv` |
| **Codex** | Skill Directory | `~/.codex/skills/ego-flow-mv` |
| **Claude Code** | Skill Directory | `~/.claude/skills/ego-flow-mv` |
| **DSH** | Skill Directory | `~/.dsh/skills/ego-flow-mv` |
| **OpenCode** | Skill Directory | `~/.config/opencode/skills/ego-flow-mv` |

---

## Key Features & 6 Battle-Tested EGO + Google Flow Pitfalls Solved

1. **PowerShell Quote Immunity**: Always writes a UTF-8 `.mjs` file first and executes `ego-browser nodejs -e "await import('file:///...')"`, completely eliminating Windows shell quoting failures.
2. **EGO TaskSpace Ownership & Clean Hand-Back**: Calls `listTaskSpaces()` and handles `user` / `agentDelegatedToUser` states via `claimTaskSpace` / `takeOverTaskSpace` + `adopt`, then releases control cleanly in a `finally` block via `task.finish({ keep })`.
3. **Unambiguous Frame Picker Selection**: Stages each uploaded frame under a unique randomized filename prefix, waits for upload/preview indicators to clear, and explicitly clicks `[role="option"]:has-text("<unique_filename>")` before `Add to prompt` (also clears stuck composer prompts before each shot).
4. **Zero-Indexed Duration Slider Stepping**: Google Flow's duration slider maps `0..12` to `3s..15s` (`value = duration - 3`) and ignores raw `.value` assignment; `flow_ego.py` focuses the slider and steps with `ArrowLeft` / `ArrowRight` while verifying the trigger readout.
5. **Scoped Settings Selectors & `1080p` Download Diffing**: Avoids sidebar `Videos` nav collisions, switches to the `videocam` view, snapshots baseline video card count before generation, and downloads the newest leftmost card at `1080p` (with automatic `720p` fallback on timeout; never auto-triggers 50-credit `4K` upscales).
6. **Cross-Platform `ffmpeg` & Silent-Clip Resilience**: Auto-selects `libx264` or Windows MediaFoundation `h264_mf` (`-b:v 18M`) and synthesizes matching `anullsrc` stereo tracks for silent clips so `acrossfade` never fails.

## Directory Layout

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
    └── scripts/
        ├── flow_ego.py
        └── stitch_mv.py
```

## Manual CLI Installation & Prerequisites

Prerequisites: Python 3.10+, `ffmpeg` / `ffprobe`, and EGO Lite (`ego-browser` on `PATH`, signed in to `https://flow.google.com/`).

```bash
git clone https://github.com/hxhptt-dotcom/ego-flow-mv.git ~/.gemini/config/plugins/ego-flow-mv
```

Windows PowerShell:

```powershell
git clone https://github.com/hxhptt-dotcom/ego-flow-mv.git "$env:USERPROFILE\.gemini\config\plugins\ego-flow-mv"
```

## CLI Quick Reference

```bash
# 1. Inspect active EGO task spaces and open Google Flow tabs (read-only, 0 credits)
python skills/ego-flow-mv/scripts/flow_ego.py status --json

# 2. Generate and download a single 1080p Flow shot
python skills/ego-flow-mv/scripts/flow_ego.py shot --start-frame frame.png --duration 11 --prompt "In a single continuous unbroken shot, no scene cuts. ... No on-screen text, no subtitles." --out shot_01.mp4 --json

# 3. Run an end-to-end multi-shot manifest (chained last-frame continuity + final stitch)
python skills/ego-flow-mv/scripts/flow_ego.py batch --manifest manifest.json --json

# 4. Extract a clean tail frame or manually stitch clips with VO / BGM
python skills/ego-flow-mv/scripts/stitch_mv.py last-frame --video shot_01.mp4 --out shot_01_last.png --json
python skills/ego-flow-mv/scripts/stitch_mv.py s1.mp4 s2.mp4 --out final.mp4 --size 1080x1920 --fps 24 --transitions 0.25 --voiceover vo.mp3 --bgm bgm.mp3 --json
```
