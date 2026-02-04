import customtkinter as ctk
import threading
import requests
from version import APP_VERSION

# GitHub repository info
GITHUB_REPO = "DDR2AS/CRM-Sancao"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, command=None):
        super().__init__(master, width=220, corner_radius=0, fg_color="#1a1a2e")
        self.pack_propagate(False)
        self.command = command
        self.buttons = []
        self.update_available = False

        self.menu_items = [
            {"name": "Dashboard", "icon": "📊"},
            {"name": "Reporte Semanal", "icon": "📈"},
            {"name": "Gastos", "icon": "💰"},
            {"name": "Jornales", "icon": "👷"},
            {"name": "Venta de Cacao", "icon": "🍫"},
            {"name": "Enviado", "icon": "📤"},
            {"name": "Configuración", "icon": "⚙️"},
        ]

        # Header
        ctk.CTkLabel(
            self,
            text="🌿 CRM SANCAO",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=15, pady=(20, 25))

        # Menu buttons
        for item in self.menu_items:
            btn = ctk.CTkButton(
                self,
                text=f"  {item['icon']}   {item['name']}",
                command=lambda name=item["name"]: self.on_click(name),
                font=("Segoe UI", 14),
                text_color="#b8b8d1",
                fg_color="transparent",
                hover_color="#2d2d44",
                anchor="w",
                height=42,
                corner_radius=8
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.buttons.append({"name": item["name"], "btn": btn})

        # Footer frame
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=15, pady=15)

        # Version label (left side)
        ctk.CTkLabel(
            footer_frame,
            text=f"v{APP_VERSION}",
            font=("Segoe UI", 11),
            text_color="#5d5d7a"
        ).pack(side="left")

        # Update notification icon (right side) - hidden by default
        self.update_icon = ctk.CTkButton(
            footer_frame,
            text="🔔",
            font=("Segoe UI", 16),
            width=32,
            height=32,
            fg_color="#ff4757",
            hover_color="#ff6b7a",
            corner_radius=16,
            command=self.on_update_click
        )
        # Icon is hidden initially, shown when update is available

        # Check for updates in background on startup
        self.check_updates_background()

    def check_updates_background(self):
        """Check for updates silently in the background"""
        def check():
            try:
                response = requests.get(GITHUB_API_URL, timeout=10)
                if response.status_code == 200:
                    release_data = response.json()
                    latest_version = release_data.get('tag_name', '').lstrip('v')

                    # Check if .exe exists in release
                    assets = release_data.get('assets', [])
                    has_exe = any(asset['name'] == 'CRM-Sancao.exe' for asset in assets)

                    if has_exe and self.compare_versions(latest_version, APP_VERSION):
                        self.update_available = True
                        self.after(0, self.show_update_notification)
            except:
                pass  # Silently fail - no notification if can't check

        threading.Thread(target=check, daemon=True).start()

    def compare_versions(self, v1, v2):
        """Compare two version strings. Returns True if v1 > v2"""
        def parse_version(v):
            v = v.lstrip('v')
            return [int(x) for x in v.split('.')]
        try:
            parts1 = parse_version(v1)
            parts2 = parse_version(v2)
            return parts1 > parts2
        except:
            return False

    def show_update_notification(self):
        """Show the update notification icon"""
        self.update_icon.pack(side="right")
        # Add a subtle animation effect by pulsing
        self.pulse_icon()

    def pulse_icon(self):
        """Create a subtle pulse effect on the notification icon"""
        if not self.update_available:
            return

        def animate(step=0):
            if not self.update_available:
                return
            colors = ["#ff4757", "#ff6b7a", "#ff4757"]
            self.update_icon.configure(fg_color=colors[step % 3])
            if self.update_available:
                self.after(500, lambda: animate(step + 1))

        animate()

    def on_update_click(self):
        """Navigate to Configuración when update icon is clicked"""
        self.on_click("Configuración")

    def hide_update_notification(self):
        """Hide the update notification icon"""
        self.update_available = False
        self.update_icon.pack_forget()

    def on_click(self, item_name):
        for item in self.buttons:
            if item["name"] == item_name:
                item["btn"].configure(fg_color="#3EA5FF", text_color="#FFFFFF")
            else:
                item["btn"].configure(fg_color="transparent", text_color="#b8b8d1")

        if self.command:
            self.command(item_name)
