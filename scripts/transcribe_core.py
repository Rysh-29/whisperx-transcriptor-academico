from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Callable, Optional

try:
    import torch
except Exception:  # pragma: no cover - optional dependency
    torch = None

try:
    import ctranslate2
except Exception:  # pragma: no cover - optional dependency
    ctranslate2 = None

from faster_whisper import WhisperModel

from config import (
    DEFAULT_MODEL,
    DEFAULT_LANGUAGE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_PROMPT,
    SUPPORTED_EXTS,
)


@dataclass
class TranscribeConfig:
    model: str = DEFAULT_MODEL
    language: str = DEFAULT_LANGUAGE  # "es" or "auto"
    output_format: str = DEFAULT_OUTPUT_FORMAT  # "txt" or "srt"
    prompt: str = DEFAULT_PROMPT
    device: Optional[str] = None
    compute_type: Optional[str] = None


def resolve_device() -> tuple[str, str]:
    if ctranslate2 is not None:
        try:
            if ctranslate2.get_cuda_device_count() > 0:
                return "cuda", "float16"
        except Exception:
            pass
    if torch is not None:
        try:
            if torch.cuda.is_available():
                return "cuda", "float16"
        except Exception:
            pass
    return "cpu", "int8"


def srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def collect_audio_files(audio_dir: Path, selected_files: Optional[Iterable[Path]] = None) -> list[Path]:
    if selected_files:
        files = []
        for p in selected_files:
            p = Path(p)
            if p.exists() and p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                files.append(p)
        return sorted(files)

    return sorted(
        p for p in audio_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    )


def transcribe_files(
    audio_paths: Iterable[Path],
    output_dir: Path,
    config: TranscribeConfig,
    progress_cb: Optional[Callable[[int, int, float, str], None]] = None,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    device, compute_type = resolve_device()
    if config.device:
        device = config.device
    if config.compute_type:
        compute_type = config.compute_type

    model = WhisperModel(config.model, device=device, compute_type=compute_type)

    results: list[Path] = []
    audio_list = list(audio_paths)
    total_files = len(audio_list)

    for index, audio_path in enumerate(audio_list, start=1):
        segments, info = model.transcribe(
            str(audio_path),
            language=None if config.language == "auto" else config.language,
            initial_prompt=config.prompt.strip() or None,
        )

        total_duration = getattr(info, "duration", None)
        if not total_duration or total_duration <= 0:
            total_duration = None

        output_format = config.output_format.lower()
        if output_format == "txt":
            out_path = output_dir / f"{audio_path.stem}.txt"
            with open(out_path, "w", encoding="utf-8") as f:
                for seg in segments:
                    text = (seg.text or "").strip()
                    if text:
                        f.write(text + "\n")
                    if progress_cb and total_duration:
                        pct = min(seg.end / total_duration * 100, 100.0)
                        progress_cb(index, total_files, pct, audio_path.name)
        elif output_format == "srt":
            out_path = output_dir / f"{audio_path.stem}.srt"
            with open(out_path, "w", encoding="utf-8") as f:
                for i, seg in enumerate(segments, start=1):
                    f.write(f"{i}\n")
                    f.write(f"{srt_timestamp(seg.start)} --> {srt_timestamp(seg.end)}\n")
                    text = (seg.text or "").strip()
                    f.write(text + "\n\n")
                    if progress_cb and total_duration:
                        pct = min(seg.end / total_duration * 100, 100.0)
                        progress_cb(index, total_files, pct, audio_path.name)
        else:
            raise ValueError(f"Formato de salida no soportado: {config.output_format}")

        if progress_cb:
            progress_cb(index, total_files, 100.0, audio_path.name)

        results.append(out_path)

    return results
