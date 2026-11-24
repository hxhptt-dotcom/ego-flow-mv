#!/usr/bin/env python3
"""Drive Google Flow (https://flow.google.com/) through EGO (ego-browser) cleanly.

Zero third-party dependencies. Executes UTF-8 `.mjs` files via:
  ego-browser nodejs -e "await import('file:///...')"
to avoid PowerShell quoting pitfalls and cleanly encapsulates all Flow UI fixes:
  1. Proper EGO TaskSpace lifecycle (`listTaskSpaces` -> claim/takeOver/taskSpace + adopt + finish).
  2. Settings popover pill scoping + `duration - 3` keyboard slider stepping (3..15s).
  3. Composer clear reset + unique staged upload filename + explicit `[role="option"]` selection.
  4. `videocam` filter baseline card counting + generation polling + `1080p` download (with 720p fallback).
  5. Optional automatic `stitch_mv` call at the end of a `batch --manifest` run.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import stitch_mv  # noqa: E402

JSON_SENTINEL = "===EGO_FLOW_JSON==="


def find_ego_browser() -> str:
    """Resolve ego-browser executable (.cmd or binary) from PATH."""
    for candidate_name in ("ego-browser", "ego-browser.cmd", "ego-browser.exe"):
        found = shutil.which(candidate_name)
        if found:
            return found
    raise FileNotFoundError(
        "Cannot find `ego-browser` in PATH. Launch EGO Lite and ensure ego-browser CLI is installed."
    )


def _run_mjs(mjs_code: str, tmp_dir: Path, filename: str, timeout: int = 360) -> dict[str, Any]:
    """Write a temporary UTF-8 `.mjs` script and run it inside `ego-browser nodejs`."""
    tmp_dir.mkdir(parents=True, exist_ok=True)
    mjs_path = tmp_dir / filename
    mjs_path.write_text(mjs_code, encoding="utf-8")
    mjs_uri = mjs_path.resolve().as_uri()
    ego_bin = find_ego_browser()

    proc = subprocess.run(
        [ego_bin, "nodejs", "-e", f"await import('{mjs_uri}')"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    idx = combined.rfind(JSON_SENTINEL)
    if idx != -1:
        raw_json = combined[idx + len(JSON_SENTINEL) :].strip()
        # Extract first valid JSON object lines after sentinel.
        decoder = json.JSONDecoder()
        try:
            parsed, _ = decoder.raw_decode(raw_json)
            if proc.returncode != 0 and isinstance(parsed, dict) and parsed.get("ok", True):
                parsed["ok"] = False
                parsed["returncode"] = proc.returncode
            return parsed
        except json.JSONDecodeError:
            pass

    raise RuntimeError(
        f"ego-browser nodejs script `{filename}` failed (rc={proc.returncode}):\n{combined[-2500:]}"
    )


def _js_const(name: str, value: Any) -> str:
    return f"const {name} = {json.dumps(value, ensure_ascii=False)};"


def build_status_mjs() -> str:
    return f"""
const SENTINEL = {json.dumps(JSON_SENTINEL)};
const spaces = await listTaskSpaces();
const flowTabs = [];
for (const s of spaces) {{
  for (const t of s.tabs || []) {{
    if ((t.url || "").includes("flow.google.com")) {{
      flowTabs.push({{ spaceId: s.id, spaceName: s.name, ownership: s.ownership, url: t.url, title: t.title }});
    }}
  }}
}}
console.log(SENTINEL);
console.log(JSON.stringify({{ ok: true, spaces, flowTabs }}, null, 2));
""".lstrip()


def build_finish_mjs(space_id: int | None, space_name: str, keep_page_label: str = "p1") -> str:
    return f"""
const SENTINEL = {json.dumps(JSON_SENTINEL)};
{_js_const("SPACE_ID", space_id)}
{_js_const("SPACE_NAME", space_name)}
{_js_const("KEEP_LABEL", keep_page_label)}
const spaces = await listTaskSpaces();
const entry = SPACE_ID != null
  ? spaces.find((s) => s.id === SPACE_ID)
  : spaces.find((s) => s.name === SPACE_NAME);
if (!entry) {{
  console.log(SENTINEL);
  console.log(JSON.stringify({{ ok: true, skipped: true, reason: "space_not_found" }}));
}} else if (entry.ownership === "user") {{
  console.log(SENTINEL);
  console.log(JSON.stringify({{ ok: true, spaceId: entry.id, alreadyUserOwned: true }}));
}} else {{
  const task = entry.ownership === "agentDelegatedToUser"
    ? await takeOverTaskSpace(entry.id)
    : await taskSpace(entry.id);
  const pages = await task.pages();
  let page = pages[0];
  if (!page) {{
    const tabs = await task.tabs();
    if (tabs.length) page = await task.adopt(tabs[0].page);
  }}
  const keepList = page?.label ? [page.label] : (KEEP_LABEL ? [KEEP_LABEL] : []);
  await task.finish({{ keep: keepList }});
  console.log(SENTINEL);
  console.log(JSON.stringify({{ ok: true, spaceId: entry.id, kept: keepList }}));
}}
""".lstrip()


def build_shot_mjs(cfg: dict[str, Any]) -> str:
    """Generate a single deterministic `.mjs` that runs one Flow video shot end-to-end."""
    return f"""
const SENTINEL = {json.dumps(JSON_SENTINEL)};
{_js_const("CFG", cfg)}

