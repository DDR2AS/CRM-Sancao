import customtkinter as ctk

class ConfiguracionFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        label = ctk.CTkLabel(self, text="Configuraciones", font=("Arial", 20))
        label.pack(pady=20)
