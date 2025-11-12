######################################################################################################################################################################################
############################################################################# LIBRERIAS ##############################################################################################
###################################################################################################################################################################################### 

import Funciones_Archivos
import Funciones_Medicion
import numpy as np
import scipy.stats as stats
from pathlib import Path
from scipy.stats import linregress
from Instrumental.HP3458A import HP3458A
from Instrumental.HP3245A import HP3245A
from Instrumental.AFG1022 import TektronixAFG1022
from Instrumental.KL2110 import Keithley2110

###################################################################################################################################################################################### 
####################################################################### VARIABLES GLOBALES ###########################################################################################
######################################################################################################################################################################################

#estado_actual  = "INICIO"
estado_actual  = "FINALIZACION"
Cant_Muestras  = 10000
Aper_Time      = 3e-6
Rcablegenerador  = 88e-3
tau_por_ciclo_on = 5

######################################################################################################################################################################################
######################################################################################################################################################################################
while True: ######################################################## BUCLE PRINCIPAL DE PROGRAMA ##################################################################################
######################################################################################################################################################################################
######################################################################################################################################################################################

######################################################################################################################################################################################
######################################################################### INICIO DEL BUCLE ########################################################################################
######################################################################################################################################################################################

    if estado_actual == "INICIO":
        Funciones_Archivos.limpiar_pantalla()
        opcion = Funciones_Archivos.Mostrar_Menu()
        estado_actual = "MODO_USO"

######################################################################################################################################################################################
######################################################################## MODO DE APLICACION #######################################################################################
######################################################################################################################################################################################    

    elif estado_actual == "MODO_USO":
    
        Funciones_Archivos.limpiar_pantalla()
        Funciones_Archivos.limpiar_teclado()
        modo_u = Funciones_Archivos.Menu_Inicial()

        # Opción 1: Nuevo análisis        
        if modo_u == '1':

            # Limpio pantalla y elijo instrumental
            Funciones_Archivos.limpiar_pantalla()
            set_u  = Funciones_Archivos.Menu_Instrumental()
            
            # Obtengo rutas de archivos de medición y configuración
            Ruta_Medicion_Entrada, Ruta_Medicion_Carga_Descarga, Ruta_archivo_config = Funciones_Archivos.Ruta_de_analisis_nuevo()
            
            Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time, Cantidad_Ciclos = Funciones_Archivos.Configuracion()
            
            estado_actual = "INICIALIZACION"
            

        # Opción 2: Análisis desde archivos existente 
        elif modo_u== '2':
            Funciones_Archivos.limpiar_pantalla()
            
            # Limpio pantalla y elijo instrumental
            set_u  = Funciones_Archivos.Menu_Instrumental()
            
            # Obtengo rutas y configuración ya existentes
            Ruta_Medicion_Entrada, Ruta_Medicion_Carga_Descarga, Ruta_archivo_config, Archivo_Generador, Archivo_Capacitor, Archivo_Config = Funciones_Archivos.Ruta_de_analisis_existente()
            Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time = Funciones_Archivos.extraccion_datos(Ruta_archivo_config)
            
            estado_actual = "EXTRACCION"
        
        else:
            Funciones_Archivos.limpiar_pantalla()
            print("Opción incorrecta")
            modo_u = Funciones_Archivos.Menu_Inicial()  
            Funciones_Archivos.limpiar_pantalla()
            Funciones_Archivos.limpiar_teclado()
            #set_u  = Funciones_Archivos.Menu_Instrumental()
    

######################################################################################################################################################################################
################################################################## INICIALIZA GENERADOR DE TENSION ###############################################################################
######################################################################################################################################################################################  

    elif estado_actual == "INICIALIZACION":   
        
        with HP3245A("GPIB0::9::INSTR") as gen:
            gen.configurar_generador_full(
            Frec= Frec,
            Sweep_Time     = Sweep_time,    
        )
        estado_actual = "MEDICION_GEN"

