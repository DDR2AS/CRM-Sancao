import customtkinter as ctk

class InicioFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        label = ctk.CTkLabel(self, text="Bienvenido a la vista de Inicio", font=("Arial", 20))
        label.pack(pady=20)