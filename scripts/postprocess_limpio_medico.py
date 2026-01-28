import re
from pathlib import Path

# ---------- CONFIGURACIÓN ----------
INPUT_DIR = Path("../pruebas/salida")
OUTPUT_SUFFIX = "_limpio"

# ---------- REGLAS ----------
# Muletillas comunes (eliminación suave)
MULETILLAS = [
    r"\beh\b", r"\beste\b", r"\bbueno\b", r"\bentonces\b", r"\b¿no\?\b",
    r"\bmmm\b", r"\bmm\b"
]

# Correcciones médicas determinísticas (cerradas)
CORRECCIONES = {
    r"\bericipela\b": "erisipela",
    r"\beris\s*y\s*pel[aá]\b": "erisipela",
    r"\bestreto\s*coco\b": "estreptococo",
    r"\bgas\b": "estreptococo del grupo A (GAS)",
    r"\bcutibacterium\s+agnes\b": "Cutibacterium acnes",
    r"\bpropionibacterium\s+agnes\b": "Propionibacterium acnes",
    r"\bcephaloporina\b": "cefalosporina",
}

# ---------- UTILIDADES ----------
def limpiar_linea(linea: str) -> str:
    texto = linea

    # Eliminar muletillas (case-insensitive)
    for m in MULETILLAS:
        texto = re.sub(m, "", texto, flags=re.IGNORECASE)

    # Correcciones médicas
    for patron, reemplazo in CORRECCIONES.items():
        texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)

    # Normalizaciones suaves
    texto = re.sub(r"\s{2,}", " ", texto)   # espacios múltiples
    texto = texto.strip()

    return texto

# ---------- MAIN ----------
def main():
    if not INPUT_DIR.exists():
        print("❌ No existe la carpeta de entrada:", INPUT_DIR)
        return

    archivos = list(INPUT_DIR.glob("*.txt"))
    if not archivos:
        print("❌ No se encontraron .txt para procesar.")
        return

    print(f"🧼 Procesando {len(archivos)} archivos...")

    for path in archivos:
        if path.stem.endswith(OUTPUT_SUFFIX):
            continue  # evita reprocesar

        out_path = path.with_name(f"{path.stem}{OUTPUT_SUFFIX}.txt")

        with open(path, "r", encoding="utf-8") as fin, \
             open(out_path, "w", encoding="utf-8") as fout:

            for linea in fin:
                limpia = limpiar_linea(linea)
                if limpia:  # evita líneas vacías
                    fout.write(limpia + "\n")

        print(f"✅ Generado: {out_path.name}")

    print("🎉 BLOQUE 10 – limpieza mínima completada.")


if __name__ == "__main__":
    main()
