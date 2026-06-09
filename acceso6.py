import cv2
import pytesseract
import numpy as np
import re
import time
import pymysql
from datetime import datetime
from deepface import DeepFace
import os

# CONFIGURACIÓN GENERAL
PROCESS_EVERY_N_FRAMES = 5  
DEBOUNCE_SECONDS = 5.0      

#  CONFIGURACIÓN FILTRO ESTABILIDAD 
LECTURAS_REQUERIDAS = 2     
historial_controles = []    

#  CONFIGURACIÓN BD 
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "credenciales",
    "port": 3306
}

#  MEDIDAS DE LA CREDENCIAL 
DPI = 96
CARD_WIDTH_CM = 9.5   
CARD_HEIGHT_CM = 6.0

CARD_WIDTH_PX = int((CARD_WIDTH_CM / 2.54) * DPI)
CARD_HEIGHT_PX = int((CARD_HEIGHT_CM / 2.54) * DPI)

#  FUNCIONES BD 
def buscar_persona(control):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM registros WHERE control = %s", (control,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(" Error de BD en buscar_persona:", e)
        return None

def buscar_acceso_abierto(control):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM accesos
            WHERE control = %s AND hora_salida IS NULL
            ORDER BY hora_entrada DESC
            LIMIT 1
        """, (control,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print("Error de BD en buscar_acceso_abierto:", e)
        return None

def registrar_entrada(control):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accesos (control, hora_entrada)
            VALUES (%s, %s)
        """, (control, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(" Error al registrar entrada:", e)

def registrar_salida(acceso_id):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE accesos
            SET hora_salida = %s
            WHERE id = %s
        """, (datetime.now(), acceso_id))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error al registrar salida:", e)

# FUNCIÓN VERIFICACIÓN FACIAL 
def verificar_rostro(control, cap):
    extensiones_posibles = [".jpg", ".png", ".jpeg", ".JPG", ".PNG"]
    ruta_bd = None
    
    for ext in extensiones_posibles:
        ruta_prueba = f"rostros/{control}{ext}"
        if os.path.exists(ruta_prueba):
            ruta_bd = ruta_prueba
            break
            
    if not ruta_bd:
        print(f"Archivo de imagen NO encontrado para el ID {control}")
        return False

    # PAUSA  (2 SEGUNDOS) PARA ACOMODAR EL ROSTRO 
    tiempo_pausa = time.time()
    while time.time() - tiempo_pausa < 2.0:
        ret, frame = cap.read()
        if not ret: continue
        
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 110), (0, 165, 255), -1)
        cv2.putText(frame, f"ID DETECTADO: {control}", (30, 45), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, "PREPARANDO BIOMETRICO... MIRE A LA CAMARA", (30, 85), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        
        cv2.circle(frame, (w // 2, h // 2), 160, (0, 165, 255), 3)
        cv2.imshow("Control de Acceso", frame)
        cv2.waitKey(1)

    #  CAPTURA DE UN ÚNICO SNAPSHOT LIMPIO 
    ret, frame_captura = cap.read()
    if not ret:
        return False

    # Forzar actualización de pantalla indicando el procesamiento
    h, w = frame_captura.shape[:2]
    frame_espera = frame_captura.copy()
    cv2.rectangle(frame_espera, (0, 0), (w, 110), (0, 100, 255), -1) 
    cv2.putText(frame_espera, "PROCESANDO ROSTRO BIOMETRICO...", (30, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 3, cv2.LINE_AA)
    cv2.circle(frame_espera, (w // 2, h // 2), 160, (0, 100, 255), 3)
    cv2.imshow("Control de Acceso", frame_espera)
    cv2.waitKey(100) 

    # ANÁLISIS AUTOMÁTICO 
    print(f" Analizando rostro de forma optimizada contra {ruta_bd}...")
    try:
        resultado = DeepFace.verify(
            img1_path=frame_captura,
            img2_path=ruta_bd,
            enforce_detection=False,
            model_name="VGG-Face",
            detector_backend="opencv", 
            distance_metric="cosine"
        )
        
        print("Resultado de la verificación:", resultado)
        return resultado["verified"]

    except Exception as e:
        print("Error en análisis DeepFace:", e)
        return False

#  CLASE OCR HORIZONTAL 
class IDCardOCR:
    def __init__(self):
        print("Sistema OCR listo y restaurado.")

    def preprocess_card(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(3.0, (8, 8))
        enhanced = clahe.apply(gray)
        blur = cv2.GaussianBlur(enhanced, (3, 3), 0)

        if blur.shape[1] < 1200:
            scale = 1200 / blur.shape[1]
            blur = cv2.resize(blur, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        return blur

    def recognize_text(self, img):
        try:
            config = "--oem 3 --psm 6 -l spa"
            text = pytesseract.image_to_string(img, config=config)
        except:
            config = "--oem 3 --psm 6 -l eng"
            text = pytesseract.image_to_string(img, config=config)
        return text.upper()

    def extract_control(self, text):
        if not text:
            return None
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 4]
        for line in lines:
            m = re.search(r"\d{8}", line)
            if m:
                control = m.group()
                if control.isdigit():
                    return control
        return None

    def process_frame(self, frame):
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        # Límites del marco horizontal
        x1 = max(cx - CARD_WIDTH_PX // 2, 0)
        y1 = max(cy - CARD_HEIGHT_PX // 2, 0)
        x2 = min(cx + CARD_WIDTH_PX // 2, w)
        y2 = min(cy + CARD_HEIGHT_PX // 2, h)

        card = frame[y1:y2, x1:x2]
        if card.size == 0: return None
        
        #  Orientación normal de la credencias
        processed = self.preprocess_card(card)
        text = self.recognize_text(processed)
        control = self.extract_control(text)
        
        #  Inversión de 180 grados si entra de cabeza la credencial 
        if not control:
            card_rotated = cv2.rotate(card, cv2.ROTATE_180)
            processed_r = self.preprocess_card(card_rotated)
            text_r = self.recognize_text(processed_r)
            control = self.extract_control(text_r)
            
        return control

# MAIN LOOP 
def main():
    global historial_controles
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("ERROR: No se pudo acceder a la cámara web.")
        return

    ocr = IDCardOCR()
    
    mensaje_barra_1 = "ESPERANDO CREDENCIAL..."
    mensaje_barra_2 = "COLOQUE LA TARJETA EN EL RECUADRO"
    color_banner = (139, 61, 10)  
    
    last_time = 0
    frame_count = 0

    cv2.namedWindow("Control de Acceso", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Control de Acceso", 950, 650)

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame_count += 1
        now = time.time()

        # Solo procesamos OCR si no estamos bloqueados por el tiempo de espera 
        if frame_count % PROCESS_EVERY_N_FRAMES == 0 and (now - last_time > DEBOUNCE_SECONDS):
            
            # Resetear mensajes por defecto si ya pasó el tiempo de congelamiento exitoso/erroneo
            if mensaje_barra_1 != "ESPERANDO CREDENCIAL...":
                mensaje_barra_1 = "ESPERANDO CREDENCIAL..."
                mensaje_barra_2 = "COLOQUE LA TARJETA EN EL RECUADRO"
                color_banner = (139, 61, 10)

            try:
                control_detectado = ocr.process_frame(frame.copy())

                if control_detectado:
                    historial_controles.append(control_detectado)
                    if len(historial_controles) > LECTURAS_REQUERIDAS:
                        historial_controles.pop(0)
                    
                    if len(historial_controles) == LECTURAS_REQUERIDAS and len(set(historial_controles)) == 1:
                        control = historial_controles[0] 
                        nombre = buscar_persona(control)

                        if nombre:
                            # Llamada a la verificación biométrica 
                            rostro_verificado = verificar_rostro(control, cap)

                            if rostro_verificado:
                                acceso_abierto = buscar_acceso_abierto(control)
                                if acceso_abierto:
                                    registrar_salida(acceso_abierto)
                                    mensaje_barra_1 = f"HASTA LUEGO: {nombre}"
                                else:
                                    registrar_entrada(control)
                                    mensaje_barra_1 = f"BIENVENIDO: {nombre}"
                                    
                                mensaje_barra_2 = f"CONTROL: {control} VERIFICADO"
                                color_banner = (39, 174, 96) # Verde
                            else:
                                mensaje_barra_1 = "ACCESO DENEGADO"
                                mensaje_barra_2 = "EL ROSTRO NO COINCIDE CON LA CREDENCIAL"
                                color_banner = (0, 0, 255) # Rojo
                        else:
                            mensaje_barra_1 = "NO REGISTRADO"
                            mensaje_barra_2 = f"ID {control} NO EXISTE EN LA BASE DE DATOS"
                            color_banner = (0, 0, 255) # Rojo
                        
                        historial_controles.clear() 
                        last_time = time.time()
                else:
                    if historial_controles: historial_controles.pop(0)
            except Exception as e:
                print("  Excepción en bucle principal:", e)

        # DIBUJAR CAPA GRÁFICA
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        # Dibujar el marco guía en pantalla solo si estamos buscando credenciales
        if mensaje_barra_1 == "ESPERANDO CREDENCIAL...":
            x1 = cx - CARD_WIDTH_PX // 2
            y1 = cy - CARD_HEIGHT_PX // 2
            x2 = cx + CARD_WIDTH_PX // 2
            y2 = cy + CARD_HEIGHT_PX // 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.putText(frame, "ALINEE LA CREDENCIAL EN ESTA AREA", (x1 + 10, y1 - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

        # Pintar la barra de estado superior
        cv2.rectangle(frame, (0, 0), (w, 110), color_banner, -1)
        cv2.putText(frame, mensaje_barra_1, (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, mensaje_barra_2, (30, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow("Control de Acceso", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()