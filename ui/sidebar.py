import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, command=None):
        self.expanded_width = 250
        self.collapsed_width = 70
        super().__init__(master, width=self.expanded_width, corner_radius=0, fg_color="#1a1a2e")
        self.pack_propagate(False)
        self.grid_propagate(False)
        self.master = master

        self.menu_items = [
            {"name": "Dashboard", "icon": "📊"},
            {"name": "Reporte Semanal", "icon": "📈"},
            {"name": "Gastos", "icon": "💰"},
            {"name": "Jornales", "icon": "👷"},
            {"name": "Venta de Cacao", "icon": "🍫"},
            {"name": "Enviado", "icon": "📤"},
            {"name": "Configuración", "icon": "⚙️"},
        ]
        self.command = command
        self.expanded = True
        self.active_button = None

        # ========== TOGGLE BUTTON ==========
        toggle_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        toggle_frame.pack(fill="x", padx=15, pady=(15, 5))

        self.toggle_btn = ctk.CTkButton(
            toggle_frame,
            text="◀ Ocultar",
            command=self.toggle,
            font=("Segoe UI", 13, "bold"),
            text_color="#7f8c8d",
            fg_color="transparent",
            hover_color="#2d2d44",
            anchor="w",
            width=100,
            height=32
        )
        self.toggle_btn.pack(anchor="w")

        # ========== HEADER ==========
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.header_frame.pack(fill="x", padx=15, pady=(10, 10))

        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="🌿 CRM SANCAO",
            font=("Segoe UI", 20, "bold"),
            text_color="#FFFFFF"
        )
        self.header_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Sistema de Gestión",
            font=("Segoe UI", 13),
            text_color="#7f8c8d"
        )
        self.subtitle_label.pack(anchor="w")

        # ========== SEPARATOR ==========
        self.separator = ctk.CTkFrame(self, height=2, fg_color="#2d2d44")
        self.separator.pack(fill="x", padx=15, pady=(10, 15))

        # ========== MENU LABEL ==========
        self.menu_label = ctk.CTkLabel(
            self,
            text="MENÚ PRINCIPAL",
            font=("Segoe UI", 12, "bold"),
            text_color="#5d5d7a"
        )
        self.menu_label.pack(anchor="w", padx=20, pady=(0, 10))

        # ========== MENU BUTTONS ==========
        self.buttons = []
        self.button_frames = []

        for item in self.menu_items:
            btn_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=8, border_width=0)
            btn_frame.pack(fill="x", padx=10, pady=3)

            btn = ctk.CTkButton(
                btn_frame,
                text=f"  {item['icon']}   {item['name']}",
                command=lambda i=item["name"], f=btn_frame: self.on_click(i, f),
                font=("Segoe UI", 15, "bold"),
                text_color="#b8b8d1",
                fg_color="transparent",
                hover_color="#2d2d44",
                anchor="w",
                height=48,
                corner_radius=8
            )
            btn.pack(fill="x", padx=5, pady=0)
            self.buttons.append(btn)
            self.button_frames.append(btn_frame)

        # ========== SPACER ==========
        self.spacer = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.spacer.pack(fill="both", expand=True)

        # ========== FOOTER ==========
        self.footer_frame = ctk.CTkFrame(self, fg_color="#16162a", corner_radius=0, border_width=0)
        self.footer_frame.pack(fill="x", side="bottom")

        footer_inner = ctk.CTkFrame(self.footer_frame, fg_color="transparent", border_width=0)
        footer_inner.pack(padx=15, pady=12)

        ctk.CTkLabel(
            footer_inner,
            text="v1.0.2",
            font=("Segoe UI", 12, "bold"),
            text_color="#5d5d7a"
        ).pack(anchor="w")

    def on_click(self, item_name, btn_frame):
        # Reset all buttons
        for i, frame in enumerate(self.button_frames):
            frame.configure(fg_color="transparent")
            self.buttons[i].configure(
                fg_color="transparent",
                text_color="#b8b8d1"
            )

        # Highlight active
        btn_frame.configure(fg_color="#3EA5FF")
        idx = self.button_frames.index(btn_frame)
        self.buttons[idx].configure(
            fg_color="#3EA5FF",
            text_color="#FFFFFF"
        )

        # Execute command
        if self.command:
            self.command(item_name)

    def toggle(self):
        self.expanded = not self.expanded
        if self.expanded:
            # Show sidebar - expanded
            new_width = self.expanded_width
            self.toggle_btn.configure(text="◀ Ocultar")
            self.header_frame.pack(fill="x", padx=15, pady=(10, 10))
            self.header_label.pack(anchor="w")
            self.subtitle_label.pack(anchor="w")
            self.separator.pack(fill="x", padx=15, pady=(10, 15))
            self.menu_label.pack(anchor="w", padx=20, pady=(0, 10))
            for i, btn in enumerate(self.buttons):
                item = self.menu_items[i]
                btn.configure(text=f"  {item['icon']}   {item['name']}")
                self.button_frames[i].pack(fill="x", padx=10, pady=3)
                btn.pack(fill="x", padx=5, pady=0)
        else:
            # Collapse sidebar
            new_width = self.collapsed_width
            self.toggle_btn.configure(text="▶")
            self.header_frame.pack_forget()
            self.header_label.pack_forget()
            self.subtitle_label.pack_forget()
            self.separator.pack_forget()
            self.menu_label.pack_forget()
            for i, btn in enumerate(self.buttons):
                item = self.menu_items[i]
                btn.configure(text=f" {item['icon']}")
                # Reduce padding when collapsed to avoid grey lines
                self.button_frames[i].pack(fill="x", padx=2, pady=1)
                btn.pack(fill="x", padx=2, pady=0)

        # Force width update
        self.configure(width=new_width)
        self._current_width = new_width
        self.update_idletasks()