function emit(obj) {{
  console.log(SENTINEL);
  console.log(JSON.stringify(obj, null, 2));
}}

async function openOrAdoptTaskSpace() {{
  const spaces = await listTaskSpaces();
  let entry = CFG.spaceId != null
    ? spaces.find((s) => s.id === CFG.spaceId)
    : spaces.find((s) => s.name === CFG.spaceName);

  let task;
  if (!entry) {{
    task = await taskSpace(CFG.spaceName);
  }} else if (entry.ownership === "user") {{
    task = await claimTaskSpace(entry.id);
  }} else if (entry.ownership === "agentDelegatedToUser") {{
    task = await takeOverTaskSpace(entry.id);
  }} else {{
    task = await taskSpace(entry.id);
  }}

  const managed = await task.pages();
  let page = managed[0] ?? null;
  if (!page) {{
    const tabs = await task.tabs();
    if (tabs.length > 0) {{
      const flowTab = tabs.find((t) => (t.url || "").includes("flow.google.com")) ?? tabs[0];
      page = await task.adopt(flowTab.page);
    }} else {{
      page = task.page("p1");
    }}
  }}
  return {{ task, page }};
}}

async function ensureFlowProject(page) {{
  const targetUrl = CFG.projectUrl || "https://flow.google.com/";
  const currentUrl = await page.url();

  if (CFG.projectUrl) {{
    if (!currentUrl.includes(CFG.projectUrl)) {{
      await page.goto(CFG.projectUrl, {{ timeout: 45_000 }});
      await page.waitForTimeout(3500);
    }}
  }} else if (!currentUrl.includes("flow.google.com/project/")) {{
    if (!currentUrl.startsWith("https://flow.google.com")) {{
      await page.goto(targetUrl, {{ timeout: 45_000 }});
      await page.waitForTimeout(3500);
    }}
  }}

  const postNavUrl = await page.url();
  const authCheck = await page.evaluate(() => {{
    const txt = document.body?.innerText || "";
    const hasSignInBtn = [...document.querySelectorAll("button, a")].some((el) => {{
      const t = (el.innerText || "").trim();
      return t === "Sign in" || t === "登录" || t === "Sign in with Google";
    }});
    const hasAccountAvatar = Boolean(
      document.querySelector('button[aria-label*="账号详情"], button[aria-label*="Account details"]')
    );
    return {{ hasSignInBtn, hasAccountAvatar, sample: txt.slice(0, 300) }};
  }});

  if (postNavUrl.includes("accounts.google.com") || (authCheck.hasSignInBtn && !authCheck.hasAccountAvatar)) {{
    return {{ ok: false, error: "LOGIN_REQUIRED", url: postNavUrl }};
  }}

  const curNow = await page.url();
  if (!curNow.includes("/project/")) {{
    const newPt = await page.evaluate(() => {{
      const btns = [...document.querySelectorAll("button, a")].filter((el) => {{
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) return false;
        const t = (el.innerText || "").trim();
        const aria = el.getAttribute("aria-label") || "";
        return (
          t.includes("新建项目") ||
          t.includes("New project") ||
          t.includes("add_2") ||
          aria.includes("新建项目") ||
          aria.includes("New project")
        );
      }});
      if (!btns.length) return null;
      const r = btns[0].getBoundingClientRect();
      return {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }};
    }});
    if (!newPt) {{
      return {{ ok: false, error: "NEW_PROJECT_BUTTON_NOT_FOUND", url: curNow }};
    }}
    await page.mouse.click(newPt.x, newPt.y, {{ label: "create new Flow project" }});
    await page.waitForURL(/\\/project\\//, {{ timeout: 30_000 }});
    await page.waitForTimeout(3500);

    if (CFG.projectTitle) {{
      try {{
        const titleSel = 'input[aria-label="可编辑文本"], input[aria-label*="Editable"]';
        const hasInput = await page.evaluate((s) => Boolean(document.querySelector(s)), titleSel);
        if (hasInput) {{
          await page.fill(titleSel, CFG.projectTitle, {{ timeout: 3000 }});
          await page.keyboard.press("Enter");
          await page.waitForTimeout(400);
        }}
      }} catch (_err) {{
        // Project title input is optional; never block shot execution.
      }}
    }}
  }}

  return {{ ok: true, projectUrl: await page.url() }};
}}

async function clickPopoverPill(page, texts) {{
  const pt = await page.evaluate((targets) => {{
    const isVisible = (el) => {{
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== "hidden";
    }};
    const inIgnoredContainer = (el) => Boolean(
      el.closest("nav") ||
      el.closest('button[aria-label="设置触发器"]') ||
      el.closest('button[aria-label*="Settings"]')
    );
    const candidates = [...document.querySelectorAll('button, [role="radio"], [role="tab"]')]
      .filter((el) => isVisible(el) && !inIgnoredContainer(el));
    const matches = [];
    for (const el of candidates) {{
      const raw = (el.innerText || "").trim();
      const aria = el.getAttribute("aria-label") || "";
      for (const t of targets) {{
        if (raw === t || raw.includes(t) || aria === t || aria.includes(t)) {{
          const r = el.getBoundingClientRect();
          matches.push({{ el, r, len: raw.length, area: r.width * r.height }});
          break;
        }}
      }}
    }}
    if (!matches.length) return null;
    matches.sort((a, b) => a.area - b.area || a.len - b.len);
    const m = matches[0];
    return {{
      x: Math.round(m.r.left + m.r.width / 2),
      y: Math.round(m.r.top + m.r.height / 2),
      text: (m.el.innerText || "").trim(),
    }};
  }}, texts);
  if (!pt) return null;
  await page.mouse.click(pt.x, pt.y, {{ label: "select popover pill " + pt.text }});
  return pt.text;
}}

