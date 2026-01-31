import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
import threading
import os
import sys
import subprocess

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config import (
    DEFAULT_MODEL,
    DEFAULT_LANGUAGE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_PROMPT,
)
from transcribe_core import TranscribeConfig, collect_audio_files, transcribe_files, resolve_device

# ---------- FIX ENCODING WINDOWS ----------
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SCRIPT_POST = SCRIPT_DIR / "postprocess_limpio_medico.py"


class WhisperXGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("WhisperX – Transcriptor académico")
        self.geometry("640x520")
        self.resizable(False, False)

        self.audio_dir: Path | None = None
        self.audio_files: list[Path] = []

        self.status = tk.StringVar(value="Listo.")
        self.progress = tk.DoubleVar(value=0)

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        header = ttk.Label(
            self,
            text="WhisperX – Transcriptor académico",
            font=("Segoe UI", 12, "bold"),
        )
        header.pack(pady=8)

        ttk.Button(
            self,
            text="📂 Seleccionar carpeta de audios",
            command=self.select_folder,
        ).pack(fill="x", padx=15)

        self.options_frame = ttk.Frame(self)
        self.options_frame.pack(fill="x", padx=15, pady=8)

        ttk.Label(self.options_frame, text="Modelo:").grid(row=0, column=0, sticky="w")
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.model_box = ttk.Combobox(
            self.options_frame,
            textvariable=self.model_var,
            values=("tiny", "base", "small", "medium", "large-v2"),
            width=12,
        )
        self.model_box.grid(row=0, column=1, padx=6, sticky="w")

        ttk.Label(self.options_frame, text="Idioma:").grid(row=0, column=2, sticky="w")
        self.lang_var = tk.StringVar(value=DEFAULT_LANGUAGE)
        self.lang_box = ttk.Combobox(
            self.options_frame,
            textvariable=self.lang_var,
            values=("es", "auto"),
            width=8,
            state="readonly",
        )
        self.lang_box.grid(row=0, column=3, padx=6, sticky="w")

        ttk.Label(self.options_frame, text="Formato:").grid(row=0, column=4, sticky="w")
        self.format_var = tk.StringVar(value=DEFAULT_OUTPUT_FORMAT)
        self.format_box = ttk.Combobox(
            self.options_frame,
            textvariable=self.format_var,
            values=("txt", "srt"),
            width=8,
            state="readonly",
        )
        self.format_box.grid(row=0, column=5, padx=6, sticky="w")

        device, compute_type = resolve_device()
        self.device_label = ttk.Label(
            self.options_frame,
            text=f"Dispositivo: {device} ({compute_type})",
        )
        self.device_label.grid(row=1, column=0, columnspan=6, sticky="w", pady=(4, 0))

        ttk.Label(
            self,
            text="Contexto / prompt (editable):",
        ).pack(anchor="w", padx=15)

        self.prompt_text = tk.Text(self, height=4, wrap="word")
        self.prompt_text.pack(fill="x", padx=15, pady=(0, 8))
        self.prompt_text.insert("1.0", DEFAULT_PROMPT)

        ttk.Label(
            self,
            text="Archivos detectados (selecciona uno o varios):",
        ).pack(anchor="w", padx=15, pady=(4, 0))

        self.listbox = tk.Listbox(self, selectmode="extended", height=10)
        self.listbox.pack(fill="both", expand=True, padx=15)

        ttk.Button(
            self,
            text="▶ Iniciar transcripción",
            command=self.start_process,
        ).pack(pady=8)

        self.bar = ttk.Progressbar(self, variable=self.progress, maximum=100)
        self.bar.pack(fill="x", padx=20)

        ttk.Label(self, textvariable=self.status).pack(pady=6)

        ttk.Button(
            self,
            text="🧼 Post-procesar textos",
            command=self.run_postprocess,
        ).pack(pady=4)

        ttk.Button(
            self,
            text="📁 Abrir carpeta de resultados",
            command=self.open_output,
        ).pack()

    # ---------- LOGIC ----------
    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.audio_dir = Path(folder)
        self.scan_audios()

    def scan_audios(self):
        self.listbox.delete(0, tk.END)
        self.audio_files.clear()

        if not self.audio_dir or not self.audio_dir.exists():
            return

        self.audio_files = collect_audio_files(self.audio_dir)
        for f in self.audio_files:
            name = f.name.encode("utf-8", "replace").decode("utf-8")
            self.listbox.insert(tk.END, name)

        if not self.audio_files:
            self.status.set("⚠️ No se encontraron audios compatibles.")
        else:
            self.status.set(f"🎧 {len(self.audio_files)} audios detectados.")

    def start_process(self):
        if not self.audio_files or not self.audio_dir:
            messagebox.showwarning("Sin audios", "No hay audios para procesar.")
            return

        selected_indices = self.listbox.curselection()
        selected_files = [self.audio_files[i] for i in selected_indices]

        self.progress.set(0)
        self.status.set("Procesando transcripción...")

        threading.Thread(
            target=self.run_batch,
            args=(selected_files,),
            daemon=True,
        ).start()

    def run_batch(self, selected_files: list[Path]):
        try:
            if not self.audio_dir:
                return

            files = selected_files or self.audio_files
            output_dir = self.audio_dir / "salida"

            config = TranscribeConfig(
                model=self.model_var.get().strip() or DEFAULT_MODEL,
                language=self.lang_var.get().strip() or DEFAULT_LANGUAGE,
                output_format=self.format_var.get().strip() or DEFAULT_OUTPUT_FORMAT,
                prompt=self.prompt_text.get("1.0", "end").strip(),
            )

            def on_progress(file_index: int, total_files: int, file_pct: float, filename: str):
                overall = ((file_index - 1) + (file_pct / 100.0)) / max(total_files, 1) * 100.0
                self._set_progress(overall)
                self._set_status(f"{filename} ({file_index}/{total_files}) {file_pct:.1f}%")

            transcribe_files(files, output_dir, config, progress_cb=on_progress)

            self._set_progress(100)
            self._set_status("✅ Transcripción finalizada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_postprocess(self):
        if not self.audio_dir:
            messagebox.showwarning("Sin carpeta", "Primero selecciona una carpeta de audios.")
            return

        salida = self.audio_dir / "salida"
        if not salida.exists():
            messagebox.showwarning("Sin salida", "No existe la carpeta de salida.")
            return

        try:
            subprocess.run([sys.executable, str(SCRIPT_POST), str(salida)], check=True)
            self.status.set("🧼 Post-proceso completado.")
        except Exception as e:
            messagebox.showerror("Error post-proceso", str(e))

    def open_output(self):
        if not self.audio_dir:
            return

        salida = self.audio_dir / "salida"
        if salida.exists():
            os.startfile(salida)
        else:
            messagebox.showinfo("Info", "Aún no existe la carpeta salida.")

    def _set_status(self, text: str):
        self.after(0, lambda: self.status.set(text))

    def _set_progress(self, value: float):
        self.after(0, lambda: self.progress.set(value))


if __name__ == "__main__":
    WhisperXGUI().mainloop()
