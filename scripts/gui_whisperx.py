import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
import threading
import subprocess
import os
import sys

# ---------- FIX ENCODING WINDOWS ----------
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------- CONFIG ----------
SUPPORTED_EXTS = (".mp3", ".wav", ".m4a", ".mp4")

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_BATCH = SCRIPT_DIR / "batch_whisperx_lib.py"
SCRIPT_POST = SCRIPT_DIR / "postprocess_limpio_medico.py"


class WhisperXGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("WhisperX – Transcriptor académico")
        self.geometry("620x420")
        self.resizable(False, False)

        self.audio_dir: Path | None = None
        self.audio_files: list[Path] = []

        self.status = tk.StringVar(value="Listo.")
        self.progress = tk.DoubleVar(value=0)

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        ttk.Label(
            self,
            text="WhisperX – Transcriptor académico",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=10)

        ttk.Button(
            self,
            text="📂 Seleccionar carpeta de audios",
            command=self.select_folder
        ).pack(fill="x", padx=15)

        ttk.Label(
            self,
            text="Archivos detectados (selecciona uno o varios):"
        ).pack(anchor="w", padx=15, pady=(10, 0))

        self.listbox = tk.Listbox(
            self,
            selectmode="extended",
            height=10
        )
        self.listbox.pack(fill="both", expand=True, padx=15)

        ttk.Button(
            self,
            text="▶ Iniciar transcripción",
            command=self.start_process
        ).pack(pady=10)

        self.bar = ttk.Progressbar(
            self,
            variable=self.progress,
            maximum=100
        )
        self.bar.pack(fill="x", padx=20)

        ttk.Label(self, textvariable=self.status).pack(pady=6)

        ttk.Button(
            self,
            text="🧼 Post-procesar textos",
            command=self.run_postprocess
        ).pack(pady=4)

        ttk.Button(
            self,
            text="📁 Abrir carpeta de resultados",
            command=self.open_output
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

        for f in sorted(self.audio_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                self.audio_files.append(f)
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
            daemon=True
        ).start()

    def run_batch(self, selected_files: list[Path]):
        try:
            cmd = [
                sys.executable,
                "-u",
                str(SCRIPT_BATCH),
                str(self.audio_dir)
            ]

            # si hay selección → solo esos archivos
            for f in selected_files:
                cmd.append(str(f))

            process = subprocess.Popen(
                cmd,
                cwd=str(self.audio_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("PROGRESS"):
                    try:
                        pct = float(line.split()[1].replace("%", ""))
                        self.progress.set(pct)
                    except Exception:
                        pass
                else:
                    self.status.set(line)

            self.progress.set(100)
            self.status.set("✅ Transcripción finalizada.")

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
            subprocess.run(
                [sys.executable, str(SCRIPT_POST), str(salida)],
                check=True
            )
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


# ---------- MAIN ----------
if __name__ == "__main__":
    WhisperXGUI().mainloop()
