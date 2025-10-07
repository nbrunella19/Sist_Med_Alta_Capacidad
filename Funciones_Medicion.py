################################## LIBRERIAS ###############################################
import os
import json
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
from scipy.stats import linregress
from pathlib import Path

#############################################################################################
Extremo_de_ventana_inf = 0.3
Extremo_de_ventana_sup = 0.7
R_Cuadrado = 0.999
Cant_Muestras = 10000

###############################################################################################
# Datos de DVM HP3458 
HP3458_Accuracy_T   = 1e-4
HP3458_Offset_T     = 5e-9
HP3458_Resolu_T     = 1e-7
HP3458_Jitter_T     = 1e-10
HP3458_Accuracy_V   = 14e-6
HP3458_Offset_V     = 1e-6 
HP3458_Gain_error_V = 60e-6         # pag 99 sampling with ...
HP3458_Resolution_V = 1/200000      #pag 51 // 5 dig y medio // Synthesys and Sampling


################################## Valores de Cables ###########################################

Rcablegenerador1  = 54e-3
Rcablegenerador2  = 31.152e6
Rcablemultimetro1 = 34e-3
Rcablemultimetro2 = 4.2e6
RDVM              = 10e9+5e3+5e3

##################################  FUNCIONES GENERALES  ########################################

def Calculo_Ciclos(Cx,Rp,Ciclos,tau_por_ciclo,Cant_Muestras):
    tau                = (float(Cx)/1000000)*float(Rp)
    periodo            = float(tau_por_ciclo*2*tau)
    frec_recomendada   = str(round((1/periodo),1))
    sweep_time         = periodo*Ciclos/Cant_Muestras
    return tau,frec_recomendada,sweep_time   
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
###############################################################################################################################################################
###############################################################################################################################################################
def Procesamiento_CargayDescarga(Ruta_Medicion_Carga_Descarga,Medicion_Capacitor,V_max,Sweep_Time,Rp,Rcablegenerador):
    """
    Entrada: Ruta del archivo de medición, Vector de muestras, Valor máximo de tensión del generador, Tiempo entre muestras,
              Valor de resistencia patrón, Resistencia del cable del generador.
    Retorna: Vector de capacidades calculadas, vectores de parámetros de la linealización, cantidad de ciclos válidos,
    Función: Procesa los datos de medición de tensión en la carga del capacitor para calcular su valor nominal y la incertidumbre asociada.
    """
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

    Muestras_de_Ciclo        =[0]*Cantidad_ciclos 
    Muestras_de_Ciclo_Lin    =[0]*Cantidad_ciclos 
    Num_Muestras_de_Ciclo    =[0]*Cantidad_ciclos 
    Tiempo_Muestras_de_Ciclo =[0]*Cantidad_ciclos

    Mediciones_leidas = pd.read_csv(Ruta_Medicion_Carga_Descarga, header=None, names=['Tensión'], sep='\s+', skiprows=13)
    
    Cantidad_de_muestras= len(Mediciones_leidas)
    
    # Genera el vector de tiempo en función del `timer`
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
        # slope esla inversa negativa de tau
        # intercept es el valor de y cuando x=0
        # r_value es el coeficiente de correlación
        # p_value es el valor p para la hipótesis nula que la pendiente es cero
        # std_err es la desviación estándar del error de la pendiente
        # Acá se hace la REGRESION LINEAL
        slope, intercept, r_value, p_value, std_err= linregress(Muestras_Filtradas_aux['Tiempo'], Muestras_de_Ciclo_Lin[Indice])
               
        # Evalua si la medición es válida según el coeficiente de determinación R^2
        if (r_value)**2 > R_Cuadrado:

            # Si es válida, almacena los resultados    
            slope_vector.append(slope)  
            intercept_vector.append(intercept)
            r_value_vector.append(r_value)
            p_value_vector.append(p_value)
            std_err_vector.append(std_err)
        
    # Obtengo el número de ciclos válidos
    Cantidad_ciclos_validos = len(slope_vector)   

    Numero_Muestras_Finales = [item for sublista in Numero_de_Muestras_Filtradas for item in sublista]
    Muestras_Filtradas      = [elemento for sublista in  Muestras_Filtradas  for elemento in sublista]


    # Creación del vector de capacidad sabiendo que: C = tau/R y tau = -1/slope  => C = -1/R*slope
    Cx=[0]*Cantidad_ciclos_validos

    for i in range(Cantidad_ciclos_validos):
        Cx[i] = (-1 / float((slope_vector[i]) * float(Rp+Rcablegenerador)))

    #Devuelve los valores calculados para su análisis posterior
    return Cx,slope_vector,intercept_vector,r_value_vector,std_err_vector,Cantidad_ciclos_validos,Cantidad_de_muestras,V_dig

