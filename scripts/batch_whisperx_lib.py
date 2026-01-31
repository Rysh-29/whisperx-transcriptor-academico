import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config import DEFAULT_MODEL, DEFAULT_LANGUAGE, DEFAULT_OUTPUT_FORMAT, DEFAULT_PROMPT
from transcribe_core import TranscribeConfig, collect_audio_files, transcribe_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcripción batch con faster-whisper")
    parser.add_argument("audio_dir", help="Carpeta con audios")
    parser.add_argument("files", nargs="*", help="Archivos específicos dentro de la carpeta")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, choices=["es", "auto"])
    parser.add_argument("--output_format", default=DEFAULT_OUTPUT_FORMAT, choices=["txt", "srt"])
    parser.add_argument("--initial_prompt", default=DEFAULT_PROMPT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audio_dir = Path(args.audio_dir).expanduser().resolve()
    if not audio_dir.exists() or not audio_dir.is_dir():
        print(f"ERROR: La carpeta no existe o no es válida: {audio_dir}")
        return 2

    selected_files = [Path(p).expanduser().resolve() for p in args.files] if args.files else None
    audio_files = collect_audio_files(audio_dir, selected_files)
    if not audio_files:
        print("No se encontraron audios compatibles.")
        return 2

    output_dir = audio_dir / "salida"
    config = TranscribeConfig(
        model=args.model,
        language=args.language,
        output_format=args.output_format,
        prompt=args.initial_prompt,
    )

    def on_progress(file_index: int, total_files: int, file_pct: float, filename: str):
        overall = ((file_index - 1) + (file_pct / 100.0)) / max(total_files, 1) * 100.0
        print(f"{filename} {overall:.1f}%")

    transcribe_files(audio_files, output_dir, config, progress_cb=on_progress)
    print("Transcripción finalizada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
