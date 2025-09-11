################################## LIBRERIAS ###############################################
import os
import time
import struct
import pyvisa
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
from scipy.stats import linregress
from pathlib import Path
import json

#############################################################################################
Extremo_de_ventana_inf = 0.3
Extremo_de_ventana_sup = 0.7
R_Cuadrado = 0.999
Indice     = 0
Cant_Muestras = 10000
#############################################################################################
Array_Generador  = ["HP3245A","HPXXXX"]
Array_Multimetro = ["HP3458A","HPXXXX"]
#############################################################################################
# Datos de DVM HP3458 
HP3458_Accuracy_T   = 1e-4
HP3458_Offset_T     = 5e-9
HP3458_Resolu_T     = 1e-7
HP3458_Jitter_T     = 1e-10
HP3458_Accuracy_V   = 14e-6
HP3458_Offset_V     = 1e-6 
HP3458_Gain_error_V = 60e-6         # pag 99 sampling with ...
HP3458_Resolution_V = 1/200000      #pag 51 // 5 dig y medio // Synthesys and Sampling
################################################################################################
###################################Valores de Cables############################################
Rcablegenerador1= 54e-3
Rcablegenerador2=31.152e6
Rcablemultimetro1=34e-3
Rcablemultimetro2=4.2e6
RDVM=10e9+5e3+5e3
##################################  FUNCIONES GENERALES  ########################################

def Mostrar_Menu():
    print("\n--- Menú Principal ---")
    opcion = input("Presione Enter para empezar")
    return opcion
    
def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def Menu_Inicial():
    
    print("\n--- Modo de aplicación ---\n") 
    print("1. Medir y calibrar")
    print("2. Calcular desde una medición ya existente")
    while True:
            
            opcion = input("Introducir Set (1 o 2):\n")
            if opcion != "1" and opcion != "2":
                limpiar_pantalla()
                print("\n--- Modo de aplicación ---\n") 
                print("1. Medir y calibrar")
                print("2. Calcular desde una medición ya existente")
                    
            else:
                break
        
    return opcion   

def Ruta_de_analisis_existente():
    # --- pedir y validar ruta del generador ---
    limpiar_pantalla()
    while True:
        ruta_generador_str = input("Introducir la ruta de archivo de medición de generador:\n")
        ruta_generador = Path(ruta_generador_str)
        if ruta_generador.exists():
            ruta_generador = ruta_generador.resolve()  # normalizar ruta absoluta
            break
        print("⚠️ La ruta no existe o está mal escrita. Intente de nuevo.\n")

    # --- pedir y validar ruta de la curva de carga ---
    while True:
        ruta_curva_carga_str = input("Introducir la ruta de archivo de medición de curva de carga:\n")
        ruta_curva_carga = Path(ruta_curva_carga_str)
        if ruta_curva_carga.exists():
            ruta_curva_carga = ruta_curva_carga.resolve()
            break
        print("⚠️ La ruta no existe o está mal escrita. Intente de nuevo.\n")

    # --- obtener nombres de archivo ---
    nombre_archivo_generador = ruta_generador.name  # solo el nombre con extensión
    nombre_archivo_curva = ruta_curva_carga.name

    return (str(ruta_generador), str(ruta_curva_carga),
            nombre_archivo_generador, nombre_archivo_curva)

def Ruta_de_analisis_nuevo():
    # Base de ejecución
    base_path = Path(__file__).parent

    # Timestamp para nombre del archivo
    fecha_actual = datetime.datetime.now()
    nombre_archivo = fecha_actual.strftime("Medicion_%Y-%m-%d_%H-%M-%S.txt")

    # Carpetas
    carpeta_mediciones = base_path / "Mediciones" 

    Carpeta_Mediciones_Generador  = carpeta_mediciones / "Generador_1"
    Carpeta_Mediciones_Carga      = carpeta_mediciones / "Capacitor_1" 

    # Crear carpetas necesarias
    carpeta_mediciones.mkdir(parents=True, exist_ok=True)

    Carpeta_Mediciones_Generador.mkdir(parents=True, exist_ok=True)
    Carpeta_Mediciones_Carga.mkdir(parents=True, exist_ok=True)


    # Ruta final del archivo .txt
    ruta_medicion_generador = Carpeta_Mediciones_Generador / nombre_archivo
    ruta_medicion_CargayDescarga = Carpeta_Mediciones_Carga / nombre_archivo
 
    return str(ruta_medicion_generador), str(ruta_medicion_CargayDescarga)



