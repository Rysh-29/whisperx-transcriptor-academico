import subprocess
from pathlib import Path

# ===== CONFIGURACIÓN =====
AUDIO_DIR = Path("../pruebas")
OUTPUT_DIR = AUDIO_DIR / "salida"

MODEL = "medium"
LANGUAGE = "es"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"

INITIAL_PROMPT = (
    "Clase universitaria de medicina, vocabulario clínico, "
    "términos técnicos, español formal"
)

EXTENSIONES_VALIDAS = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}

# =========================

def main():
    print("📂 Contenido de la carpeta de audios:")
    for f in AUDIO_DIR.iterdir():
        print(" -", f.name, "| ext:", f.suffix)

    audios = [
        f for f in AUDIO_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONES_VALIDAS
    ]

    if not audios:
        print("❌ No se encontraron audios.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    total = len(audios)
    print(f"🎧 Audios encontrados: {total}\n")

    for i, audio in enumerate(audios, start=1):
        print(f"▶️ [{i}/{total}] Transcribiendo: {audio.name}")

        cmd = [
            "whisperx",
            str(audio),
            "--model", MODEL,
            "--language", LANGUAGE,
            "--device", DEVICE,
            "--compute_type", COMPUTE_TYPE,
            "--initial_prompt", INITIAL_PROMPT,
            "--output_dir", str(OUTPUT_DIR),
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"✅ Completado: {audio.name}\n")
        except subprocess.CalledProcessError:
            print(f"❌ Error al procesar: {audio.name}\n")

    print("🎉 Transcripción batch finalizada.")

if __name__ == "__main__":
    main()