async function configureSettings(page) {{
  await page.keyboard.press("Escape");
  await page.waitForTimeout(300);

  // Clear stuck prompt or frames from an earlier shot when possible.
  const clrPt = await page.evaluate(() => {{
    const clr = document.querySelector('button[aria-label="清除提示"], button[aria-label*="Clear prompt"]');
    if (!clr) return null;
    const r = clr.getBoundingClientRect();
    return r.width > 0 && r.height > 0
      ? {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }}
      : null;
  }});
  if (clrPt) {{
    await page.mouse.click(clrPt.x, clrPt.y, {{ label: "clear previous prompt" }});
    await page.waitForTimeout(300);
  }}

  const triggerSel = 'button[aria-label="设置触发器"], button[aria-label*="Settings"]';
  await page.click(triggerSel, {{ label: "open Flow generation settings" }});
  await page.waitForTimeout(500);

  // Select Video mode, Frames vs Ingredients mode, Aspect, Resolution, Output Count x1.
  await clickPopoverPill(page, ["视频", "Video"]);
  await page.waitForTimeout(250);

  if (CFG.videoSubMode === "frames") {{
    await clickPopoverPill(page, ["帧", "Frames", "crop_free"]);
  }} else if (CFG.videoSubMode === "ingredients") {{
    await clickPopoverPill(page, ["素材", "Ingredients", "chrome_extension"]);
  }}
  await page.waitForTimeout(250);

  await clickPopoverPill(page, [CFG.aspect]);
  await page.waitForTimeout(200);
  await clickPopoverPill(page, [CFG.res]);
  await page.waitForTimeout(200);
  await clickPopoverPill(page, ["x1"]);
  await page.waitForTimeout(250);

  // Pitfall 2 fix: duration slider is 0-indexed (0..12 => 3s..15s) and requires keyboard Arrow keys.
  const targetVal = Math.max(0, Math.min(12, Number(CFG.duration) - 3));
  const sliderSel = 'input[aria-label="时长"], input[aria-label*="Duration"]';
  const hasSlider = await page.evaluate((sel) => Boolean(document.querySelector(sel)), sliderSel);
  if (hasSlider) {{
    await page.focus(sliderSel);
    for (let i = 0; i < 16; i++) {{
      const cur = await page.evaluate(
        (sel) => Number(document.querySelector(sel)?.value ?? -1),
        sliderSel,
      );
      if (cur < 0 || cur === targetVal) break;
      await page.keyboard.press(cur < targetVal ? "ArrowRight" : "ArrowLeft");
      await page.waitForTimeout(120);
    }}
  }}

  const triggerText = await page.evaluate(
    (sel) => document.querySelector(sel)?.innerText?.replace(/\\s+/g, " ").trim() || "",
    triggerSel,
  );
  await page.click(triggerSel, {{ label: "close Flow generation settings" }});
  await page.waitForTimeout(350);
  return triggerText;
}}

