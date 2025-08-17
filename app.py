from services.mongodb import DBMongo
from services.drive_manager import GoogleService
from services.process import Pipelines
import customtkinter as ctk
from ui.sidebar import Sidebar
from tkinter import messagebox

from ui.inicio import InicioFrame
from ui.configuracion import ConfiguracionFrame
from ui.main_table import MainTable
from ui.ViewGastosFrame import GastosFrame
from ui.ViewResumenFrame import ResumenFrame
from ui.ViewEnviosFrame import EnviosFrame
from ui.ViewJornalesFrame import JornalesFrame

import threading

# Conexión MongoDB en hilo separado
def init_db_connection():
    db_service = DBMongo()
    db_service.connect()
    g_service = GoogleService()
    return db_service, g_service

def load_db_thread(callback):
    def run():
        print("⏳ Conectando a MongoDB...")
        db_mongo, g_service = init_db_connection()
        print("✅ Conexión a MongoDB y drive listo.")
        process = Pipelines(db_mongo,g_service)
        print("✅ Pipelines inicializados.")
        callback(process)
    threading.Thread(target=run, daemon=True).start()

# Configuración de apariencia de la app
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CRM SANCAO")
        window_width = 1225
        window_height = 600
        # Calculando el centro
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # Calcular posición
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.resizable(True, True)
        self.process = None  # Se asignará luego

        # Sidebar
        self.sidebar = Sidebar(self, command=self.on_menu_click)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        # Contenedor principal
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_view = None
        self.show_view("Inicio")

    def on_menu_click(self, item):
        # Evitar acceso a vistas que requieren DB sin conexión aún
        if (item == "Gastos"  or item == "Reporte Semanal" or item == "Jornales" or item == 'Enviado') and self.process is None:
            print("Aún no se ha conectado a la base de datos. Espera un momento...")
            messagebox.showinfo("Database Connection", "Conectando a la BD. Espere un momento...")
            return

        self.show_view(item)

    def show_view(self, view_name):
        if self.current_view:
            self.current_view.destroy()

        if view_name == "Inicio":
            self.current_view = InicioFrame(self.main_container)
        elif view_name == 'Reporte Semanal':
            self.current_view = ResumenFrame(self.main_container,process=self.process)
        elif view_name == "Gastos":
            self.current_view = GastosFrame(self.main_container, process=self.process)
        elif view_name == "Jornales":
            self.current_view = JornalesFrame(self.main_container, process=self.process)
        elif view_name == "Configuración":
            self.current_view = ConfiguracionFrame(self.main_container)
        elif view_name == "Enviado":
            self.current_view = EnviosFrame(self.main_container, process=self.process)
        else:
            self.current_view = ctk.CTkLabel(self.main_container, text=f"Vista: {view_name}")

        self.current_view.pack(fill="both", expand=True)

    def set_process(self, process):
        self.process = process
        print("Base de datos asignada a la app")

if __name__ == "__main__":
    app = App()
    app.after(100, lambda: load_db_thread(app.set_process))
    app.mainloop()