##################################################################################################################################################################
##################################################################################################################################################################


##################################################################################################################################################################
##################################################################################################################################################################

def Calculo_Valor_Medio(Vector):
    """
    Entrada: Vector de datos.
    Salida: Valor promedio del vector.
    """   
    Promedio = np.mean(Vector)
    return Promedio

##################################################################################################################################################################
##################################################################################################################################################################

def Calculo_Incertidumbre(Cx,slope_vector,intercept_vector,r_value_vector,std_err_vector,Cantidad_ciclos,Cantidad_de_muestras,V_dig,V_max,Vn_Cx,Vn_Rp):

    slope_promedio     = np.mean(slope_vector)
    slope_desv_est     = np.std(slope_vector)
    intercept_promedio = np.mean(intercept_vector)
    std_err_promedio   = np.mean(std_err_vector)
    tau_promedio       = -1 / slope_promedio
    error_C            = std_err_promedio/ ((slope_promedio**2) * Vn_Rp) 
    
    # Incertidumbre tipo B (división entre sqrt(3) para distribución rectangular)
    factor_r    =1/np.sqrt(3)
    factor_g =  2

    # Coeficientes de sensibilidad del modelo C=tau/R
    dC_dtau =  1 / Vn_Rp
    dC_dRp  = tau_promedio/Vn_Rp**2  

    # Incertidumbre medida de resistencia de referencia con multimetro en ohm 
    uRp        = 12e-6* Vn_Rp 
    
    # Razón de tensiones
    gamma= V_dig/V_max
    
    # Coeficientes de sensibilidad del modelo tau=-t/ln(1-Vdig/Vm)
    dtau_dt     = 1/np.log(1-V_dig/V_max)
    dtau_dgamma = -tau_promedio / ((1 - gamma) * np.square(np.log(1 - gamma))) # equivalente: -tau_promedio / ((1 - gamma) * (np.log(1 - gamma)**2))

    dgamma_dVDIG   = 1 / V_max
    dgamma_dVM     = V_dig / V_max**2

    ut     = np.sqrt(((HP3458_Accuracy_T*tau_promedio)+HP3458_Offset_T)/factor_r)**2 + (HP3458_Resolu_T/(2*factor_r))**2 +(HP3458_Jitter_T /(2*factor_r))**2

    uVDIG = np.sqrt(
        (HP3458_Accuracy_V * V_dig / factor_r)**2 + 
        (HP3458_Offset_V / factor_r)**2 +
        (HP3458_Gain_error_V*V_dig / factor_g)**2 + 
        (HP3458_Resolution_V*V_dig / factor_r)**2 
    ) 
  
    uVM  = np.sqrt(
        (HP3458_Accuracy_V*V_max/factor_r)**2 + (HP3458_Offset_V/factor_r)**2 +  (HP3458_Gain_error_V*V_max /factor_g)**2 + (HP3458_Resolution_V*V_max  /factor_r)**2 )
        
    ugamma= np.sqrt((dgamma_dVDIG*uVDIG)**2 +dgamma_dVM*uVM**2)
    
    # Incertidumbre tipo a obtenida de función de linealización
    utau_A     = slope_desv_est/((slope_promedio**2)*(Cantidad_ciclos)**(1/2))   

    # Se suman cuadráticamente las u obtenidas a partir de datos del manual del HP3458
    utau   = np.sqrt(utau_A**2 + (dtau_dt*ut)**2 + (dtau_dgamma*ugamma)**2)

    # Incertidumbre combinada en uF
    uc=1e6*np.sqrt((dC_dtau*utau)**2 + (dC_dRp*uRp)**2)

    uc_porcentual= uc*100/Vn_Cx

    return  uc, uc_porcentual


##################################################################################################################################################################

##################################################################################################################################################################

def Mostrar_Resultados(Cx_promedio,uc,uc_porcentual,Vn_Rp,ruta_medicion_generador,ruta_medicion_CargayDescarga):
    print(f"Archivo de Medición del Generador  :\n {ruta_medicion_generador}\n")
    print(f"Archivo de Medición del Multímetro :\n {ruta_medicion_CargayDescarga}\n")
    print(f"Valor de resistencia nominal del patrón (Rp)      : {round(Vn_Rp,4)} ohm")
    print(f"Capacidad promedio (Cx)      : {round(Cx_promedio*1e6,6)} uF")
    print(f"Incertidumbre combinada      : {round(uc,7)} uF")
    print(f"Incertidumbre combinada en % : {round(uc_porcentual,5)} %")

##################################################################################################################################################################