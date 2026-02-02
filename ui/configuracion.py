import customtkinter as ctk
import subprocess
import threading
import sys
import os

APP_VERSION = "1.0.2"
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ConfiguracionFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="white")

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
            command=self.apply_update,
            font=("Segoe UI", 13, "bold"),
            fg_color="#28a745",
            hover_color="#218838",
            height=36,
            width=140,
            state="disabled"
        )
        self.update_btn.pack(side="left")

    def check_updates(self):
        """Check if updates are available from remote repository"""
        self.check_btn.configure(state="disabled")
        self.status_label.configure(text="Verificando...", text_color="#6C757D")

        def check():
            try:
                # Fetch latest from remote
                fetch_result = subprocess.run(
                    ["git", "fetch"],
                    cwd=APP_DIR,
                    capture_output=True,
                    text=True
                )

                if fetch_result.returncode != 0:
                    self.after(0, lambda: self.status_label.configure(
                        text="Error: No se pudo conectar al repositorio",
                        text_color="#dc3545"
                    ))
                    self.after(0, lambda: self.check_btn.configure(state="normal"))
                    return

                # Check if we're behind remote
                status_result = subprocess.run(
                    ["git", "status", "-uno"],
                    cwd=APP_DIR,
                    capture_output=True,
                    text=True
                )

                if "behind" in status_result.stdout:
                    # Get commit count
                    count_result = subprocess.run(
                        ["git", "rev-list", "--count", "HEAD..@{u}"],
                        cwd=APP_DIR,
                        capture_output=True,
                        text=True
                    )
                    commits = count_result.stdout.strip()
                    self.after(0, lambda: self.status_label.configure(
                        text=f"Hay {commits} actualización(es) disponible(s)",
                        text_color="#28a745"
                    ))
                    self.after(0, lambda: self.update_btn.configure(state="normal"))
                else:
                    self.after(0, lambda: self.status_label.configure(
                        text="Ya tienes la última versión",
                        text_color="#6C757D"
                    ))
                    self.after(0, lambda: self.update_btn.configure(state="disabled"))

            except FileNotFoundError:
                self.after(0, lambda: self.status_label.configure(
                    text="Error: Git no está instalado",
                    text_color="#dc3545"
                ))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(
                    text=f"Error: {str(e)[:40]}",
                    text_color="#dc3545"
                ))

            self.after(0, lambda: self.check_btn.configure(state="normal"))

        threading.Thread(target=check, daemon=True).start()

    def apply_update(self):
        """Pull latest changes and restart the application"""
        self.update_btn.configure(state="disabled")
        self.check_btn.configure(state="disabled")
        self.status_label.configure(text="Descargando actualizaciones...", text_color="#6C757D")

        def update():
            try:
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=APP_DIR,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    self.after(0, lambda: self.status_label.configure(
                        text="Actualización completada. Reiniciando...",
                        text_color="#28a745"
                    ))
                    # Restart the application after a short delay
                    self.after(1500, self.restart_app)
                else:
                    self.after(0, lambda: self.status_label.configure(
                        text=f"Error al actualizar: {result.stderr[:40]}",
                        text_color="#dc3545"
                    ))
                    self.after(0, lambda: self.check_btn.configure(state="normal"))
                    self.after(0, lambda: self.update_btn.configure(state="normal"))

            except Exception as e:
                self.after(0, lambda: self.status_label.configure(
                    text=f"Error: {str(e)[:40]}",
                    text_color="#dc3545"
                ))
                self.after(0, lambda: self.check_btn.configure(state="normal"))

        threading.Thread(target=update, daemon=True).start()

    def restart_app(self):
        """Restart the application"""
        python = sys.executable
        os.execl(python, python, *sys.argv)