######################################################################################################################################################################################
########################################################## CONFIGURA MULTIMETRO Y MIDE GENERADOR DE TENSION ######################################################################
######################################################################################################################################################################################  
         
    elif estado_actual == "MEDICION_GEN":       
        
        with HP3458A("GPIB0::22::INSTR") as dvm:
            Medicion_Generador=dvm.configurar_y_medir_tension(Cant_Muestras, Sweep_time, Aper_Time)
        
        Funciones_Archivos.Guardar_Medicion(Ruta_Medicion_Entrada,Medicion_Generador)
        Funciones_Archivos.Guardar_Medicion_Config(Ruta_archivo_config,Modo,Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time)
        
        input("Cambiar posición de llave para medir la tensión en el capacitor y presionar Enter")      
        
        estado_actual = "MEDICION_MUL"

######################################################################################################################################################################################
############################################################ CONFIGURA MULTIMETRO Y SOBRE EL CAPACITOR #########################################################################
######################################################################################################################################################################################            

    elif estado_actual == "MEDICION_MUL":
        
        with HP3458A("GPIB0::22::INSTR") as dvm:
            Medicion_Capacitor=dvm.configurar_y_medir_tension(Cant_Muestras, Sweep_time, Aper_Time)
        
        Funciones_Archivos.Guardar_Medicion(Ruta_Medicion_Carga_Descarga,Medicion_Capacitor)
        
        
        estado_actual = "CALCULO"

######################################################################################################################################################################################
################################################################# EXTRAE MEDICIONES DE ARCHIVOS YA CREADOS ###########################################################################
######################################################################################################################################################################################     

    elif estado_actual == "EXTRACCION": 
        
        Funciones_Archivos.limpiar_pantalla()
        
        # Se transforman los archivos en formato txt a ndarrays
        Medicion_Generador = np.loadtxt(Ruta_Medicion_Entrada)            
        Medicion_Capacitor = np.loadtxt(Ruta_Medicion_Carga_Descarga)
        
        #Muestro por pantalla la cantidad de datos cargados
        print("Datos generador cargados:", Medicion_Generador.shape)
        print("Datos capacitor cargados:", Medicion_Capacitor.shape)

        estado_actual = "CALCULO"

######################################################################################################################################################################################
####################################################################### PROCESAMIENTO DE DATOS PARA EL CALCULO #######################################################################
######################################################################################################################################################################################  

    elif estado_actual == "CALCULO":
        
        Funciones_Archivos.limpiar_pantalla()
        V_max, V_max_std = Funciones_Medicion.analizar_senal_cuadrada(Medicion_Generador)
        
        Cx_vector,slope_vector,intercept_vector,r_value_vector,std_err_vector,Cantidad_ciclos_validos,Cantidad_de_muestras,V_dig = Funciones_Medicion.Procesamiento_CargayDescarga(
                                                                                                                                    Ruta_Medicion_Carga_Descarga,                                                                                                                                    
                                                                                                                                    Medicion_Capacitor,
                                                                                                                                    V_max,
                                                                                                                                    Sweep_time,
                                                                                                                                    Vn_Rp,
                                                                                                                                    Rcablegenerador)
        
        Cx         = np.mean(Cx_vector)
        ucx, ucxp  = Funciones_Medicion.Calculo_Incertidumbre(Cx,slope_vector,intercept_vector,r_value_vector,std_err_vector,Cantidad_ciclos_validos,Cantidad_de_muestras,V_dig,V_max,Vn_Cx,Vn_Rp)
        
        Funciones_Medicion.Mostrar_Resultados(Cx,ucx, ucxp, Vn_Rp,Ruta_Medicion_Entrada,Ruta_Medicion_Carga_Descarga,Ruta_archivo_config)
        
        input("Presionar Enter para continuar") 
        Funciones_Archivos.limpiar_pantalla()
        estado_actual = "FINALIZACION"

########################################################################################################################################################
#################################################### FINALIZACION DEL PROGRAMA #########################################################################
######################################################################################################################################################## 
    
    elif estado_actual == "FINALIZACION":
        estado_actual = Funciones_Archivos.Menu_Final()

########################################################################################################################################################
######################################################################################################################################################## 
    
    else:
        Funciones_Archivos.limpiar_pantalla()
        break

########################################################################################################################################################
######################################################################################################################################################## 