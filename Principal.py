#########################################################################################################
import os
import time
import pyvisa
import datetime
import Funciones
import numpy as np
import scipy.stats as stats
from scipy.stats import linregress
from pathlib import Path
from Instrumental.HP3458A import HP3458A
from Instrumental.HP3245A import HP3245A
#########################################################################################################
#estado_actual = "CALCULO"
estado_actual = "CONFIGURACION"
#estado_actual = "INICIALIZACION"
#estado_actual  = "MEDICION_MUL"

Cant_Muestras = 10000
Aper_Time     = 3e-6
#########################################################################################################
# Base de ejecución
base_path = Path(__file__).parent

# Timestamp para nombre del archivo
fecha_actual = datetime.datetime.now()
#nombre_archivo = fecha_actual.strftime("Medicion_%Y-%m-%d_%H-%M-%S.txt")
nombre_archivo = "Medicion_2025-09-03_10-56-50.txt"
# Carpetas
carpeta_mediciones = base_path / "Mediciones" 
carpeta_calculos   = base_path / "Resultados" 
Carpeta_Mediciones_Generador  = carpeta_mediciones / "Generador_1"
Carpeta_Mediciones_Carga      = carpeta_mediciones / "Capacitor_1" 


# Crear carpetas necesarias
carpeta_mediciones.mkdir(parents=True, exist_ok=True)
carpeta_calculos.mkdir(parents=True, exist_ok=True)
Carpeta_Mediciones_Generador.mkdir(parents=True, exist_ok=True)
Carpeta_Mediciones_Carga.mkdir(parents=True, exist_ok=True)


# Ruta final del archivo .txt
ruta_medicion_generador = Carpeta_Mediciones_Generador / nombre_archivo
ruta_medicion_CargayDescarga = Carpeta_Mediciones_Carga / nombre_archivo
ruta_resultados = carpeta_calculos / nombre_archivo


#########################################################################################################
Funciones.limpiar_pantalla()
opcion = Funciones.Mostrar_Menu()

while True:
          
    if estado_actual == "CONFIGURACION":
        
        Funciones.limpiar_pantalla()
        
        Modo = Funciones.Menu_Instrumental()
        
        Funciones.limpiar_pantalla()
        
        #Configura parámetros de medición en función de los vallores ingresados
        Vn_Cx, Vn_Rp, Ciclos, Tau_x_ciclo=Funciones.Menu_Config()         
        
        Funciones.limpiar_pantalla()
                        
        Vn_Tau,Frec,Sweep_time = Funciones.Calculo_Ciclos(Vn_Cx,Vn_Rp,Ciclos,Tau_x_ciclo, Cant_Muestras)              
        
        Funciones.limpiar_pantalla()
        
        estado_actual =  Funciones.Mostrar_Configuracion(Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec)    
      
  
    elif estado_actual == "INICIALIZACION":   
        with HP3245A("GPIB0::9::INSTR") as gen:
            gen.configurar_generador_full(
            Frec= Frec,
            Sweep_Time     = Sweep_time*1e6,    
        )
        #estado_actual = "MEDICION_GEN"
        estado_actual  = "MEDICION_MUL"
        
    elif estado_actual == "MEDICION_GEN":       
        with HP3458A("GPIB0::22::INSTR") as dvm:
            Medicion_Generador=dvm.configurar_y_medir_sweep(Cant_Muestras, Sweep_time, Aper_Time)
        V_max, Gen_std = Funciones.analizar_senal_cuadrada(Medicion_Generador)
        Funciones.Guardar_Medicion(ruta_medicion_generador,Medicion_Generador)
        input("Cambiar posición de llave para medir la tensión en el capacitor y presionar Enter")      
        estado_actual = "MEDICION_MUL"
           
    elif estado_actual == "MEDICION_MUL":
        with HP3458A("GPIB0::22::INSTR") as dvm:
            Medicion_Capacitor=dvm.configurar_y_medir_sweep(Cant_Muestras, Sweep_time, Aper_Time)
        Funciones.Guardar_Medicion(ruta_medicion_CargayDescarga,Medicion_Capacitor)
        V_max =1.0
        Funciones.Procesamiento_CargayDescarga(ruta_medicion_CargayDescarga,Medicion_Capacitor,V_max,Sweep_time,Vn_Rp)
        estado_actual = "CALCULO"
    
    elif estado_actual == "CALCULO":
        input("Presionar Enter para continuar") 
        Funciones.limpiar_pantalla()
    
    elif estado_actual == "FINALIZACION":
        input("Presionar Enter para continuar") 
        Funciones.limpiar_pantalla()
        break
    
    else:
        Funciones.limpiar_pantalla()
        break