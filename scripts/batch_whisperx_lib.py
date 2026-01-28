import whisperx
import torch
import torchaudio
from pathlib import Path
import sys

# ---------- CONFIG ----------
MODEL_NAME = "medium"
LANGUAGE = "es"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

SCRIPT_BATCH = "batch_whisperx_lib.py"
SCRIPT_POST = "postprocess_limpio_medico.py"
SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_BATCH_PATH = (SCRIPT_DIR / SCRIPT_BATCH).resolve()
SCRIPT_POST_PATH = (SCRIPT_DIR / SCRIPT_POST).resolve()

SUPPORTED_EXTS = [".mp3", ".wav", ".m4a", ".mp4"]

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

print("[DIAG] batch_whisperx_lib.py", flush=True)
print(f"[DIAG] __file__={__file__}", flush=True)
print(f"[DIAG] cwd={Path.cwd()}", flush=True)
print(f"[DIAG] sys.executable={sys.executable}", flush=True)
print(f"[DIAG] sys.argv={sys.argv}", flush=True)
print(f"[DIAG] SCRIPT_BATCH resolve={SCRIPT_BATCH_PATH}", flush=True)
print(f"[DIAG] SCRIPT_POST resolve={SCRIPT_POST_PATH}", flush=True)

# ---------- UTILIDADES ----------
def barra_progreso(porcentaje, ancho=30):
    completado = int(ancho * porcentaje / 100)
    restante = ancho - completado
    return "[" + "#" * completado + "-" * restante + f"] {porcentaje:5.1f}%"

def safe_print(text):
    if not isinstance(text, str):
        text = str(text)
    print(text.encode("utf-8", "replace").decode("utf-8"), flush=True)

# ---------- MAIN ----------
def main(audio_dir_path, selected_files=None):
    audio_dir = Path(audio_dir_path).expanduser().resolve()
    if not audio_dir.exists() or not audio_dir.is_dir():
        safe_print(f"ERROR: La carpeta no existe o no es valida: {audio_dir}")
        return 2

    output_dir = audio_dir / "salida"
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_print("Iniciando WhisperX como libreria")
    safe_print(f"Dispositivo: {DEVICE}")
    safe_print(f"Modelo: {MODEL_NAME}")
    safe_print(f"Carpeta de audios: {audio_dir}")

    all_files = []
    if selected_files:
        for p in selected_files:
            if p.exists() and p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                all_files.append(p)
            else:
                safe_print(f"AVISO: archivo invalido o no soportado: {p}")

        if not all_files:
            safe_print("No hay archivos seleccionados validos. Usando carpeta completa.")
            selected_files = None

    if selected_files is None:
        all_files = [p for p in audio_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]

    counts = {ext: 0 for ext in SUPPORTED_EXTS}
    for p in all_files:
        counts[p.suffix.lower()] += 1

    if not all_files:
        safe_print("No se encontraron audios.")
        safe_print("Extensiones soportadas: " + ", ".join(SUPPORTED_EXTS))
        safe_print("Conteo por extension:")
        for ext in SUPPORTED_EXTS:
            safe_print(f"  {ext}: {counts[ext]}")
        return 2

    safe_print(f"Audios encontrados: {len(all_files)}")

    # Cargar modelo una sola vez
    model = whisperx.load_model(
        MODEL_NAME,
        DEVICE,
        compute_type=COMPUTE_TYPE,
        language=LANGUAGE
    )

    processed_any = False
    for i, audio_path in enumerate(sorted(all_files), start=1):
        safe_print(f"Procesando: {audio_path.name} ({i}/{len(all_files)})")

        try:
            waveform, sr = torchaudio.load(audio_path)
        except Exception as e:
            if audio_path.suffix.lower() == ".mp4":
                safe_print(
                    f"AVISO: no se pudo leer .mp4 directo: {audio_path.name}. "
                    "Convierte a .mp3/.wav/.m4a."
                )
            else:
                safe_print(f"ERROR: no se pudo leer {audio_path.name}: {e}")
            continue

        duracion_total = waveform.shape[1] / sr if sr else 0.0
        if duracion_total <= 0:
            safe_print(f"ERROR: duracion invalida para {audio_path.name}")
            continue

        result = model.transcribe(str(audio_path))

        out_txt = output_dir / f"{audio_path.stem}.txt"
        last_pct = -1.0
        with open(out_txt, "w", encoding="utf-8") as f:
            for seg in result.get("segments", []):
                texto = seg.get("text", "").strip()
                if texto:
                    f.write(texto + "\n")

                progreso = min((seg.get("end", 0.0) / duracion_total) * 100, 100)
                if progreso - last_pct >= 1.0 or progreso >= 100:
                    last_pct = progreso
                    print(f"PROGRESS {progreso:.1f}%", flush=True)
                    print(f"Transcribiendo {barra_progreso(progreso)}", flush=True)

        safe_print(f"Guardado: {out_txt.name}")
        processed_any = True

    if not processed_any:
        safe_print("No se pudieron procesar archivos. Verifica formatos y codecs.")
        return 2

    safe_print("Transcripcion finalizada.")
    return 0

# ---------- ENTRY ----------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        safe_print("ERROR: Debes indicar la carpeta de audios como argumento.")
        sys.exit(1)

    audio_dir_arg = sys.argv[1]
    selected_args = sys.argv[2:]
    selected_files = [Path(p).expanduser().resolve() for p in selected_args] if selected_args else None
    sys.exit(main(audio_dir_arg, selected_files))