def Menu_Instrumental():
    
    print("\n Seleccionar Set de medición \n")
    print("1. INTI")
    print("2. FRH")
    
    
    while True:
        
        opcion_generador = input("Introducir Set (1 o 2):\n")
        
        if opcion_generador == "1":
                    opcion = "Set INTI"
                    break
                   
        elif opcion_generador == "2":
                    opcion = "Set FRH"
                    break     
        else:
            limpiar_pantalla()
            print("\n Seleccionar Set de medición \n")
            print("1. INTI")
            print("2. FRH")
    
    return opcion   

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

def Calculo_Ciclos(Cx,Rp,Ciclos,tau_por_ciclo,Cant_Muestras):
    tau                = (float(Cx)/1000000)*float(Rp)
    periodo            = float(tau_por_ciclo*2*tau)
    frec_recomendada   = str(round((1/periodo),1))
    sweep_time         = periodo*Ciclos/Cant_Muestras
    return tau,frec_recomendada,sweep_time   



def Mostrar_Configuracion(Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec):
    print("\n--- Resumen de configuración ---\n") 
    print(f"Se utilizará el set de medición: {Modo}")
    print(f"Capacitor incognita de valor nominal : {Vn_Cx} uF")
    print(f"Resistor patrón de: {Vn_Rp} ohm")
    print(f"El tau esperado es de: {Vn_Tau} segundos")
    print("\n--- ------------------------- ---\n") 
    print(f"Se aplicará una señal cuadrada de valor tensión pico 1 V, montada sobre una contínua de 0.5 V y frecuencia de: {Frec} Hz \n")
  
    while True:
        entrada = input("Para continuar presione 1. Para volver a iniciar presione r\n")
        
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
                        
    Vn_Tau, Frec, Sweep_time = Calculo_Ciclos(Vn_Cx,Vn_Rp,Ciclos,Tau_x_ciclo, Cant_Muestras)              
        
    limpiar_pantalla()
        
    return Modo, Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time    

###################################################################################################################

def Procesamiento_CargayDescarga(Ruta,Medicion_Capacitor,V_max,Sweep_Time,Rp):

    # Inicializa vectores de resultados
    Muestras_Filtradas   = []
    Muestras_Validas     = []
    muestrasdeinicio     = []  # Almacenará los números de muestra del inicio de carga
    muestrasdefin        = []  # Almacenará los números de muestra del final de carga
    Numero_de_Muestras_Filtradas =[]
    V_offset            =  0.0
    
    R_Cuadrado = 0.999
    Indice     = 0
    
    cargando         = False  # Bandera para identificar si estamos en una carga
    enganche         = False
    
    V_dig            = V_max* 0.6321205588
    valor_inicial    = 0.01 * V_max 
    valor_final      = 0.99 * V_max  
    
    slope_vector    =[]   
    intercept_vector=[]
    r_value_vector  =[]
    p_value_vector  =[]
    std_err_vector  =[]
    Cx_vector       =[]  

    for i, valor in enumerate(Medicion_Capacitor, start=1):   
    # el enganche es como un trigger, es para sincronizar con el cero.  
        if not enganche and not cargando and valor <= valor_inicial:
            enganche = True
        # Una vez que se sincronizo con un cero analizo cuando sale del mismo.
        if not cargando and enganche and valor >= valor_inicial:
        # Detecta el inicio de una carga
            muestrasdeinicio.append(i)
            cargando = True
        #Va a cargar y adquirir datos hasta que llegue al final.
        elif cargando and valor >= valor_final:
        # Detectar el final de una carga
            muestrasdefin.append(i)
            cargando = False
            enganche = False
    
    Cantidad_inicios = len(muestrasdeinicio)
    Cantidad_finales = len(muestrasdefin)
    #Si la cantidad de inicios y finales fuesen distintos tomaria el de menor valor 'n'
    Cantidad_ciclos  = min(len(muestrasdeinicio), len(muestrasdefin))
    #Tomo finalmente los primeros 'n' valores
    muestrasdeinicio = muestrasdeinicio[:Cantidad_ciclos]
    muestrasdefin    = muestrasdefin[:Cantidad_ciclos]

    Muestras_de_Ciclo     =[0]*Cantidad_ciclos 
    Muestras_de_Ciclo_Lin =[0]*Cantidad_ciclos 
    Num_Muestras_de_Ciclo =[0]*Cantidad_ciclos 
    Tiempo_Muestras_de_Ciclo =[0]*Cantidad_ciclos

    Mediciones_leidas = pd.read_csv(Ruta, header=None, names=['Tensión'], sep='\s+', skiprows=13)
    Cantidad_de_muestras= len(Mediciones_leidas)
    # Generar el vector de tiempo en función del `timer`
    Mediciones_leidas['Tiempo'] = np.arange(0, Cantidad_de_muestras * Sweep_Time, Sweep_Time)

    for i in range(Cantidad_ciclos):
    
    # Seleccionar el rango de muestras especificado
        Muestras_Filtradas_aux  = Mediciones_leidas.iloc[muestrasdeinicio[i]:muestrasdefin[i]]

        # Filtrar los datos seleccionados para que estén entre 0.3V y 0.7V
        Muestras_Filtradas_aux = Muestras_Filtradas_aux [
            (Muestras_Filtradas_aux['Tensión'] >= Extremo_de_ventana_inf) & (Muestras_Filtradas_aux['Tensión'] <= Extremo_de_ventana_sup)
            ]  
        
        Muestras_de_Ciclo[Indice]      = Muestras_Filtradas_aux['Tensión']
        Num_Muestras_de_Ciclo[Indice]  = Muestras_Filtradas_aux.index  
        
        #Linealización los datos seleccionados
        Muestras_de_Ciclo_Lin[Indice] = np.log(1 - (Muestras_Filtradas_aux['Tensión']-V_offset) / V_max)

        # Calcular la pendiente de la curva linealizada usando una regresión lineal
        slope, intercept, r_value, p_value, std_err= linregress(Muestras_Filtradas_aux['Tiempo'], Muestras_de_Ciclo_Lin[Indice])
        if (r_value)**2 > R_Cuadrado:
            # Modificar el 0.999 a una variable de entrada modificable      
            slope_vector.append(slope)  
            intercept_vector.append(intercept)
            r_value_vector.append(r_value)
            p_value_vector.append(p_value)
            std_err_vector.append(std_err)
            Indice=Indice+1
        
    Numero_Muestras_Finales = [item for sublista in Numero_de_Muestras_Filtradas for item in sublista]
    Muestras_Filtradas      = [elemento for sublista in Muestras_Filtradas for elemento in sublista]
    Cantidad_ciclos_validos = len(slope_vector)


    Cx=[0]*Cantidad_ciclos_validos
    for i in range(Cantidad_ciclos_validos):
        Cx[i] = (-1 / float((slope_vector[i]) * float(Rp)))

    print(f"Capacidad promedio (Cx)      : {round((np.mean(Cx))*1e6,6)} uF")