async function attachFrame(page, slotLabels, stagedFilePath, stagedBaseName) {{
  const slotPt = await page.evaluate((labels) => {{
    const btns = [...document.querySelectorAll("button")].filter((el) => {{
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return false;
      const t = (el.innerText || "").trim();
      const aria = el.getAttribute("aria-label") || "";
      if (aria.includes("开始生成") || aria.includes("Generate")) return false;
      const tokens = t.split(/\\s+/);
      return labels.some((l) => t === l || tokens.includes(l) || aria === l);
    }});
    if (!btns.length) return null;
    const r = btns[0].getBoundingClientRect();
    return {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }};
  }}, slotLabels);

  if (!slotPt) {{
    throw new Error("Could not find frame slot button for: " + slotLabels.join(", "));
  }}
  await page.mouse.click(slotPt.x, slotPt.y, {{ label: "open frame picker" }});
  await page.waitForTimeout(700);

  const chooserPromise = page.waitForFileChooser({{ timeout: 20_000 }});
  const uploadPt = await page.evaluate(() => {{
    const candidates = [...document.querySelectorAll("button, [role='menuitem'], span, div")].filter((el) => {{
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return false;
      const t = (el.innerText || "").trim();
      return t === "上传媒体" || t === "Upload media" || t === "Upload";
    }});
    if (!candidates.length) return null;
    candidates.sort((a, b) => {{
      const ra = a.getBoundingClientRect();
      const rb = b.getBoundingClientRect();
      return ra.width * ra.height - rb.width * rb.height;
    }});
    const r = candidates[0].getBoundingClientRect();
    return {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }};
  }});
  if (!uploadPt) {{
    throw new Error("Could not locate '上传媒体' / 'Upload media' button inside frame picker.");
  }}
  await page.mouse.click(uploadPt.x, uploadPt.y, {{
    label: "click Upload media inside frame picker",
  }});
  const chooser = await chooserPromise;
  await chooser.setFiles(stagedFilePath);

  await page.waitForTimeout(1500);
  await page.waitForFunction(
    (base) => {{
      const root = document.querySelector('.cdk-overlay-pane, [role="dialog"]') || document.body;
      const txt = root.innerText || "";
      const uploading =
        txt.includes("正在上传") ||
        txt.includes("正在加载预览") ||
        txt.includes("Uploading") ||
        txt.includes("Loading preview") ||
        /\\b\\d{{1,3}}%/.test(txt);
      return txt.includes(base) && !uploading;
    }},
    stagedBaseName,
    {{ timeout: 45_000 }},
  );
  await page.waitForTimeout(1000);

  // Pitfall 1 fix: explicitly select the newly uploaded short filename inside the modal overlay.
  const optPt = await page.evaluate((base) => {{
    const root = document.querySelector('.cdk-overlay-pane, [role="dialog"]') || document.body;
    const opts = [...root.querySelectorAll('[role="option"], [role="listbox"] > *')].filter((el) => {{
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && (el.innerText || "").includes(base);
    }});
    if (!opts.length) return null;
    const r = opts[0].getBoundingClientRect();
    return {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }};
  }}, stagedBaseName);

  if (!optPt) {{
    throw new Error("Uploaded frame option not found in picker modal: " + stagedBaseName);
  }}
  await page.mouse.click(optPt.x, optPt.y, {{ label: "select uploaded frame option" }});
  await page.waitForTimeout(1000);

  // In some Flow versions clicking [role="option"] attaches immediately and closes the modal;
  // only click "添加到提示" / "Add to prompt" if the picker modal is still open.
  const modalStillOpen = await page.evaluate(() =>
    Boolean(document.querySelector('.cdk-overlay-pane [role="option"], [role="dialog"] [role="option"]')),
  );
  if (modalStillOpen) {{
    let addPt = null;
    for (let i = 0; i < 10; i++) {{
      addPt = await page.evaluate(() => {{
        const root = document.querySelector('.cdk-overlay-pane, [role="dialog"]') || document.body;
        const candidates = [...root.querySelectorAll('button, [role="button"], span, div')].filter((el) => {{
          const r = el.getBoundingClientRect();
          if (r.width <= 0 || r.height <= 0) return false;
          if (el.disabled || el.getAttribute("aria-disabled") === "true") return false;
          const t = (el.innerText || "").trim();
          return t.includes("添加到提示") || t.includes("Add to prompt");
        }});
        if (!candidates.length) return null;
        candidates.sort((a, b) => {{
          const ra = a.getBoundingClientRect();
          const rb = b.getBoundingClientRect();
          return ra.width * ra.height - rb.width * rb.height;
        }});
        const r = candidates[0].getBoundingClientRect();
        return {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }};
      }});
      if (addPt) break;
      await page.waitForTimeout(500);
    }}
    if (!addPt) {{
      throw new Error("Could not locate '添加到提示' / 'Add to prompt' button inside modal.");
    }}
    await page.mouse.click(addPt.x, addPt.y, {{
      label: "attach staged frame to prompt",
    }});
    await page.waitForTimeout(1500);
  }}
}}

async function switchToVideosTab(page) {{
  const vidPt = await page.evaluate(() => {{
    const btns = [...document.querySelectorAll("button")].filter((b) => {{
      const r = b.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return false;
      const t = b.innerText || "";
      return t.includes("videocam") && (t.includes("视频") || t.includes("Videos"));
    }});
    if (!btns.length) return null;
    const r = btns[0].getBoundingClientRect();
    return {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }};
  }});
  if (vidPt) {{
    await page.mouse.click(vidPt.x, vidPt.y, {{ label: "switch to Videos view" }});
  }}
  await page.waitForTimeout(1200);
}}

async function scanVideoCards(page) {{
  return await page.evaluate(() => {{
    const text = document.body.innerText || "";
    const hasError =
      text.includes("无法生成") ||
      text.includes("违反") ||
      text.includes("生成失败") ||
      text.includes("Unable to generate") ||
      text.includes("violates") ||
      text.includes("Something went wrong");
    const pctMatch = text.match(/\\b\\d{{1,3}}%/g);
    const pendingCount = document.querySelectorAll("flow-pending-tile").length;
    const playEls = [...document.querySelectorAll("*")].filter(
      (el) =>
        el.childNodes.length === 1 &&
        el.textContent?.trim() === "play_circle" &&
        !el.closest("flow-pending-tile") &&
        !el.closest("nav"),
    );
    const cards = [];
    for (const el of playEls) {{
      let cur = el.parentElement;
      while (cur && (cur.getBoundingClientRect().width < 100 || cur.getBoundingClientRect().height < 90)) {{
        cur = cur.parentElement;
      }}
      const r = cur?.getBoundingClientRect();
      if (!r || r.width > 340 || r.height < 90) continue;
      const cx = Math.round(r.left + r.width / 2);
      const cy = Math.round(r.top + r.height / 2);
      if (cards.some((c) => Math.abs(c.x - cx) < 40 && Math.abs(c.y - cy) < 60)) continue;
      cards.push({{ x: cx, y: cy, w: Math.round(r.width), h: Math.round(r.height) }});
    }}
    cards.sort((a, b) => a.y - b.y || a.x - b.x);
    return {{ hasError, pctMatch, pendingCount, cardCount: cards.length, cards }};
  }});
}}

