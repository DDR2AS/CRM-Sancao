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
from ui.ViewSalesFrame import SalesFrame
from ui.ViewProduccionFrame import ProduccionFrame

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

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)

        self.overrideredirect(True)

        # DPI awareness para Windows con escalado
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        sw, sh = 380, 200
        x = (1920 - sw) // 2
        y = (1080 - sh) // 2
        self.geometry(f"{sw}x{sh}+{x}+{y}")
        self.configure(fg_color="#1a1a2e")
        self.attributes("-topmost", True)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.4, anchor="center")

        ctk.CTkLabel(
            inner, text="CRM SANCAO",
            font=("Segoe UI", 28, "bold"), text_color="#FFFFFF"
        ).pack()

        self.spinner_label = ctk.CTkLabel(
            inner, text="",
            font=("Segoe UI", 24), text_color="#3EA5FF"
        )
        self.spinner_label.pack(pady=(15, 0))

        ctk.CTkLabel(
            inner, text="Conectando...",
            font=("Segoe UI", 12), text_color="#7a7a9a"
        ).pack(pady=(8, 0))

        self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._idx = 0
        self._animate()

    def _animate(self):
        if self.winfo_exists():
            self.spinner_label.configure(text=self._frames[self._idx])
            self._idx = (self._idx + 1) % len(self._frames)
            self.after(100, self._animate)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CRM SANCAO")
        window_width = 1225
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.resizable(True, True)
        self.process = None
        self.withdraw()

        # Splash
        self.splash = SplashScreen(self)
        self.after(3000, self._dismiss_splash)

    def _dismiss_splash(self):
        if self.splash and self.splash.winfo_exists():
            self.splash.destroy()
        self.splash = None
        self._build_ui()
        self.deiconify()

    def _build_ui(self):
        # Sidebar
        self.sidebar = Sidebar(self, command=self.on_menu_click)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        # Contenedor principal
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.grid_columnconfigure(0, weight=0, minsize=70)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_view = None
        self.notification = None
        self.show_view("Dashboard")

        if getattr(self, "_pending_notification", False):
            self._pending_notification = False
            self.show_notification("✅ Conexión exitosa", "Base de datos conectada correctamente")

    def on_menu_click(self, item):
        # Evitar acceso a vistas que requieren DB sin conexión aún
        views_require_db = ["Gastos", "Reporte", "Jornales", "Enviado", "Ventas", "Producción"]
        if item in views_require_db and self.process is None:
            print("Aún no se ha conectado a la base de datos. Espera un momento...")
            messagebox.showinfo("Database Connection", "Conectando a la BD. Espere un momento...")
            return

        self.show_view(item)

    def show_view(self, view_name):
        if self.current_view:
            self.current_view.destroy()

        if view_name == "Dashboard":
            self.current_view = InicioFrame(self.main_container, process=self.process)
        elif view_name == 'Reporte':
            self.current_view = ResumenFrame(self.main_container,process=self.process)
        elif view_name == "Gastos":
            self.current_view = GastosFrame(self.main_container, process=self.process)
        elif view_name == "Jornales":
            self.current_view = JornalesFrame(self.main_container, process=self.process)
        elif view_name == "Configuración":
            self.current_view = ConfiguracionFrame(self.main_container)
        elif view_name == "Enviado":
            self.current_view = EnviosFrame(self.main_container, process=self.process)
        elif view_name == "Ventas":
            self.current_view = SalesFrame(self.main_container, process=self.process)
        elif view_name == "Producción":
            self.current_view = ProduccionFrame(self.main_container, process=self.process)
        else:
            self.current_view = ctk.CTkLabel(self.main_container, text=f"Vista: {view_name}")

        self.current_view.pack(fill="both", expand=True)

    def set_process(self, process):
        self.process = process
        print("Base de datos asignada a la app")
        if hasattr(self, "notification"):
            self.show_notification("✅ Conexión exitosa", "Base de datos conectada correctamente")
        else:
            self._pending_notification = True

    def show_notification(self, title, message, duration=4000):
        """Show a toast notification at the bottom right"""
        # Remove existing notification if any
        if self.notification:
            self.notification.destroy()

        # Create notification frame
        self.notification = ctk.CTkFrame(
            self,
            fg_color="#28a745",
            corner_radius=10
        )

        inner = ctk.CTkFrame(self.notification, fg_color="transparent")
        inner.pack(padx=15, pady=12)

        ctk.CTkLabel(
            inner,
            text=title,
            font=("Segoe UI", 13, "bold"),
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text=message,
            font=("Segoe UI", 11),
            text_color="#E8F5E9"
        ).pack(anchor="w")

        # Position at bottom right
        self.notification.place(relx=0.98, rely=0.95, anchor="se")

        # Auto-hide after duration
        self.after(duration, self.hide_notification)

    def hide_notification(self):
        """Hide the notification"""
        if self.notification:
            self.notification.destroy()
            self.notification = None

if __name__ == "__main__":
    app = App()
    app.after(100, lambda: load_db_thread(app.set_process))
    app.mainloop()
