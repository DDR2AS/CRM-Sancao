import customtkinter as ctk
from version import APP_VERSION


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, command=None):
        super().__init__(master, width=220, corner_radius=0, fg_color="#1a1a2e")
        self.pack_propagate(False)
        self.command = command
        self.buttons = []

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

        # Footer
        ctk.CTkLabel(
            self,
            text=f"v{APP_VERSION}",
            font=("Segoe UI", 11),
            text_color="#5d5d7a"
        ).pack(side="bottom", anchor="w", padx=15, pady=15)

    def on_click(self, item_name):
        for item in self.buttons:
            if item["name"] == item_name:
                item["btn"].configure(fg_color="#3EA5FF", text_color="#FFFFFF")
            else:
                item["btn"].configure(fg_color="transparent", text_color="#b8b8d1")

        if self.command:
            self.command(item_name)