async function main() {{
  const {{ task, page }} = await openOrAdoptTaskSpace();
  const projectState = await ensureFlowProject(page);
  if (!projectState.ok) {{
    emit({{ ...projectState, spaceId: task.spaceId, pageLabel: page.label }});
    return;
  }}

  const triggerText = await configureSettings(page);

  if (CFG.stagedStartFrame) {{
    await attachFrame(page, ["开始", "Start"], CFG.stagedStartFrame, CFG.stagedStartBase);
  }}
  if (CFG.stagedEndFrame) {{
    await attachFrame(page, ["结束", "End"], CFG.stagedEndFrame, CFG.stagedEndBase);
  }}

  await switchToVideosTab(page);
  const beforeState = await scanVideoCards(page);

  const promptRect = await page.evaluate(() => {{
    const el =
      document.querySelector('[role="textbox"][contenteditable="true"]') ||
      document.querySelector('[contenteditable="true"]') ||
      document.querySelector("textarea");
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {{ x: Math.round(r.left + 40), y: Math.round(r.top + 15) }};
  }});
  if (promptRect) {{
    await page.mouse.click(promptRect.x, promptRect.y, {{ label: "focus prompt box" }});
  }} else {{
    await page.click('[contenteditable="true"], textarea', {{
      label: "focus fallback prompt input",
    }});
  }}
  await page.waitForTimeout(250);
  await page.keyboard.paste(CFG.prompt);
  await page.waitForTimeout(450);

  await page.click('button[aria-label="开始生成"], button[aria-label*="Generate"]', {{
    label: "start Flow video generation",
  }});
  await page.waitForTimeout(3000);
  await switchToVideosTab(page);

  const startMs = Date.now();
  const timeoutMs = Number(CFG.timeoutSeconds || 300) * 1000;
  let finalState = beforeState;
  while (Date.now() - startMs < timeoutMs) {{
    finalState = await scanVideoCards(page);
    if (finalState.hasError) {{
      emit({{
        ok: false,
        error: "GENERATION_REJECTED",
        spaceId: task.spaceId,
        pageLabel: page.label,
        projectUrl: projectState.projectUrl,
        triggerText,
        state: finalState,
      }});
      return;
    }}
    if (!finalState.pctMatch && finalState.pendingCount === 0 && finalState.cardCount > beforeState.cardCount) {{
      break;
    }}
    await page.waitForTimeout(6000);
  }}

  if (finalState.cardCount <= beforeState.cardCount) {{
    emit({{
      ok: false,
      error: "GENERATION_TIMEOUT",
      spaceId: task.spaceId,
      pageLabel: page.label,
      projectUrl: projectState.projectUrl,
      triggerText,
      beforeCount: beforeState.cardCount,
      state: finalState,
    }});
    return;
  }}

  await page.waitForTimeout(2000);
  const newest = finalState.cards[0];
  let moreBtn = null;
  for (const offsetY of [0, -30, 30]) {{
    await page.mouse.move(newest.x, newest.y + offsetY, {{ label: "hover newest video card" }});
    await page.waitForTimeout(800);
    moreBtn = await page.evaluate(({{ tx, ty }}) => {{
      const btns = [...document.querySelectorAll("button")].filter((b) => {{
        const lbl = (b.textContent || b.innerText || "");
        if (!lbl.includes("more_vert")) return false;
        const r = b.getBoundingClientRect();
        return r.width > 0 && Math.abs(r.left + r.width / 2 - tx) < 140 && Math.abs(r.top + r.height / 2 - ty) < 200;
      }});
      if (!btns.length) return null;
      btns.sort((a, b) => {{
        const ra = a.getBoundingClientRect();
        const rb = b.getBoundingClientRect();
        const da = Math.hypot(ra.left - tx, ra.top - ty);
        const db = Math.hypot(rb.left - tx, rb.top - ty);
        return da - db;
      }});
      const r = btns[0].getBoundingClientRect();
      return {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }};
    }}, {{ tx: newest.x, ty: newest.y }});
    if (moreBtn) break;
  }}

  if (!moreBtn) {{
    emit({{ ok: false, error: "MORE_MENU_BUTTON_NOT_FOUND", newest, projectUrl: projectState.projectUrl }});
    return;
  }}

  await page.mouse.click(moreBtn.x, moreBtn.y, {{ label: "open card options menu" }});
  await page.waitForTimeout(600);

  const dlMenuPt = await page.evaluate(() => {{
    const items = [...document.querySelectorAll('[role="menuitem"]')].filter((el) => {{
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return false;
      const t = (el.innerText || "").trim();
      return t.includes("下载") || t.includes("Download");
    }});
    if (!items.length) return null;
    const r = items[0].getBoundingClientRect();
    return {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }};
  }});
  if (!dlMenuPt) {{
    emit({{ ok: false, error: "DOWNLOAD_MENU_ITEM_NOT_FOUND", projectUrl: projectState.projectUrl }});
    return;
  }}

  await page.mouse.move(dlMenuPt.x, dlMenuPt.y, {{ label: "hover Download submenu" }});
  await page.waitForTimeout(500);
  const subOpen = await page.evaluate(
    () => document.body.innerText.includes("1080p") || document.body.innerText.includes("720p"),
  );
  if (!subOpen) {{
    await page.mouse.click(dlMenuPt.x, dlMenuPt.y, {{ label: "click Download submenu" }});
    await page.waitForTimeout(500);
  }}

  let download = null;
  let actualDlRes = CFG.dlRes;
  const targets = CFG.dlRes === "1080p" && CFG.fallback720p ? ["1080p", "720p"] : [CFG.dlRes];
  for (const resLabel of targets) {{
    try {{
      const resPt = await page.evaluate((lbl) => {{
        const items = [...document.querySelectorAll('[role="menuitem"]')].filter((el) => {{
          const r = el.getBoundingClientRect();
          return r.width > 0 && r.height > 0 && (el.innerText || "").includes(lbl);
        }});
        if (!items.length) return null;
        const r = items[0].getBoundingClientRect();
        return {{ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }};
      }}, resLabel);
      if (!resPt) throw new Error("Resolution menu item not found: " + resLabel);
      const dlPromise = page.waitForEvent("download", {{ timeout: resLabel === "1080p" ? 160_000 : 120_000 }});
      await page.mouse.click(resPt.x, resPt.y, {{ label: `download video at ${{resLabel}}` }});
      download = await dlPromise;
      actualDlRes = resLabel;
      break;
    }} catch (err) {{
      if (resLabel === targets[targets.length - 1]) throw err;
    }}
  }}

  await download.saveAs(CFG.outPath);
  emit({{
    ok: true,
    spaceId: task.spaceId,
    pageLabel: page.label,
    projectUrl: await page.url(),
    triggerText,
    actualDlRes,
    suggestedFilename: download.suggestedFilename(),
    outPath: CFG.outPath,
  }});
}}