#########################################################################################################
        
def analizar_senal_cuadrada(signal: np.ndarray, umbral: float = 0.01):
    """
    Analiza una señal cuadrada para obtener los valores promedio y desviación estándar de Von y Voff.
    """
# Estimar niveles
    v_max = np.max(signal)
    v_min = np.min(signal)
    amplitud = v_max - v_min

    # Estimar umbrales
    umbral_superior = v_max - umbral * amplitud
    umbral_inferior = v_min + umbral * amplitud

    # Clasificar valores
    von_values = signal[signal >= umbral_superior]
    voff_values = signal[signal <= umbral_inferior]

    # Calcular estadísticas
    von_mean = np.mean(von_values)
    von_std = np.std(von_values)

    voff_mean = np.mean(voff_values)
    voff_std = np.std(voff_values)

    V_max = von_mean - voff_mean

    
    if von_std>voff_std:
        Gen_std=von_std
    else:
        Gen_std=voff_std
        
    return  V_max, Gen_std

#########################################################################################################
def Guardar_Medicion(Ruta_Guardado,Medicion_Realizada):
    with open(Ruta_Guardado, "w") as file:         
            for dato in Medicion_Realizada:
                file.write(f"{dato}\n")  
#########################################################################################################
def Guardar_Medicion_Config(Ruta_Guardado, Medicion_Realizada, 
                     Vn_Cx=None, Vn_Rp=None, Vn_Tau=None, Frec=None, Sweep_time=None):
    # Guardar los datos de la medición en un archivo de texto
    with open(Ruta_Guardado, "w") as file:         
        for dato in Medicion_Realizada:
            file.write(f"{dato}\n")  
    
    # Si se pasaron los parámetros, guardarlos en un archivo JSON
    if None not in (Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time):
        parametros = {
            "Vn_Cx": Vn_Cx,
            "Vn_Rp": Vn_Rp,
            "Vn_Tau": Vn_Tau,
            "Frec": Frec,
            "Sweep_time": Sweep_time
        }
        
        ruta_json = Path(Ruta_Guardado).with_suffix(".json")
        with open(ruta_json, "w") as json_file:
            json.dump(parametros, json_file, indent=4)
#########################################################################################################