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
estado_actual = "MODO_USO"
#estado_actual = "INICIALIZACION"
#estado_actual  = "MEDICION_MUL"

Cant_Muestras = 10000
Aper_Time     = 3e-6
#########################################################################################################

Funciones.limpiar_pantalla()
opcion = Funciones.Mostrar_Menu()

while True:

########################################################################################################################################################    

    if estado_actual == "MODO_USO":
    
        Funciones.limpiar_pantalla()
        modo_u = Funciones.Menu_Inicial()
        
        if modo_u == "1":
            ruta_medicion_generador, ruta_medicion_CargayDescarga = Funciones.Ruta_de_analisis_nuevo()
            Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time = Funciones.Configuracion()
            estado_actual = "INICIALIZACION"
        
        elif modo_u== "2":
            ruta_medicion_generador, ruta_medicion_CargayDescarga, Archivo_Generador, Archivo_Capacitor = Funciones.Ruta_de_analisis_existente()
            Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time = Funciones.extraccion_datos(Archivo_Generador, Archivo_Capacitor)
            estado_actual = "EXTRACCION"
        
        else:
            Funciones.limpiar_pantalla()
            print("Opción incorrecta. Ingresá 1 o 2.")
            opcion = Funciones.Menu_Inicial()
             
######################################################################################################################################################## 

    elif estado_actual == "INICIALIZACION":   
        
        with HP3245A("GPIB0::9::INSTR") as gen:
            gen.configurar_generador_full(
            Frec= Frec,
            Sweep_Time     = Sweep_time*1e6,    
        )
        #estado_actual = "MEDICION_GEN"
        estado_actual  = "MEDICION_MUL"

######################################################################################################################################################## 
         
    elif estado_actual == "MEDICION_GEN":       
        
        with HP3458A("GPIB0::22::INSTR") as dvm:
            Medicion_Generador=dvm.configurar_y_medir_sweep(Cant_Muestras, Sweep_time, Aper_Time)
        
        Funciones.Guardar_Medicion_Config(ruta_medicion_generador,Medicion_Generador,Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time)
        
        input("Cambiar posición de llave para medir la tensión en el capacitor y presionar Enter")      
        
        estado_actual = "MEDICION_MUL"

########################################################################################################################################################           

    elif estado_actual == "MEDICION_MUL":
        
        with HP3458A("GPIB0::22::INSTR") as dvm:
            Medicion_Capacitor=dvm.configurar_y_medir_sweep(Cant_Muestras, Sweep_time, Aper_Time)
        
        Funciones.Guardar_Medicion(ruta_medicion_CargayDescarga,Medicion_Capacitor)
        
        estado_actual = "CALCULO"

########################################################################################################################################################    
    elif estado_actual == "EXTRACCION": 
        
        Funciones.limpiar_pantalla()
        # Cargar datos en arrays
        Medicion_Generador = np.loadtxt(ruta_medicion_generador)  # ajustá delimiter si hace falta
        Medicion_Capacitor = np.loadtxt(ruta_medicion_CargayDescarga)
        
        # Opcional: mostrar tamaños
        print("Datos generador cargados:", Medicion_Generador.shape)
        print("Datos capacitor cargados:", Medicion_Capacitor.shape)

        estado_actual = "CALCULO"
######################################################################################################################################################## 

    elif estado_actual == "CALCULO":
        
        Funciones.limpiar_pantalla()
        V_max, Gen_std = Funciones.analizar_senal_cuadrada(Medicion_Generador)
        Funciones.Procesamiento_CargayDescarga(ruta_medicion_CargayDescarga,Medicion_Capacitor,V_max,Sweep_time,Vn_Rp)
        input("Presionar Enter para continuar") 
        Funciones.limpiar_pantalla()

########################################################################################################################################################
    
    elif estado_actual == "FINALIZACION":
        
        input("Presionar Enter para continuar") 
        Funciones.limpiar_pantalla()
        break
########################################################################################################################################################
    
    else:
        Funciones.limpiar_pantalla()
        break
########################################################################################################################################################