########################################################################################################################################################
######################################################################################################################################################## 
import Funciones_Archivos
import Funciones_Medicion
import numpy as np
import scipy.stats as stats
from pathlib import Path
from scipy.stats import linregress
from Instrumental.HP3458A import HP3458A
from Instrumental.HP3245A import HP3245A
########################################################################################################################################################
######################################################################################################################################################## 

estado_actual  = "INICIO"
Cant_Muestras  = 10000
Aper_Time      = 3e-6

########################################################################################################################################################
######################################################################################################################################################## 

while True:

########################################################################################################################################################
########################################################################################################################################################

    if estado_actual == "INICIO":
        Funciones_Archivos.limpiar_pantalla()
        opcion = Funciones_Archivos.Mostrar_Menu()
        estado_actual = "MODO_USO"

########################################################################################################################################################
########################################################################################################################################################    

    elif estado_actual == "MODO_USO":
    
        Funciones_Archivos.limpiar_pantalla()
        modo_u = Funciones_Archivos.Menu_Inicial()
        Funciones_Archivos.limpiar_pantalla()
        set_u  = Funciones_Archivos.Menu_Instrumental()
        
        if modo_u == "1":
            ruta_medicion_generador, ruta_medicion_CargayDescarga = Funciones_Archivos.Ruta_de_analisis_nuevo()
            Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time = Funciones_Archivos.Configuracion()
            estado_actual = "INICIALIZACION"
        
        elif modo_u== "2":
            ruta_medicion_generador, ruta_medicion_CargayDescarga, ruta_archivo_config, Archivo_Generador, Archivo_Capacitor, Archivo_Config = Funciones_Archivos.Ruta_de_analisis_existente()
            Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time = Funciones_Archivos.extraccion_datos(ruta_archivo_config)
            estado_actual = "EXTRACCION"
        
        else:
            Funciones_Archivos.limpiar_pantalla()
            print("Opción incorrecta. Ingresá 1 o 2.")
            modo_u = Funciones_Archivos.Menu_Inicial()  
            set_u  = Funciones_Archivos.Menu_Instrumental()

########################################################################################################################################################
########################################################################################################################################################  

    elif estado_actual == "INICIALIZACION":   
        
        with HP3245A("GPIB0::9::INSTR") as gen:
            gen.configurar_generador_full(
            Frec= Frec,
            Sweep_Time     = Sweep_time*1e6,    
        )
        estado_actual = "MEDICION_GEN"

########################################################################################################################################################
########################################################################################################################################################  
         
    elif estado_actual == "MEDICION_GEN":       
        
        with HP3458A("GPIB0::22::INSTR") as dvm:
            Medicion_Generador=dvm.configurar_y_medir_sweep(Cant_Muestras, Sweep_time, Aper_Time)
        
        Funciones_Archivos.Guardar_Medicion_Config(ruta_medicion_generador,Medicion_Generador,Modo,Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time)
        
        input("Cambiar posición de llave para medir la tensión en el capacitor y presionar Enter")      
        
        estado_actual = "MEDICION_MUL"

########################################################################################################################################################
########################################################################################################################################################            

    elif estado_actual == "MEDICION_MUL":
        
        with HP3458A("GPIB0::22::INSTR") as dvm:
            Medicion_Capacitor=dvm.configurar_y_medir_sweep(Cant_Muestras, Sweep_time, Aper_Time)
        
        Funciones_Archivos.Guardar_Medicion(ruta_medicion_CargayDescarga,Medicion_Capacitor)
        
        estado_actual = "CALCULO"

########################################################################################################################################################
########################################################################################################################################################     

    elif estado_actual == "EXTRACCION": 
        
        Funciones_Archivos.limpiar_pantalla()
        # Cargar datos en arrays
        Medicion_Generador = np.loadtxt(ruta_medicion_generador)  # ajustá delimiter si hace falta
        Medicion_Capacitor = np.loadtxt(ruta_medicion_CargayDescarga)
        

        print("Datos generador cargados:", Medicion_Generador.shape)
        print("Datos capacitor cargados:", Medicion_Capacitor.shape)

        estado_actual = "CALCULO"

########################################################################################################################################################
########################################################################################################################################################  

    elif estado_actual == "CALCULO":
        
        Funciones_Archivos.limpiar_pantalla()
        V_max, Gen_std = Funciones_Medicion.analizar_senal_cuadrada(Medicion_Generador)
        Cx,slope_vector,intercept_vector,r_value_vector,std_err_vector,Cantidad_ciclos_validos,Cantidad_de_muestras,V_dig =Funciones_Medicion.Procesamiento_CargayDescarga(ruta_medicion_CargayDescarga,Medicion_Capacitor,V_max,Sweep_time,Vn_Rp)
        Funciones_Medicion.Calculo_Incertidumbre(Cx,slope_vector,intercept_vector,r_value_vector,std_err_vector,Cantidad_ciclos_validos,Cantidad_de_muestras,V_dig,V_max,Vn_Cx,Vn_Rp,Medicion_Generador,Medicion_Capacitor)
        input("Presionar Enter para continuar") 
        Funciones_Archivos.limpiar_pantalla()
        estado_actual = "FINALIZACION"

########################################################################################################################################################
######################################################################################################################################################## 
    
    elif estado_actual == "FINALIZACION":
        
        input("La calibración ha finalizado. \nPresionar Enter para volver al menú principal") 
        Funciones_Archivos.limpiar_pantalla()
        estado_actual = "INICIO"

########################################################################################################################################################
######################################################################################################################################################## 
    
    else:
        Funciones_Archivos.limpiar_pantalla()
        break

########################################################################################################################################################
######################################################################################################################################################## 