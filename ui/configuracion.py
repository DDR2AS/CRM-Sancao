import customtkinter as ctk
import threading
import sys
import os
import requests
import tempfile
import subprocess
from version import APP_VERSION

# GitHub repository info
GITHUB_REPO = "DDR2AS/CRM-Sancao"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
EXE_NAME = "CRM-Sancao.exe"


class ConfiguracionFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white")

        self.latest_version = None
        self.download_url = None

        # Header
        header = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="Configuración",
            font=("Segoe UI", 24, "bold"),
            text_color="#1a1a2e"
        ).pack(anchor="w", padx=25, pady=15)

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=20)

        # Update Section
        update_frame = ctk.CTkFrame(content, fg_color="#F8F9FA", corner_radius=10)
        update_frame.pack(fill="x", pady=(0, 15))

        update_inner = ctk.CTkFrame(update_frame, fg_color="transparent")
        update_inner.pack(fill="x", padx=20, pady=15)

        # Title row
        title_row = ctk.CTkFrame(update_inner, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text="Actualizaciones",
            font=("Segoe UI", 16, "bold"),
            text_color="#1a1a2e"
        ).pack(side="left")

        ctk.CTkLabel(
            title_row,
            text=f"v{APP_VERSION}",
            font=("Segoe UI", 12),
            text_color="#6C757D"
        ).pack(side="right")

        # Status label
        self.status_label = ctk.CTkLabel(
            update_inner,
            text="",
            font=("Segoe UI", 12),
            text_color="#6C757D"
        )
        self.status_label.pack(anchor="w", pady=(5, 10))

        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(update_inner, width=300)
        self.progress_bar.set(0)

        # Buttons row
        btn_row = ctk.CTkFrame(update_inner, fg_color="transparent")
        btn_row.pack(fill="x")

        self.check_btn = ctk.CTkButton(
            btn_row,
            text="Verificar actualizaciones",
            command=self.check_updates,
            font=("Segoe UI", 13, "bold"),
            fg_color="#3EA5FF",
            hover_color="#2196F3",
            height=36,
            width=180
        )
        self.check_btn.pack(side="left", padx=(0, 10))

        self.update_btn = ctk.CTkButton(
            btn_row,
            text="Actualizar ahora",
            command=self.confirm_update,
            font=("Segoe UI", 13, "bold"),
            fg_color="#28a745",
            hover_color="#218838",
            height=36,
            width=140,
            state="disabled"
        )
        self.update_btn.pack(side="left")

    def compare_versions(self, v1, v2):
        """Compare two version strings. Returns True if v1 > v2"""
        def parse_version(v):
            # Remove 'v' prefix if present
            v = v.lstrip('v')
            return [int(x) for x in v.split('.')]

        try:
            parts1 = parse_version(v1)
            parts2 = parse_version(v2)
            return parts1 > parts2
        except:
            return False

    def check_updates(self):
        """Check if updates are available from GitHub Releases"""
        self.check_btn.configure(state="disabled")
        self.status_label.configure(text="Verificando...", text_color="#6C757D")

        def check():
            try:
                # Get latest release from GitHub API
                response = requests.get(GITHUB_API_URL, timeout=10)

                if response.status_code == 404:
                    self.after(0, lambda: self.status_label.configure(
                        text="No hay releases disponibles",
                        text_color="#6C757D"
                    ))
                    self.after(0, lambda: self.check_btn.configure(state="normal"))
                    return

                if response.status_code != 200:
                    self.after(0, lambda: self.status_label.configure(
                        text="Error: No se pudo conectar a GitHub",
                        text_color="#dc3545"
                    ))
                    self.after(0, lambda: self.check_btn.configure(state="normal"))
                    return

                release_data = response.json()
                self.latest_version = release_data.get('tag_name', '').lstrip('v')

                # Find the .exe asset
                assets = release_data.get('assets', [])
                self.download_url = None
                for asset in assets:
                    if asset['name'] == EXE_NAME:
                        self.download_url = asset['browser_download_url']
                        break

                if not self.download_url:
                    self.after(0, lambda: self.status_label.configure(
                        text="Error: No se encontró el archivo .exe en el release",
                        text_color="#dc3545"
                    ))
                    self.after(0, lambda: self.check_btn.configure(state="normal"))
                    return

                # Compare versions
                if self.compare_versions(self.latest_version, APP_VERSION):
                    self.after(0, lambda: self.status_label.configure(
                        text=f"Nueva versión disponible: v{self.latest_version}",
                        text_color="#28a745"
                    ))
                    self.after(0, lambda: self.update_btn.configure(state="normal"))
                else:
                    self.after(0, lambda: self.status_label.configure(
                        text=f"Ya tienes la última versión (v{APP_VERSION})",
                        text_color="#6C757D"
                    ))
                    self.after(0, lambda: self.update_btn.configure(state="disabled"))

            except requests.exceptions.Timeout:
                self.after(0, lambda: self.status_label.configure(
                    text="Error: Tiempo de espera agotado",
                    text_color="#dc3545"
                ))
            except requests.exceptions.ConnectionError:
                self.after(0, lambda: self.status_label.configure(
                    text="Error: Sin conexión a internet",
                    text_color="#dc3545"
                ))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(
                    text=f"Error: {str(e)[:40]}",
                    text_color="#dc3545"
                ))

            self.after(0, lambda: self.check_btn.configure(state="normal"))

        threading.Thread(target=check, daemon=True).start()

    def confirm_update(self):
        """Show confirmation dialog before updating"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirmar actualización")
        dialog.geometry("400x180")
        dialog.transient(self)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 180) // 2
        dialog.geometry(f"400x180+{x}+{y}")

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="¿Actualizar ahora?",
            font=("Segoe UI", 18, "bold"),
            text_color="#1a1a2e"
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            frame,
            text=f"Se descargará e instalará la versión v{self.latest_version}\nLa aplicación se reiniciará automáticamente.",
            font=("Segoe UI", 12),
            text_color="#6C757D"
        ).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=dialog.destroy,
            font=("Segoe UI", 13),
            fg_color="#6C757D",
            hover_color="#5a6268",
            width=100
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Actualizar",
            command=lambda: self.start_update(dialog),
            font=("Segoe UI", 13, "bold"),
            fg_color="#28a745",
            hover_color="#218838",
            width=100
        ).pack(side="left")

    def start_update(self, dialog):
        """Start the update process"""
        dialog.destroy()
        self.apply_update()

    def apply_update(self):
        """Download and install the update"""
        self.update_btn.configure(state="disabled")
        self.check_btn.configure(state="disabled")
        self.status_label.configure(text="Descargando actualización...", text_color="#6C757D")
        self.progress_bar.pack(anchor="w", pady=(0, 10))
        self.progress_bar.set(0)

        def update():
            try:
                # Get the current exe path
                if getattr(sys, 'frozen', False):
                    # Running as compiled exe
                    current_exe = sys.executable
                else:
                    # Running as script - for testing
                    current_exe = os.path.join(os.path.dirname(os.path.dirname(__file__)), EXE_NAME)

                exe_dir = os.path.dirname(current_exe)
                new_exe_path = os.path.join(exe_dir, f"{EXE_NAME}.new")

                # Download the new exe
                response = requests.get(self.download_url, stream=True, timeout=300)
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(new_exe_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = downloaded / total_size
                                self.after(0, lambda p=progress: self.progress_bar.set(p))

                self.after(0, lambda: self.status_label.configure(
                    text="Instalando actualización...",
                    text_color="#6C757D"
                ))

                # Create a batch script to replace the exe and restart
                batch_script = os.path.join(exe_dir, "update.bat")
                with open(batch_script, 'w') as f:
                    f.write(f'''@echo off
timeout /t 2 /nobreak > nul
del "{current_exe}"
move "{new_exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
''')

                self.after(0, lambda: self.status_label.configure(
                    text="Reiniciando aplicación...",
                    text_color="#28a745"
                ))

                # Run the batch script and exit
                self.after(1000, lambda: self.run_update_script(batch_script))

            except Exception as e:
                self.after(0, lambda: self.status_label.configure(
                    text=f"Error: {str(e)[:40]}",
                    text_color="#dc3545"
                ))
                self.after(0, lambda: self.progress_bar.pack_forget())
                self.after(0, lambda: self.check_btn.configure(state="normal"))
                self.after(0, lambda: self.update_btn.configure(state="normal"))

                # Clean up failed download
                try:
                    if os.path.exists(new_exe_path):
                        os.remove(new_exe_path)
                except:
                    pass

        threading.Thread(target=update, daemon=True).start()

    def run_update_script(self, batch_script):
        """Run the update batch script and exit the application"""
        subprocess.Popen(
            ['cmd', '/c', batch_script],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            close_fds=True
        )
        sys.exit(0)