main().catch((err) => {{
  emit({{ ok: false, error: String(err?.stack || err) }});
  process.exitCode = 1;
}});
""".lstrip()


def _stage_image(src_path: str | Path, stage_dir: Path, prefix: str) -> tuple[str, str]:
    src = Path(src_path).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Frame image not found: {src}")
    stage_dir.mkdir(parents=True, exist_ok=True)
    # Keep filename <= 12 chars so Flow's frame picker never truncates it with '...'.
    unique_name = f"{prefix}_{uuid.uuid4().hex[:4]}{src.suffix.lower() or '.png'}"
    dst = stage_dir / unique_name
    shutil.copy2(src, dst)
    return str(dst).replace("\\", "/"), unique_name


def _resolve_prompt(prompt: str | None, prompt_file: str | None) -> str:
    if prompt_file:
        p = Path(prompt_file)
        if not p.is_file():
            raise FileNotFoundError(f"Prompt file not found: {p}")
        return p.read_text(encoding="utf-8").strip()
    if prompt:
        return prompt.strip()
    raise ValueError("Either --prompt or --prompt-file must be provided.")


def _normalize_duration(seconds: int) -> int:
    return max(3, min(15, int(seconds)))


def run_single_shot(
    *,
    prompt: str,
    out_path: str | Path,
    start_frame: str | Path | None = None,
    end_frame: str | Path | None = None,
    mode: str = "auto",
    aspect: str = "9:16",
    duration: int = 11,
    res: str = "720p",
    dl_res: str = "1080p",
    fallback_720p: bool = True,
    project_url: str | None = None,
    project_title: str | None = None,
    space_name: str = "ego-flow-studio",
    space_id: int | None = None,
    timeout: int = 300,
    keep_claimed: bool = False,
    dry_run: bool = False,
    work_dir: Path | None = None,
) -> dict[str, Any]:
    out_p = Path(out_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    sub_mode = mode
    if sub_mode == "auto":
        sub_mode = "frames" if (start_frame or end_frame) else "ingredients"

    stage_root = work_dir or (out_p.parent / ".ego_flow_tmp")
    staged_start_path = None
    staged_start_base = None
    staged_end_path = None
    staged_end_base = None

    if start_frame:
        staged_start_path, staged_start_base = _stage_image(start_frame, stage_root / "uploads", "sf")
    if end_frame:
        staged_end_path, staged_end_base = _stage_image(end_frame, stage_root / "uploads", "ef")

    dur = _normalize_duration(duration)
    cfg = {
        "prompt": prompt,
        "outPath": str(out_p).replace("\\", "/"),
        "stagedStartFrame": staged_start_path,
        "stagedStartBase": staged_start_base,
        "stagedEndFrame": staged_end_path,
        "stagedEndBase": staged_end_base,
        "videoSubMode": sub_mode,
        "aspect": aspect,
        "duration": dur,
        "sliderValue": dur - 3,
        "res": res,
        "dlRes": dl_res,
        "fallback720p": fallback_720p,
        "projectUrl": project_url,
        "projectTitle": project_title,
        "spaceName": space_name,
        "spaceId": space_id,
        "timeoutSeconds": timeout,
    }
    shot_mjs = build_shot_mjs(cfg)
    finish_mjs = build_finish_mjs(space_id, space_name)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "cfg": cfg,
            "shot_mjs": shot_mjs,
            "finish_mjs": finish_mjs,
        }

    try:
        res_obj = _run_mjs(shot_mjs, stage_root / "scripts", f"shot_{out_p.stem}.mjs", timeout=timeout + 240)
        if not res_obj.get("ok"):
            return res_obj
        res_obj["probe"] = stitch_mv.probe_media(out_p)
        return res_obj
    finally:
        if not keep_claimed:
            try:
                final_sid = space_id
                if "res_obj" in locals() and isinstance(res_obj, dict) and res_obj.get("spaceId") is not None:
                    final_sid = res_obj["spaceId"]
                _run_mjs(build_finish_mjs(final_sid, space_name), stage_root / "scripts", "finish.mjs", timeout=45)
            except Exception:
                pass


def run_batch(manifest_path: str | Path, *, resume: bool = False, dry_run: bool = False) -> dict[str, Any]:
    m_path = Path(manifest_path).resolve()
    if not m_path.is_file():
        raise FileNotFoundError(f"Manifest file not found: {m_path}")

    manifest = json.loads(m_path.read_text(encoding="utf-8"))
    shots = manifest.get("shots") or []
    if not shots:
        raise ValueError("Manifest must contain a non-empty `shots` list.")

    base_dir = m_path.parent
    stage_root = base_dir / ".ego_flow_tmp"
    space_name = manifest.get("space_name", "ego-flow-studio")
    space_id = manifest.get("space_id")
    project_url = manifest.get("project_url")
    project_title = manifest.get("project_title")
    default_aspect = manifest.get("aspect", "9:16")
    default_res = manifest.get("res", "720p")
    default_dl_res = manifest.get("dl_res", "1080p")
    default_timeout = int(manifest.get("timeout", 300))

    results: list[dict[str, Any]] = []
    dry_scripts: list[dict[str, Any]] = []
    prev_out: Path | None = None

    try:
        for idx, shot in enumerate(shots):
            shot_id = shot.get("id") or f"shot_{idx + 1:02d}"
            out_raw = shot.get("out") or str(base_dir / "flow_shots" / f"{shot_id}.mp4")
            out_p = (base_dir / out_raw).resolve() if not Path(out_raw).is_absolute() else Path(out_raw).resolve()

            start_frame = shot.get("start_frame")
            if start_frame and not Path(start_frame).is_absolute():
                start_frame = str((base_dir / start_frame).resolve())

            end_frame = shot.get("end_frame")
            if end_frame and not Path(end_frame).is_absolute():
                end_frame = str((base_dir / end_frame).resolve())

            use_prev_tail = bool(shot.get("start_from_prev_last_frame"))
            if use_prev_tail:
                if prev_out is None:
                    raise ValueError(f"Shot `{shot_id}` sets start_from_prev_last_frame=true on the first shot.")
                tail_png = out_p.parent / f"{out_p.stem}_start_from_prev.png"
                if dry_run:
                    tail_png.parent.mkdir(parents=True, exist_ok=True)
                    tail_png.write_bytes(b"DRY_RUN_PLACEHOLDER")
                else:
                    stitch_mv.extract_last_frame(prev_out, tail_png)
                start_frame = str(tail_png)

            if (resume or manifest.get("resume")) and not dry_run and out_p.is_file() and out_p.stat().st_size > 10_000:
                probe = stitch_mv.probe_media(out_p)
                results.append({"id": shot_id, "ok": True, "skipped": True, "outPath": str(out_p), "probe": probe})
                prev_out = out_p
                continue

            prompt = _resolve_prompt(shot.get("prompt"), shot.get("prompt_file"))
            res_obj = run_single_shot(
                prompt=prompt,
                out_path=out_p,
                start_frame=start_frame,
                end_frame=end_frame,
                mode=shot.get("mode", "auto"),
                aspect=shot.get("aspect", default_aspect),
                duration=int(shot.get("duration", 10)),
                res=shot.get("res", default_res),
                dl_res=shot.get("dl_res", default_dl_res),
                fallback_720p=bool(shot.get("fallback_720p", True)),
                project_url=project_url,
                project_title=project_title if idx == 0 else None,
                space_name=space_name,
                space_id=space_id,
                timeout=int(shot.get("timeout", default_timeout)),
                keep_claimed=True,
                dry_run=dry_run,
                work_dir=stage_root,
            )

            if dry_run:
                dry_scripts.append({"id": shot_id, "out": str(out_p), **res_obj})
                prev_out = out_p
                continue

            if not res_obj.get("ok"):
                return {
                    "ok": False,
                    "failed_shot": shot_id,
                    "error_detail": res_obj,
                    "completed_shots": results,
                    "project_url": project_url,
                    "space_id": space_id,
                }

            project_url = res_obj.get("projectUrl") or project_url
            space_id = res_obj.get("spaceId") if res_obj.get("spaceId") is not None else space_id
            results.append({"id": shot_id, **res_obj})
            prev_out = out_p
    finally:
        if not dry_run and (space_id is not None or space_name):
            try:
                _run_mjs(build_finish_mjs(space_id, space_name), stage_root / "scripts", "batch_finish.mjs", timeout=45)
            except Exception:
                pass
        # Clean temporary dry-run placeholders if created.
        if dry_run:
            for s in shots:
                if s.get("start_from_prev_last_frame"):
                    out_raw = s.get("out") or str(base_dir / "flow_shots" / f"{s.get('id', 'shot')}.mp4")
                    out_p = (base_dir / out_raw).resolve() if not Path(out_raw).is_absolute() else Path(out_raw).resolve()
                    ph = out_p.parent / f"{out_p.stem}_start_from_prev.png"
                    if ph.is_file() and ph.read_bytes() == b"DRY_RUN_PLACEHOLDER":
                        ph.unlink()

    if dry_run:
        finish_mjs = build_finish_mjs(space_id, space_name)
        return {
            "ok": True,
            "dry_run": True,
            "manifest": str(m_path),
            "shots": dry_scripts,
            "finish_mjs": finish_mjs,
            "final_out": manifest.get("final_out"),
        }

    stitch_result = None
    final_out = manifest.get("final_out")
    if final_out:
        final_p = (base_dir / final_out).resolve() if not Path(final_out).is_absolute() else Path(final_out).resolve()
        clips = [r["outPath"] for r in results]
        vo = manifest.get("voiceover")
        if vo and not Path(vo).is_absolute():
            vo = str((base_dir / vo).resolve())
        bgm = manifest.get("bgm")
        if bgm and not Path(bgm).is_absolute():
            bgm = str((base_dir / bgm).resolve())

        stitch_result = stitch_mv.stitch_videos(
            clips,
            final_p,
            size=manifest.get("size"),
            fps=int(manifest.get("fps", 24)),
            transitions=manifest.get("transitions", "0.3"),
            transition_types=manifest.get("transition_types", "fade"),
            voiceover=vo,
            vo_vol=float(manifest.get("vo_vol", 1.0)),
            orig_vol=float(manifest.get("orig_vol", 1.0)),
            bgm=bgm,
            bgm_vol=float(manifest.get("bgm_vol", 0.22)),
            bgm_fade_out=float(manifest.get("bgm_fade_out", 1.5)),
        )

    return {
        "ok": True,
        "space_id": space_id,
        "project_url": project_url,
        "shots": results,
        "stitch": stitch_result,
        "final_out": (stitch_result or {}).get("out"),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Automated EGO + Google Flow (Omni 1.2 Flash) video generator and stitcher CLI."
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_st = sub.add_parser("status", help="Inspect active EGO task spaces and Google Flow tabs (read-only).")
    p_st.add_argument("--json", action="store_true", help="Print JSON output.")

    p_lf = sub.add_parser("last-frame", help="Extract tail frame PNG from an MP4 clip.")
    p_lf.add_argument("--video", required=True, help="Source MP4 path.")
    p_lf.add_argument("--out", required=True, help="Output PNG path.")
    p_lf.add_argument("--sseof", type=float, default=-0.1, help="Seek offset from end (default: -0.1).")
    p_lf.add_argument("--json", action="store_true", help="Print JSON output.")

    p_sh = sub.add_parser("shot", help="Generate and download a single Flow video shot via EGO.")
    p_sh.add_argument("--prompt", default=None, help="English Omni 1.2 Flash video prompt.")
    p_sh.add_argument("--prompt-file", default=None, help="Path to UTF-8 text file containing prompt.")
    p_sh.add_argument("--out", required=True, help="Output MP4 path.")
    p_sh.add_argument("--start-frame", default=None, help="Optional Start frame image path.")
    p_sh.add_argument("--end-frame", default=None, help="Optional End frame image path.")
    p_sh.add_argument("--mode", choices=["auto", "frames", "ingredients"], default="auto")
    p_sh.add_argument("--aspect", choices=["9:16", "16:9"], default="9:16")
    p_sh.add_argument("--duration", type=int, default=11, help="Duration seconds 3..15 (default: 11).")
    p_sh.add_argument("--res", choices=["720p", "360p"], default="720p")
    p_sh.add_argument("--dl-res", choices=["1080p", "720p"], default="1080p")
    p_sh.add_argument("--no-fallback-720p", action="store_true", help="Do not fall back to 720p if 1080p fails.")
    p_sh.add_argument("--project-url", default=None, help="Existing Flow /project/<id> URL.")
    p_sh.add_argument("--project-title", default=None, help="Project title when creating a new Flow project.")
    p_sh.add_argument("--space-name", default="ego-flow-studio", help="EGO TaskSpace name.")
    p_sh.add_argument("--space-id", type=int, default=None, help="Explicit EGO TaskSpace ID.")
    p_sh.add_argument("--timeout", type=int, default=300, help="Generation poll timeout seconds.")
    p_sh.add_argument("--keep-claimed", action="store_true", help="Skip final task.finish keep release.")
    p_sh.add_argument("--dry-run", action="store_true", help="Emit generated config and .mjs without running EGO.")
    p_sh.add_argument("--json", action="store_true", help="Print JSON output.")

    p_bt = sub.add_parser("batch", help="Execute a multi-shot manifest and optionally stitch final MP4.")
    p_bt.add_argument("--manifest", required=True, help="Path to manifest JSON file.")
    p_bt.add_argument("--resume", action="store_true", help="Skip shots whose output MP4 already exists.")
    p_bt.add_argument("--dry-run", action="store_true", help="Validate manifest and emit .mjs plans only.")
    p_bt.add_argument("--json", action="store_true", help="Print JSON output.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.subcommand == "status":
            with tempfile.TemporaryDirectory(prefix="ego_flow_status_") as td:
                res = _run_mjs(build_status_mjs(), Path(td), "status.mjs", timeout=30)
        elif args.subcommand == "last-frame":
            res = stitch_mv.extract_last_frame(args.video, args.out, sseof=args.sseof)
        elif args.subcommand == "shot":
            prompt_text = _resolve_prompt(args.prompt, args.prompt_file)
            res = run_single_shot(
                prompt=prompt_text,
                out_path=args.out,
                start_frame=args.start_frame,
                end_frame=args.end_frame,
                mode=args.mode,
                aspect=args.aspect,
                duration=args.duration,
                res=args.res,
                dl_res=args.dl_res,
                fallback_720p=not args.no_fallback_720p,
                project_url=args.project_url,
                project_title=args.project_title,
                space_name=args.space_name,
                space_id=args.space_id,
                timeout=args.timeout,
                keep_claimed=args.keep_claimed,
                dry_run=args.dry_run,
            )
        else:
            res = run_batch(args.manifest, resume=args.resume, dry_run=args.dry_run)
    except Exception as exc:
        err = {"ok": False, "error": str(exc)}
        print(json.dumps(err, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))

    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
