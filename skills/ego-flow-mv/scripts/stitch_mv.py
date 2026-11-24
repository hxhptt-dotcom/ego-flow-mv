#!/usr/bin/env python3
"""Local ffmpeg / ffprobe video utilities and seamless xfade+acrossfade MV stitcher.

Works on Windows where ffmpeg may provide `h264_mf` instead of `libx264`
(such as `~/.raea/bin/ffmpeg.exe`). Zero third-party Python deps.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


FALLBACK_BIN_DIR = Path.home() / ".raea" / "bin"


def find_media_tool(name: str) -> str:
    """Resolve `ffmpeg` or `ffprobe` executable from PATH or known local bin."""
    found = shutil.which(name)
    if found:
        return found
    exe_name = f"{name}.exe" if os.name == "nt" and not name.endswith(".exe") else name
    candidate = FALLBACK_BIN_DIR / exe_name
    if candidate.is_file():
        return str(candidate)
    raise FileNotFoundError(
        f"Cannot locate `{name}` in PATH or {FALLBACK_BIN_DIR}. Please install ffmpeg."
    )


def detect_h264_encoder(ffmpeg_bin: str | None = None) -> tuple[str, list[str]]:
    """Select `libx264` when compiled in, otherwise fall back to `h264_mf`."""
    ffmpeg = ffmpeg_bin or find_media_tool("ffmpeg")
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    encoders_out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if " libx264 " in encoders_out:
        return "libx264", ["-c:v", "libx264", "-crf", "18", "-preset", "medium"]
    if " h264_mf " in encoders_out:
        return "h264_mf", ["-c:v", "h264_mf", "-b:v", "18M"]
    if " h264_nvenc " in encoders_out:
        return "h264_nvenc", ["-c:v", "h264_nvenc", "-cq", "19"]
    raise RuntimeError("No supported H.264 encoder (libx264 / h264_mf / h264_nvenc) found in ffmpeg.")


def _parse_fps(rate_str: str | None) -> float | None:
    if not rate_str or rate_str == "0/0":
        return None
    if "/" in rate_str:
        num_s, den_s = rate_str.split("/", 1)
        try:
            num, den = float(num_s), float(den_s)
            return round(num / den, 3) if den != 0 else None
        except ValueError:
            return None
    try:
        return round(float(rate_str), 3)
    except ValueError:
        return None


def probe_media(path: str | Path, ffprobe_bin: str | None = None) -> dict[str, Any]:
    """Return normalized metadata for a local audio/video file using ffprobe."""
    ffprobe = ffprobe_bin or find_media_tool("ffprobe")
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Media file not found: {p}")

    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(p),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {p}: {proc.stderr.strip()}")

    data = json.loads(proc.stdout or "{}")
    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    raw_dur = fmt.get("duration") or (v_stream or {}).get("duration") or (a_stream or {}).get("duration") or "0"
    try:
        duration = round(float(raw_dur), 3)
    except ValueError:
        duration = 0.0

    return {
        "path": str(p.resolve()),
        "duration": duration,
        "width": int(v_stream["width"]) if v_stream and v_stream.get("width") else None,
        "height": int(v_stream["height"]) if v_stream and v_stream.get("height") else None,
        "fps": _parse_fps((v_stream or {}).get("avg_frame_rate") or (v_stream or {}).get("r_frame_rate")),
        "vcodec": (v_stream or {}).get("codec_name"),
        "acodec": (a_stream or {}).get("codec_name"),
        "has_audio": a_stream is not None,
        "size_bytes": p.stat().st_size,
    }


def extract_last_frame(
    video_path: str | Path,
    out_png: str | Path,
    sseof: float = -0.1,
    ffmpeg_bin: str | None = None,
) -> dict[str, Any]:
    """Extract a clean tail frame from a video clip, retrying deeper on ultra-short clips."""
    ffmpeg = ffmpeg_bin or find_media_tool("ffmpeg")
    src = Path(video_path)
    dst = Path(out_png)
    if not src.is_file():
        raise FileNotFoundError(f"Source video not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()

    attempts = [sseof, -0.5] if abs(sseof - (-0.5)) > 1e-6 else [sseof]
    last_err = ""
    for offset in attempts:
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-sseof",
                f"{offset:.3f}",
                "-i",
                str(src),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(dst),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
            info = probe_media(dst)
            return {
                "ok": True,
                "video": str(src.resolve()),
                "out": str(dst.resolve()),
                "sseof": offset,
                "width": info.get("width"),
                "height": info.get("height"),
                "size_bytes": info.get("size_bytes"),
            }
        last_err = (proc.stderr or proc.stdout or "").strip()

    raise RuntimeError(f"Failed to extract tail frame from {src}: {last_err}")


def _parse_size(size_str: str | None, first_probe: dict[str, Any]) -> tuple[int, int]:
    if size_str:
        clean = size_str.lower().strip()
        if "x" not in clean:
            raise ValueError(f"Invalid --size `{size_str}`; expected WxH like 1080x1920.")
        w_s, h_s = clean.split("x", 1)
        w, h = int(w_s), int(h_s)
        if w <= 0 or h <= 0 or w % 2 or h % 2:
            raise ValueError(f"Size dimensions must be positive even integers, got {w}x{h}.")
        return w, h
    w = int(first_probe.get("width") or 1080)
    h = int(first_probe.get("height") or 1920)
    return w - (w % 2), h - (h % 2)


def _expand_per_transition(spec: str | list[float] | list[str] | None, count: int, default_val: Any) -> list[Any]:
    if count <= 0:
        return []
    if spec is None or spec == "":
        return [default_val] * count
    items = [s.strip() for s in spec.split(",")] if isinstance(spec, str) else list(spec)
    items = [x for x in items if str(x) != ""]
    if not items:
        return [default_val] * count
    if len(items) == 1:
        return [items[0]] * count
    if len(items) < count:
        items.extend([items[-1]] * (count - len(items)))
    return items[:count]


def stitch_videos(
    clips: list[str | Path],
    out_path: str | Path,
    *,
    size: str | None = None,
    fps: int = 24,
    transitions: str | list[float] = "0.3",
    transition_types: str | list[str] = "fade",
    voiceover: str | Path | None = None,
    vo_vol: float = 1.0,
    orig_vol: float = 1.0,
    bgm: str | Path | None = None,
    bgm_vol: float = 0.22,
    bgm_fade_out: float = 1.5,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Normalize N clips, stitch with cumulative xfade+acrossfade, optionally mix VO/BGM."""
    if not clips:
        raise ValueError("At least 1 input clip is required.")

    ffmpeg = find_media_tool("ffmpeg")
    ffprobe = find_media_tool("ffprobe")
    encoder_name, encoder_args = detect_h264_encoder(ffmpeg)

    probes = [probe_media(c, ffprobe_bin=ffprobe) for c in clips]
    width, height = _parse_size(size, probes[0])

    n = len(clips)
    raw_trans = [float(x) for x in _expand_per_transition(transitions, n - 1, 0.3)]
    trans_types = [str(x).strip() for x in _expand_per_transition(transition_types, n - 1, "fade")]

    # Clamp transitions so no clip shorter than transition breaks xfade.
    safe_trans: list[float] = []
    for i, t in enumerate(raw_trans):
        max_allowed = max(0.05, min(probes[i]["duration"], probes[i + 1]["duration"]) - 0.1)
        safe_trans.append(round(max(0.04, min(t, max_allowed)), 3))

    cmd: list[str] = [ffmpeg, "-y"]
    for c in clips:
        cmd.extend(["-i", str(c)])

    extra_inputs: dict[str, int] = {}
    if voiceover:
        vo_p = Path(voiceover)
        if not vo_p.is_file():
            raise FileNotFoundError(f"Voiceover file not found: {vo_p}")
        extra_inputs["voiceover"] = n
        cmd.extend(["-i", str(vo_p)])
    if bgm:
        bgm_p = Path(bgm)
        if not bgm_p.is_file():
            raise FileNotFoundError(f"BGM file not found: {bgm_p}")
        extra_inputs["bgm"] = n + (1 if voiceover else 0)
        cmd.extend(["-stream_loop", "-1", "-i", str(bgm_p)])

    filters: list[str] = []
    for idx, p in enumerate(probes):
        filters.append(
            f"[{idx}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"fps={fps},format=yuv420p,settb=AVTB[v{idx}]"
        )
        if p["has_audio"]:
            filters.append(
                f"[{idx}:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{idx}]"
            )
        else:
            dur = max(0.2, p["duration"])
            filters.append(f"anullsrc=r=48000:cl=stereo:d={dur:.3f}[a{idx}]")

    if n == 1:
        v_cur = "v0"
        a_cur = "a0"
        expected_total = probes[0]["duration"]
    else:
        v_cur = "v0"
        a_cur = "a0"
        cum_dur = probes[0]["duration"]
        cum_trans = 0.0
        for i in range(n - 1):
            t_dur = safe_trans[i]
            t_kind = trans_types[i]
            offset = round(max(0.05, cum_dur - cum_trans - t_dur), 3)
            v_next = f"vx{i}" if i < n - 2 else "v_stitched"
            a_next = f"ax{i}" if i < n - 2 else "a_stitched"
            filters.append(
                f"[{v_cur}][v{i + 1}]xfade=transition={t_kind}:duration={t_dur:.3f}:offset={offset:.3f}[{v_next}]"
            )
            filters.append(
                f"[{a_cur}][a{i + 1}]acrossfade=d={t_dur:.3f}:c1=tri:c2=tri[{a_next}]"
            )
            v_cur = v_next
            a_cur = a_next
            cum_dur += probes[i + 1]["duration"]
            cum_trans += t_dur
        expected_total = round(max(0.2, cum_dur - cum_trans), 3)

    mix_labels: list[str] = []
    if abs(orig_vol - 1.0) > 1e-4:
        filters.append(f"[{a_cur}]volume={orig_vol:.3f}[a_orig]")
        mix_labels.append("[a_orig]")
    else:
        mix_labels.append(f"[{a_cur}]")

    if "voiceover" in extra_inputs:
        vo_idx = extra_inputs["voiceover"]
        filters.append(
            f"[{vo_idx}:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"volume={vo_vol:.3f},apad=whole_dur={expected_total:.3f},atrim=0:{expected_total:.3f}[a_vo]"
        )
        mix_labels.append("[a_vo]")

    if "bgm" in extra_inputs:
        bgm_idx = extra_inputs["bgm"]
        fade_d = min(bgm_fade_out, max(0.2, expected_total / 3.0))
        fade_st = round(max(0.0, expected_total - fade_d), 3)
        filters.append(
            f"[{bgm_idx}:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"atrim=0:{expected_total:.3f},volume={bgm_vol:.3f},"
            f"afade=t=out:st={fade_st:.3f}:d={fade_d:.3f}[a_bgm]"
        )
        mix_labels.append("[a_bgm]")

    final_v = f"[{v_cur}]"
    if len(mix_labels) > 1:
        filters.append(
            f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=0:normalize=0[a_final]"
        )
        final_a = "[a_final]"
    else:
        final_a = mix_labels[0]

    filter_complex = ";".join(filters)
    out_p = Path(out_path)
    if not dry_run:
        out_p.parent.mkdir(parents=True, exist_ok=True)

    cmd.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            final_v,
            "-map",
            final_a,
            *encoder_args,
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(fps),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(out_p),
        ]
    )

    result: dict[str, Any] = {
        "ok": True,
        "dry_run": dry_run,
        "encoder": encoder_name,
        "size": f"{width}x{height}",
        "fps": fps,
        "expected_duration": expected_total,
        "transitions": safe_trans,
        "transition_types": trans_types,
        "inputs": [p["path"] for p in probes],
        "out": str(out_p.resolve()),
        "command": cmd,
    }
    if dry_run:
        return result

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0 or not out_p.is_file() or out_p.stat().st_size == 0:
        raise RuntimeError(
            f"ffmpeg stitch failed (rc={proc.returncode}): {(proc.stderr or proc.stdout)[-2000:]}"
        )

    result["probe"] = probe_media(out_p, ffprobe_bin=ffprobe)
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local ffmpeg tail-frame extractor and seamless xfade+acrossfade MV stitcher."
    )
    sub = parser.add_subparsers(dest="subcommand")

    p_lf = sub.add_parser("last-frame", help="Extract a clean tail frame PNG from an MP4 clip.")
    p_lf.add_argument("--video", required=True, help="Source MP4 video path.")
    p_lf.add_argument("--out", required=True, help="Output PNG path.")
    p_lf.add_argument("--sseof", type=float, default=-0.1, help="Seek offset from end (default: -0.1).")
    p_lf.add_argument("--json", action="store_true", help="Print JSON output.")

    p_st = sub.add_parser("stitch", help="Stitch 1..N MP4 clips with xfade+acrossfade and optional VO/BGM.")
    p_st.add_argument("clips", nargs="+", help="Ordered input MP4 paths.")
    p_st.add_argument("--out", required=True, help="Final output MP4 path.")
    p_st.add_argument("--size", default=None, help="Output WxH (e.g., 1080x1920 or 1920x1080).")
    p_st.add_argument("--fps", type=int, default=24, help="Output frame rate (default: 24).")
    p_st.add_argument(
        "--transitions",
        default="0.3",
        help="Single duration or comma-separated transition durations in seconds (e.g. 0.25,0.6).",
    )
    p_st.add_argument(
        "--transition-types",
        default="fade",
        help="Single xfade type or comma-separated types (e.g. fade,fadeblack,wipeleft).",
    )
    p_st.add_argument("--voiceover", default=None, help="Optional voiceover audio path (mp3/wav).")
    p_st.add_argument("--vo-vol", type=float, default=1.0, help="Voiceover volume multiplier.")
    p_st.add_argument("--orig-vol", type=float, default=1.0, help="Clip original audio volume multiplier.")
    p_st.add_argument("--bgm", default=None, help="Optional background music path (looped & trimmed).")
    p_st.add_argument("--bgm-vol", type=float, default=0.22, help="BGM volume multiplier.")
    p_st.add_argument("--bgm-fade-out", type=float, default=1.5, help="BGM tail fade-out seconds.")
    p_st.add_argument("--dry-run", action="store_true", help="Validate & emit filtergraph without encoding.")
    p_st.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    # Allow calling `stitch_mv.py clip1.mp4 clip2.mp4 --out final.mp4` without explicit `stitch` verb.
    if args_list and args_list[0] not in {"last-frame", "stitch", "-h", "--help"}:
        args_list = ["stitch", *args_list]

    parser = _build_parser()
    args = parser.parse_args(args_list)
    if not args.subcommand:
        parser.print_help()
        return 1

    try:
        if args.subcommand == "last-frame":
            res = extract_last_frame(args.video, args.out, sseof=args.sseof)
        else:
            res = stitch_videos(
                args.clips,
                args.out,
                size=args.size,
                fps=args.fps,
                transitions=args.transitions,
                transition_types=args.transition_types,
                voiceover=args.voiceover,
                vo_vol=args.vo_vol,
                orig_vol=args.orig_vol,
                bgm=args.bgm,
                bgm_vol=args.bgm_vol,
                bgm_fade_out=args.bgm_fade_out,
                dry_run=args.dry_run,
            )
    except Exception as exc:
        err = {"ok": False, "error": str(exc)}
        print(json.dumps(err, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"OK: {res.get('out')}")
        if "probe" in res:
            p = res["probe"]
            print(
                f"Video: {p.get('width')}x{p.get('height')} @ {p.get('fps')}fps, "
                f"duration={p.get('duration')}s, size={p.get('size_bytes')} bytes, encoder={res.get('encoder')}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
