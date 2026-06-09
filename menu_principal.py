import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import customtkinter as ctk  

#  CONFIGURACIÓN DE TEMA 
ctk.set_appearance_mode("dark")   

# FUNCIONES 
def abrir_entrada():
    try:
        subprocess.Popen([sys.executable, "acceso6.py"])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el sistema:\n{e}")

def abrir_registro():
    try:
        subprocess.Popen([sys.executable, "registro.py"])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el módulo de registro:\n{e}")

#  VENTANA PRINCIPAL
ventana = ctk.CTk()  
ventana.title("Sistema de Acceso ITTUX")
ventana.geometry("850x600")
ventana.resizable(False, False)
ventana.configure(fg_color="#0A1128") 

# Centrar la ventana en pantalla
pantalla_ancho = ventana.winfo_screenwidth()
pantalla_alto = ventana.winfo_screenheight()
x = (pantalla_ancho // 2) - (850 // 2)
y = (pantalla_alto // 2) - (600 // 2)
ventana.geometry(f"850x600+{x}+{y}")

#  ENCABEZADO 
frame_textos = ctk.CTkFrame(ventana, fg_color="transparent")
frame_textos.pack(pady=(100, 40))

lbl_subtitulo = ctk.CTkLabel(
    frame_textos,
    text="SISTEMA DE",
    font=("Arial Black", 14),
    text_color="#8EA8D9"  
)
lbl_subtitulo.pack()

lbl_titulo = ctk.CTkLabel(
    frame_textos,
    text="CREDENCIALES",
    font=("Arial Black", 42, "bold"),
    text_color="#FFFFFF"
)
lbl_titulo.pack(pady=(0, 5))

lbl_slogan = ctk.CTkLabel(
    frame_textos,
    text="Gestión segura y eficiente",
    font=("Arial", 13, "italic"),
    text_color="#52658F"  
)
lbl_slogan.pack()

#  PANEL DE BOTONES 
frame_botones = ctk.CTkFrame(ventana, fg_color="transparent")
frame_botones.pack(pady=10)

#  ENTRADA ITTUX 
btn_entrada = ctk.CTkButton(
    frame_botones,
    text="🚪  ENTRADA ITTUX\n     Acceder al sistema",
    font=("Arial", 15, "bold"),
    text_color="#19E3B1",         
    fg_color="#102A43",            
    hover_color="#143656",         
    border_color="#19E3B1",        
    border_width=1,
    corner_radius=18,             
    width=400,
    height=85,
    anchor="w",                    
    command=abrir_entrada
)
btn_entrada.pack(pady=15)

#  REGISTRO ALUMNOS 
btn_registro = ctk.CTkButton(
    frame_botones,
    text="👥  REGISTRO ALUMNOS\n     Crear nueva cuenta",
    font=("Arial", 15, "bold"),
    text_color="#2F80ED",          
    fg_color="#102A43",            
    hover_color="#143656",
    border_color="#2F80ED",        
    border_width=1,
    corner_radius=18,              
    width=400,
    height=85,
    anchor="w",                   
    command=abrir_registro
)
btn_registro.pack(pady=15)

#  EJECUCIÓN 
ventana.mainloop()