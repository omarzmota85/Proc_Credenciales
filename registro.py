import tkinter as tk
from tkinter import messagebox
import pymysql
import cv2
import os

# CONFIGURACIÓN BD 
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "credenciales",
    "port": 3306
}

# CONTRASEÑA DE ADMINISTRADOR 
CONTRASENA_ACCESO = "admin123"

class RegistroAlumnoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Acceso Requerido")
        self.root.geometry("350x180")
        self.root.resizable(False, False)
        self.root.config(bg="#8B3D0A")
        
        self.centrar_ventana(self.root, 350, 180)
        
        # INTERFAZ DE LOGIN
        lbl_instruccion = tk.Label(self.root, text="Ingrese Contraseña de Administrador:", 
                                   fg="white", bg="#8B3D0A", font=("Arial", 11, "bold"))
        lbl_instruccion.pack(pady=20)
        
        self.txt_pass = tk.Entry(self.root, show="*", font=("Arial", 12), justify="center", width=20)
        self.txt_pass.pack(pady=5)
        self.txt_pass.focus()
        
        btn_entrar = tk.Button(self.root, text="Entrar", command=self.verificar_contrasena,
                               bg="#27AE60", fg="white", font=("Arial", 10, "bold"), width=12)
        btn_entrar.pack(pady=15)
        
        self.root.bind('<Return>', lambda event: self.verificar_contrasena())

    def centrar_ventana(self, ventana, ancho, alto):
        pantalla_ancho = ventana.winfo_screenwidth()
        pantalla_alto = ventana.winfo_screenheight()
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    def verificar_contrasena(self):
        entrada = self.txt_pass.get()
        if entrada == CONTRASENA_ACCESO:
            self.root.destroy()
            self.abrir_formulario()
        else:
            messagebox.showerror("Error", "Contraseña incorrecta. Acceso denegado.")
            self.txt_pass.delete(0, tk.END)

    def abrir_formulario(self):
        self.ventana_form = tk.Tk()
        self.ventana_form.title("Formulario de Registro de Alumnos")
        self.ventana_form.geometry("450x340") 
        self.ventana_form.resizable(False, False)
        self.ventana_form.config(bg="#f4f6f7")
        self.centrar_ventana(self.ventana_form, 450, 340)
        
        # Encabezado
        lbl_titulo = tk.Label(self.ventana_form, text="REGISTRO DE NUEVO ALUMNO", 
                              bg="#8B3D0A", fg="white", font=("Arial", 14, "bold"), pady=10)
        lbl_titulo.pack(fill=tk.X)
        
        # Contenedor para los campos
        frame_campos = tk.Frame(self.ventana_form, bg="#f4f6f7", padx=30, pady=20)
        frame_campos.pack(fill=tk.BOTH, expand=True)
        
        #  CAMPO: NOMBRE 
        lbl_nombre = tk.Label(frame_campos, text="Nombre Completo:", bg="#f4f6f7", font=("Arial", 11, "bold"))
        lbl_nombre.grid(row=0, column=0, sticky="w", pady=10)
        self.entry_nombre = tk.Entry(frame_campos, font=("Arial", 11), width=25)
        self.entry_nombre.grid(row=0, column=1, pady=10, padx=10)
        
        #  CAMPO: NÚMERO DE CONTROL
        lbl_control = tk.Label(frame_campos, text="Número de Control:", bg="#f4f6f7", font=("Arial", 11, "bold"))
        lbl_control.grid(row=1, column=0, sticky="w", pady=10)
        self.entry_control = tk.Entry(frame_campos, font=("Arial", 11), width=25)
        self.entry_control.grid(row=1, column=1, pady=10, padx=10)
        
        #  PANEL DE BOTONES INFERIORES
        frame_botones = tk.Frame(self.ventana_form, bg="#e5e8e8", pady=15)
        frame_botones.pack(fill=tk.X, side=tk.BOTTOM)
        
        # BOTON DE CAPTURAR/REGISTRAR 
        btn_registrar = tk.Button(frame_botones, text="📷 Capturar y Registrar", command=self.proceso_registro_completo,
                                  bg="#27AE60", fg="white", font=("Arial", 11, "bold"), width=18)
        btn_registrar.pack(side=tk.LEFT, padx=30)
        
        # Botón Salir
        btn_salir = tk.Button(frame_botones, text="Salir / Cancelar", command=self.ventana_form.destroy,
                              bg="#C0392B", fg="white", font=("Arial", 11, "bold"), width=15)
        btn_salir.pack(side=tk.RIGHT, padx=30)
        
        self.ventana_form.mainloop()

    def proceso_registro_completo(self):
        nombre = self.entry_nombre.get().strip()
        control = self.entry_control.get().strip()
        
        # Validaciones previas de texto
        if not nombre or not control:
            messagebox.showwarning("Advertencia", "Todos los campos (Nombre y Número de Control) son obligatorios.")
            return
            
        if not control.isdigit() or len(control) != 8:
            messagebox.showwarning("Formato Incorrecto", "El número de control debe ser de exactamente 8 dígitos numéricos.")
            return

        # Verificar primero si el número de control ya existe en la Base de Datos para no tomar la foto antes 
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT control FROM registros WHERE control = %s", (control,))
            existe = cursor.fetchone()
            
            if existe:
                messagebox.showerror("Error de Duplicado", f"El número de control '{control}' ya pertenece a un alumno registrado.")
                cursor.close()
                conn.close()
                return
                
        except pymysql.Error as e:
            messagebox.showerror("Error de Conexión", f"No se pudo verificar la base de datos:\n{e}")
            return

        # Si el ID está disponible, es enciende la cámara web
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error de Hardware", "No se pudo acceder a la cámara web.")
            cursor.close()
            conn.close()
            return

        messagebox.showinfo("Paso Biométrico", "Se abrirá la cámara.\nAlinee el rostro y presione ESPACIO o ENTER para registrar todo.")

        foto_tomada = False
        frame_capturado = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_visual = frame.copy()
            h, w = frame_visual.shape[:2]
            
            # Guía visual para centrar el rostro
            cv2.ellipse(frame_visual, (w // 2, h // 2), (120, 160), 0, 0, 360, (255, 255, 255), 2)
            
            cv2.rectangle(frame_visual, (0, h - 50), (w, h), (0, 0, 0), -1)
            cv2.putText(frame_visual, f"REGISTRANDO: {control} | [ESPACIO/ENTER] Capturar", (15, h - 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            
            cv2.imshow("Captura Biometrica de Rostro", frame_visual)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 32 or key == 13: # Espacio o Enter
                frame_capturado = frame.copy() # Guardamos la foto 
                foto_tomada = True
                break
            elif key == 27 or cv2.getWindowProperty("Captura Biometrica de Rostro", cv2.WND_PROP_VISIBLE) < 1:
                # Canceló la toma de foto con ESC o cerrando la ventana
                break

        cap.release()
        cv2.destroyAllWindows()

        # Si se tomó la foto con éxito, ejecutamos el doble guardado (Carpeta + Base de Datos)
        if foto_tomada and frame_capturado is not None:
            try:
                # GUARDAR EN BASE DE DATOS
                query = "INSERT INTO registros (control, nombre) VALUES (%s, %s)"
                cursor.execute(query, (control, nombre))
                conn.commit() # Guardado  en MySQL
                
                # GUARDAR EN CARPETA FISICA (Solo si la BD aceptó el registro)
                if not os.path.exists("rostros"):
                    os.makedirs("rostros")
                
                ruta_guardado = f"rostros/{control}.jpg"
                cv2.imwrite(ruta_guardado, frame_capturado)
                
                # SE GUARDO TODO
                messagebox.showinfo("Éxito", f"¡Registro Completo!\n\n• Datos guardados en MySQL.\n• Imagen guardada en: rostros/{control}.jpg")
                
                # Regresa en blanco de forma automática
                self.entry_nombre.delete(0, tk.END)
                self.entry_control.delete(0, tk.END)
                self.entry_nombre.focus()
                
            except pymysql.Error as e:
                messagebox.showerror("Error al Registrar", f"No se pudieron guardar los datos en la BD:\n{e}")
            finally:
                cursor.close()
                conn.close()
        else:
            # Si cerró la cámara sin presionar espacio/enter, se cancela todo el proceso
            messagebox.showwarning("Proceso Cancelado", "No se capturó la fotografía. El alumno no fue registrado.")
            cursor.close()
            conn.close()

if __name__ == "__main__":
    root_login = tk.Tk()
    app = RegistroAlumnoApp(root_login)
    root_login.mainloop()