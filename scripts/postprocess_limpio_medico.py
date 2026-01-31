import re
import sys
from pathlib import Path

# ---------- CONFIGURACIÓN ----------
DEFAULT_INPUT_DIR = Path("./salida")
OUTPUT_SUFFIX = "_limpio"

# ---------- REGLAS ----------
MULETILLAS = [
    r"\beh\b", r"\beste\b", r"\bbueno\b", r"\bentonces\b", r"\b¿no\?\b",
    r"\bmmm\b", r"\bmm\b",
]

CORRECCIONES = {
    r"\bericipela\b": "erisipela",
    r"\beris\s*y\s*pel[aá]\b": "erisipela",
    r"\bestreto\s*coco\b": "estreptococo",
    r"\bgas\b": "estreptococo del grupo A (GAS)",
    r"\bcutibacterium\s+agnes\b": "Cutibacterium acnes",
    r"\bpropionibacterium\s+agnes\b": "Propionibacterium acnes",
    r"\bcephaloporina\b": "cefalosporina",
}


def limpiar_linea(linea: str) -> str:
    texto = linea
    for m in MULETILLAS:
        texto = re.sub(m, "", texto, flags=re.IGNORECASE)
    for patron, reemplazo in CORRECCIONES.items():
        texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s{2,}", " ", texto)
    return texto.strip()


def main() -> int:
    input_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT_DIR
    input_dir = input_dir.expanduser().resolve()

    if not input_dir.exists():
        print("❌ No existe la carpeta de entrada:", input_dir)
        return 2

    archivos = list(input_dir.glob("*.txt"))
    if not archivos:
        print("❌ No se encontraron .txt para procesar.")
        return 2

    print(f"🧼 Procesando {len(archivos)} archivos...")

    for path in archivos:
        if path.stem.endswith(OUTPUT_SUFFIX):
            continue

        out_path = path.with_name(f"{path.stem}{OUTPUT_SUFFIX}.txt")
        with open(path, "r", encoding="utf-8") as fin, open(out_path, "w", encoding="utf-8") as fout:
            for linea in fin:
                limpia = limpiar_linea(linea)
                if limpia:
                    fout.write(limpia + "\n")

        print(f"✅ Generado: {out_path.name}")

    print("🎉 Limpieza mínima completada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
