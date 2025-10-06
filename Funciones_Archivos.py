################################################## LIBRERIAS #########################################################
import os
import sys 
import json
import datetime
from time import sleep
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
from scipy.stats import linregress
from pathlib import Path
import Funciones_Medicion

#####################################################################################################################

def Mostrar_Menu():
    print("--- Menú Principal ---")
    opcion = input("Presione Enter para empezar")
    return opcion

#####################################################################################################################   

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')


def limpiar_teclado():
    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except:
        pass  # en Windows no existe termios
#####################################################################################################################

def Menu_Inicial():
    
    print("--- Modo de aplicación ---\n") 
    print("1. Medir y calibrar")
    print("2. Calcular desde una medición ya existente")
    while True:
            
            opcion = input("Introducir modo (1 o 2):")
            if opcion != "1" and opcion != "2":
                limpiar_pantalla()
                print("--- Modo de aplicación ---\n") 
                print("1. Medir y calibrar")
                print("2. Calcular desde una medición ya existente")
                    
            else:
                break
        
    return opcion   
#####################################################################################################################

def Ruta_de_analisis_existente():
    # --- pedir y validar ruta del generador ---
    limpiar_pantalla()
    while True:
        ruta_generador_str = input("Introducir la ruta de archivo de medición de generador:\n")
        ruta_generador = Path(ruta_generador_str)
        if ruta_generador.exists():
            ruta_generador = ruta_generador.resolve()  # normalizar ruta absoluta
            break
        else:
            print("⚠️ La ruta no existe o está mal escrita. Intente de nuevo.\n")

    # --- pedir y validar ruta de la curva de carga ---
    while True:
        ruta_curva_carga_str = input("Introducir la ruta de archivo de medición de curva de carga:\n")
        ruta_curva_carga = Path(ruta_curva_carga_str)
        if ruta_curva_carga.exists():
            ruta_curva_carga = ruta_curva_carga.resolve()
            break
        else:
            print("⚠️ La ruta no existe o está mal escrita. Intente de nuevo.\n")

    while True:
        ruta_curva_config_str = input("Introducir la ruta del archivo de configuración:\n")
        ruta_curva_config = Path(ruta_curva_config_str)
        if ruta_curva_config.exists():
            ruta_curva_config= ruta_curva_config.resolve()
            break
        else:
            print("⚠️ La ruta no existe o está mal escrita. Intente de nuevo.\n")

    # --- obtener nombres de archivo ---
    nombre_archivo_generador = ruta_generador.name  # solo el nombre con extensión
    nombre_archivo_curva = ruta_curva_carga.name
    nombre_archivo_config = ruta_curva_config.name

    return (str(ruta_generador), str(ruta_curva_carga),str(ruta_curva_config),
            nombre_archivo_generador, nombre_archivo_curva, nombre_archivo_config)

#####################################################################################################################
def extraccion_datos(ruta_json):
    """
    Lee un archivo JSON y devuelve los valores:
    Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time
    """
    ruta = Path(ruta_json)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_json}")
    
    with open(ruta, "r") as file:
        datos = json.load(file)
    
    try:
        Modo   = datos["Modo"]
        Vn_Cx  = datos["Vn_Cx"]
        Vn_Rp  = datos["Vn_Rp"]
        Vn_Tau = datos["Vn_Tau"]
        Frec   = datos["Frec"]
        Sweep_time = datos["Sweep_time"]
    except KeyError as e:
        raise KeyError(f"Falta el campo {e} en el archivo JSON: {ruta_json}")
    
    return Modo,Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time

#####################################################################################################################

def Ruta_de_analisis_nuevo():
    # Base de ejecución
    base_path = Path(__file__).parent

    # Timestamp para nombre del archivo
    fecha_actual = datetime.datetime.now()
    nombre_archivo = fecha_actual.strftime("Medicion_%Y-%m-%d_%H-%M-%S.txt")
    nombre_archivo_config = fecha_actual.strftime("Medicion_%Y-%m-%d_%H-%M-%S.json")

    # Carpetas
    carpeta_mediciones = base_path / "Mediciones" 

    Carpeta_Mediciones_Generador  = carpeta_mediciones / "Generador_1"
    Carpeta_Mediciones_Carga      = carpeta_mediciones / "Capacitor_1" 
    Carpeta_Mediciones_Config     = carpeta_mediciones / "Config" 

    # Crear carpetas necesarias
    carpeta_mediciones.mkdir(parents=True, exist_ok=True)

    Carpeta_Mediciones_Generador.mkdir(parents=True, exist_ok=True)
    Carpeta_Mediciones_Carga.mkdir(parents=True, exist_ok=True)
    Carpeta_Mediciones_Config.mkdir(parents=True, exist_ok=True)


    # Ruta final del archivo de Medición
    ruta_medicion_generador = Carpeta_Mediciones_Generador / nombre_archivo
    ruta_medicion_CargayDescarga = Carpeta_Mediciones_Carga / nombre_archivo_config

    # Ruta final del archivo de Configuración
    ruta_medicion_Config = Carpeta_Mediciones_Config / nombre_archivo
 
    return str(ruta_medicion_generador), str(ruta_medicion_CargayDescarga), str(ruta_medicion_Config)

