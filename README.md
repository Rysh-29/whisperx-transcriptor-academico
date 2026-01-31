# WhisperX – Transcriptor Académico

WhisperX – Transcriptor Académico es una GUI para transcribir audios usando faster-whisper (con soporte de GPU si hay CUDA). Permite seleccionar una carpeta de audios, elegir múltiples archivos y ver el progreso de la transcripción. Incluye un post-proceso opcional para limpiar textos.

## Funcionalidades principales
- Selección de carpeta de audios
- Selección múltiple de archivos
- Barra de progreso con porcentaje
- Post-proceso de textos
- Selección de modelo, idioma, formato y prompt

## Requisitos
- Python 3.10–3.11
- faster-whisper
- CUDA opcional (recomendado para aceleración)

## Ejecución
Desde la carpeta `scripts/` (o desde la raíz usando `python scripts/gui_whisperx.py`):

```bash
python gui_whisperx.py
```
