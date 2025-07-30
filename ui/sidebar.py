import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, command=None):
        super().__init__(master, width=200, corner_radius=0)
        self.grid_propagate(False)

        self.menu_items = ["Dashboard", "Reporte Semanal", "Gastos", "Jornales" ,"Venta de Cacao", "Enviado" ,"Configuración"]
        self.command = command

        self.expanded = True

        self.toggle_btn = ctk.CTkButton(self, text="≡", width=20, command=self.toggle)
        self.toggle_btn.pack(pady=10)

        self.buttons = []
        for item in self.menu_items:
            btn = ctk.CTkButton(self, text=item, command=lambda i=item: self.command(i))
            btn.pack(pady=5, fill="x", padx=10)
            self.buttons.append(btn)

    def toggle(self):
        self.expanded = not self.expanded
        for btn in self.buttons:
            btn.pack_forget() if not self.expanded else btn.pack(pady=5, fill="x", padx=10)