#####################################################################################################################
def Menu_Instrumental():
    
    print("Seleccionar Set de medición \n")
    print("1. INTI")
    print("2. FRH")
    
    while True:
        #limpiar_teclado()
        opcion_generador = input("Introducir Set (1 o 2):")
        
        
        if opcion_generador == "1":
            opcion = "Set INTI"
            break
        elif opcion_generador == "2":
            opcion = "Set FRH"
            break  
        
        else:
            #limpiar_pantalla()
            print("Seleccionar Set de medición")
            print("1. INTI")
            print("2. FRH")
        
    return opcion   
#####################################################################################################################

def Menu_Config():   
    
    print("\n---_ Menú de Configuración ----\n")  
      
    while True:
        Vn_capacitor   = input("Valor nominal del capacitor de transferencia (Cx) en microfarad: ")
        if Vn_capacitor.isdigit():
            Vn_capacitor_int = int(Vn_capacitor) 
            break
        else:
            print("Eso no es un número válido.")   
     
    while True:
        Vn_resistencia = input("Valor nominal del resistor patrón (Rp) en ohm: ")
        if Vn_resistencia .isdigit():
            Vn_resistencia_int = int(Vn_resistencia) 
            break
        else:
            print("Eso no es un número válido.")   
    Ciclos = 5
    tau_x_ciclo = 5

    return Vn_capacitor_int, Vn_resistencia_int,Ciclos, tau_x_ciclo

#####################################################################################################################
#####################################################################################################################

def Mostrar_Configuracion(Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec):
    print("\n--- Resumen de configuración ---\n") 
    print(f"Se utilizará el set de medición: {Modo}")
    print(f"Capacitor incognita de valor nominal : {Vn_Cx} uF")
    print(f"Resistor patrón de: {Vn_Rp} ohm")
    print(f"El tau esperado es de: {Vn_Tau} segundos")
    print("\n--- ------------------------- ---\n") 
    print(f"Se aplicará una señal cuadrada de valor tensión pico 1 V, montada sobre una contínua de 0.5 V y frecuencia de: {Frec} Hz \n")
  
    while True:
        entrada = input("Para continuar presione 1. Para volver a iniciar presione r")
        
        if   entrada  == "1":
                opcion = "INICIALIZACION"
                break                  
        elif entrada  == "r":
                opcion  = "CONFIGURACION"
                break
        else:
            limpiar_pantalla()
            print("Ingreso incorrecto")
    
    return opcion
###################################################################################################################

def Configuracion():
        
    limpiar_pantalla()
        
    Modo = Menu_Instrumental()
        
    limpiar_pantalla()
        
    #Configura parámetros de medición en función de los vallores ingresados
    Vn_Cx, Vn_Rp, Ciclos, Tau_x_ciclo = Menu_Config()         
        
    limpiar_pantalla()
                        
    Vn_Tau, Frec, Sweep_time = Funciones_Medicion.Calculo_Ciclos(Vn_Cx,Vn_Rp,Ciclos,Tau_x_ciclo, Funciones_Medicion.Cant_Muestras)              
        
    limpiar_pantalla()
        
    return Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time    

###################################################################################################################

def Guardar_Medicion(Ruta_Guardado,Medicion_Realizada):
    with open(Ruta_Guardado, "w") as file:         
            for dato in Medicion_Realizada:
                file.write(f"{dato}\n")  
###################################################################################################################
def Guardar_Medicion_Config(Ruta_Guardado, Medicion_Realizada, 
                     Modo=None,Vn_Cx=None, Vn_Rp=None, Vn_Tau=None, Frec=None, Sweep_time=None):
    # Guardar los datos de la medición en un archivo de texto
    with open(Ruta_Guardado, "w") as file:         
        for dato in Medicion_Realizada:
            file.write(f"{dato}\n")  
    
    # Si se pasaron los parámetros, guardarlos en un archivo JSON
    if None not in (Modo,Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time):
        parametros = {
            "Modo": Modo, 
            "Vn_Cx": Vn_Cx,
            "Vn_Rp": Vn_Rp,
            "Vn_Tau": Vn_Tau,
            "Frec": Frec,
            "Sweep_time": Sweep_time
        }
        
        ruta_json = Path(Ruta_Guardado).with_suffix(".json")
        with open(ruta_json, "w") as json_file:
            json.dump(parametros, json_file, indent=4)
###################################################################################################################

def Menu_Final():
    
    limpiar_pantalla()
    print("La calibración ha finalizado.")
    while True: 
            select_final = input("\nPresionar 1 para volver al menú principal o 2 para cerrar: ")  
            limpiar_pantalla() 
            if select_final == "1":
                return "INICIO"
            elif select_final == "2":
                sys.exit()   
            else:
                limpiar_pantalla()
                print("Elección incorrecta.")

###################################################################################################################