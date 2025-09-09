####################################################################################
# Este programa toma una curva real o ideal del Ruta seleccionado y devuelve 
# un valor de capacidad, su desvío y error con el método de linealización de la cur-
# va de carga.
# La librería útilizada es linregress de scipy.
####################################################################################  

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress
import scipy.stats as stats
import datetime
import os

Ruta_entrada   = 'E:\\Data\\INTI\\Proyectos\\Escaner\\Escaner_v1\\datos\\Carga\\'
Archivo        = 'CargaMedicion_2024-12-05_15-56-16.txt'
Ruta_Archivo   = Ruta_entrada+Archivo

fecha_hora     = datetime.datetime.now()
Ruta_Salida    = 'E:\\Data\\INTI\\Proyectos\\Escaner\\Escaner_v1\\datos\\Resultados\\'+fecha_hora.strftime("%Y-%m-%d_%H-%M-%S")+'\\'
os.makedirs(Ruta_Salida, exist_ok=True)
Grafico_Salida = fecha_hora.strftime("Plot_%Y-%m-%d_%H-%M-%S.jpg")

##### DATOS A CARGAR######
Rpatron    = 1.000096e3 # R 
Cpatron  =  0.999830  # en uF

# En microfaradios

#Cpatron  = 207.04   
#Cpatron  = 0.999830 # 1 uf
#Cpatron  = 0.1001087    # 0,1 uF       
#Cpatron  = 2.3333   # 2 uF 
      

#########Thevenin de RC
Rcablegenerador1= 54e-3
Rcablegenerador2=31.152e6
Rcablemultimetro1=34e-3
Rcablemultimetro2=4.2e6
RDVM=10e9+5e3+5e3
Rserie1= (Rcablegenerador1*Rcablegenerador2)/(Rcablegenerador1+Rcablegenerador2) + Rpatron + Rcablegenerador1
Rserie2= (RDVM*Rcablemultimetro2)/(RDVM+Rcablemultimetro2)+Rcablemultimetro1


Rp    = Rserie1*Rserie2/(Rserie1+Rserie2) +162e-3
Rp = Rpatron
######



try:
    # Leer datos del archivo
    with open(Ruta_Archivo, 'r') as archivo:
        #Mediciones = [float(linea.strip()) for linea in archivo if linea.strip()]
        for i, linea in enumerate(archivo):
            if i < 13:
                print(linea.strip(), end=" ")  # Imprime las primeras 6 líneas
                if i == 3:  # Si es la cuarta línea (índice 3), guardamos su valor
                    Temp = float(linea.strip())
                if i == 7:  # Si es la cuarta línea (índice 3), guardamos su valor
                    V_pico = float(linea.strip())
                if i == 9:  # Si es la cuarta línea (índice 3), guardamos su valor
                    V_offset = float(linea.strip())
                if i == 11:  # Si es la cuarta línea (índice 3), guardamos su valor
                    Sweep_Time = float(linea.strip())
                
            else:
            # A partir de la octava línea (índice 7) guarda los valores como flotantes
                print()
                Mediciones = [float(linea.strip()) for linea in archivo if linea.strip()]
                break
        
    # Inicializa vectores de resultados
    muestrasdeinicio = []  # Almacenará los números de muestra del inicio de carga
    muestrasdefin    = []  # Almacenará los números de muestra del final de carga
    cargando         = False  # Bandera para identificar si estamos en una carga
    enganche         = False
    
    #######################################
    V_max    =  V_pico-V_offset 
    V_dig    =  V_max*0.6321205588
    valor_inicial  = 0.01 * V_max 
    valor_final    = 0.99 * V_max  
    Extremo_de_ventana_inf = 0.3
    Extremo_de_ventana_sup = 0.7

#################################
    # Procesa los datos
    for i, valor in enumerate(Mediciones, start=1):   
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

except FileNotFoundError:
    print(f"El archivo no se encontró en la ruta: {Ruta_Archivo}")
except ValueError:
    print("El archivo contiene datos no válidos.")
except Exception as e:
    print(f"Ocurrió un error: {e}")




#############################################
R_Cuadrado = 0.999
Indice     = 0

####################################################

# Datos de DVM HP3458
#Temp = None  # Inicializamos la variable de temperatura
HP3458_Accuracy_T = 1e-4
HP3458_Offset_T   = 5e-9
HP3458_Resolu_T   = 1e-7
HP3458_Jitter_T   = 1e-10
HP3458_Accuracy_V = 14e-6
#HP3458_Resolu_V   = 4.5/1e-6
#HP3458_Gain_V     = 10/1e-6
HP3458_Offset_V    =1e-6 
HP3458_Gain_error_V = 60e-6 # pag 99 sampling with ...
HP3458_Resolution_V = 1/200000 #pag 51 // 5 dig y medio // Synthesys and Sampling
HP3458_Linearity_Vdig = ((0.3e-6 * V_dig)+ (0.1e-6) * V_max) # Manual 3458
HP3458_Linearity_Vmax = ((0.3e-6 * V_max)+ (0.1e-6) * V_max) # Manual 3458

##################################################3


Muestras_Filtradas   = []
Muestras_Validas     = []
Numero_de_Muestras_Filtradas =[]
Cantidad_inicios = len(muestrasdeinicio)
Cantidad_finales = len(muestrasdefin)

#Si la cantidad de inicios y finales fuesen distintos tomaria el de menor valor 'n'
Cantidad_ciclos  = min(len(muestrasdeinicio), len(muestrasdefin))
#Tomo finalmente los primeros 'n' valores
muestrasdeinicio = muestrasdeinicio[:Cantidad_ciclos]
muestrasdefin    = muestrasdefin[:Cantidad_ciclos]

slope_vector    =[]   
intercept_vector=[]
r_value_vector  =[]
p_value_vector  =[]
std_err_vector  =[]
Cx_vector       =[]  
Muestras_de_Ciclo     =[0]*Cantidad_ciclos 
Muestras_de_Ciclo_Lin =[0]*Cantidad_ciclos 
Num_Muestras_de_Ciclo =[0]*Cantidad_ciclos 
Tiempo_Muestras_de_Ciclo =[0]*Cantidad_ciclos

# Leer los datos desde el archivo txt en un DataFrame de Pandas
#Mediciones_leidas = pd.read_csv(Ruta_Archivo, header=None, names=['Tensión'], sep='\s+')
Mediciones_leidas = pd.read_csv(Ruta_Archivo, header=None, names=['Tensión'], sep='\s+', skiprows=13)
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
    #print(r_value**2)
    if (r_value)**2 >R_Cuadrado:
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
    Cx[i] = (-1 / (slope_vector[i] * Rp))

#################################################
#Correccion de la capacidad por temperatura
Tref=23.0
alpha=-0.362e-3
beta= -8.8e-3
T=Temp

if Cpatron > 205 and Cpatron < 209:
    Cx_corregido = np.mean(Cx) * (1 + alpha * (T - Tref)+beta*(T-Tref)**2)
else:
    Cx_corregido = np.mean(Cx)

################################################
# Cálculo de la capacidad y parámetros de interés
slope_promedio     = np.mean(slope_vector)
slope_desv_est     = np.std(slope_vector)
intercept_promedio = np.mean(intercept_vector)
std_err_promedio   = np.mean(std_err_vector)
tau_promedio       = -1 / slope_promedio
Cx_promedio        = np.mean(Cx)
Cx_desv_est        = np.std(Cx)
error_C            = std_err_promedio/ ((slope_promedio**2) * Rp)
error_patron       = ((Cpatron-Cx_corregido*1e6)/Cpatron) *100  
r2                 = np.mean(r_value_vector) ** 2

# Grados de libertad
df = Cantidad_de_muestras - 2  
# Valor crítico t para el intervalo de confianza del 95%
t_critical = stats.t.ppf(0.975, df)
# Incertidumbre de la pendiente (intervalo de confianza)
uncertainty_slope = t_critical * std_err_promedio


###################### Cálculo de la incertidumbre combinada ##############################
Tiempo_tau_nominal  = Rp*Cpatron        #[seg]
factor_r    =1/np.sqrt(3)
factor_g =  2

# Coeficientes de sensibilidad del modelo C=tau/R
dC_dtau =  1 / Rp
dC_dRp  = tau_promedio/Rp**2  

# Incertidumbre medida de resistencia de referencia con multimetro en ohm 
uRp        = 12e-6*Rp 


gamma= V_dig/V_max
# Coeficientes de sensibilidad del modelo tau=-t/ln(1-Vdig/Vm)
dtau_dt     = 1/np.log(1-V_dig/V_max)
dtau_dgamma = tau_promedio/(np.square(np.log(1-gamma)))*(1-gamma)

dgamma_dVDIG   = 1 / V_max
dgamma_dVM     = V_dig / V_max**2

ut     = np.sqrt(((HP3458_Accuracy_T*tau_promedio)+HP3458_Offset_T)/factor_r)**2 + (HP3458_Resolu_T/(2*factor_r))**2 +(HP3458_Jitter_T /(2*factor_r))**2

uVDIG = np.sqrt(
    (HP3458_Accuracy_V * V_dig / factor_r)**2 + 
    (HP3458_Offset_V / factor_r)**2 +
    (HP3458_Gain_error_V*V_dig / factor_g)**2 + 
    (HP3458_Resolution_V*V_dig / factor_r)**2 +
    (HP3458_Linearity_Vdig *V_dig / factor_r)**2
) 

 
uVM  = np.sqrt(
    (HP3458_Accuracy_V*V_max/factor_r)**2 + (HP3458_Offset_V/factor_r)**2 +  (HP3458_Gain_error_V*V_max /factor_g)**2 + (HP3458_Resolution_V*V_max  /factor_r)**2 +  (HP3458_Linearity_Vmax * V_max  /factor_r)**2 )
    

ugamma= np.sqrt((dgamma_dVDIG*uVDIG)**2 +dgamma_dVM*uVM**2)
# Incertidumbre tipo a obtenida de función de linealización
utau_A     = slope_desv_est/((slope_promedio**2)*(Cantidad_ciclos)**(1/2))   

# Se suman cuadráticamente las u obtenidas a partir de datos del manual del HP3458
utau   = np.sqrt(utau_A**2 + (dtau_dt*ut)**2 + (dtau_dgamma*ugamma)**2)

# Incertidumbre combinada en uF
uc=1e6*np.sqrt((dC_dtau*utau)**2 + (dC_dRp*uRp)**2)

uc_porcentual= uc*100/Cpatron
############################################################################################


########################## Muestra de Resultados en Terminal ###############################

print(f"Datos obtenidos de ruta      :\n {Ruta_Archivo}\n")
print(f"Resistencia Patrón (Rp)      : {round(Rp,4)} ohm")
print(f"Capacidad Patrón   (Cp)      : {round(Cpatron,6)} uF")
print(f"Capacidad promedio (Cx)      : {round(Cx_promedio*1e6,6)} uF")
print(f"Cap corregida por temp (Cct) : {round(Cx_corregido*1e6,6)} uF")
print(f"Incertidumbre combinada      : {round(uc,7)} uF")
#print(f"Incertidumbre Rp             : {round(uc,7)} %")
#print(f"Incertidumbre Vdig             : {round(uc,7)} %")
#print(f"Incertidumbre Vm             : {round(uc,7)} %")
#print(f"Incertidumbre tao             : {round(uc,7)} %")
#print(f"Incertidumbre tiempo            : {round(uc,7)} %")
print(f"Incertidumbre combinada en % : {round(uc_porcentual,5)} %")
print(f"Error respecto a {Cpatron} uF : {round((error_patron),3)} %")

############################################################################################
'''
################### Ploteo de Señal Digitalización Filtrada y Linializada###################
for i in range(Cantidad_ciclos_validos):
    # Crear una figura con 2 subgráficos (uno al lado del otro)
    fig, axs = plt.subplots(1, 2, figsize=(10, 3))  # 1 fila y 2 columnas de subgráficos

    # Primer subgráfico: Señal sin procesar
    axs[0].plot(Num_Muestras_de_Ciclo[i], Muestras_de_Ciclo[i], 'bo', label='Tensión (V)')
    axs[0].set_xlabel('Muestras')
    axs[0].set_ylabel('Tensión (V)')
    axs[0].set_title(f"Ciclo {i+1} - Señal sin procesar")
    axs[0].legend()
    axs[0].grid()

    # Segundo subgráfico: Señal procesada
    axs[1].plot(Num_Muestras_de_Ciclo[i], Muestras_de_Ciclo_Lin[i],'bo', label='ln(VDIG/VM+1)')
    axs[1].set_xlabel('Muestras')
    axs[1].set_ylabel('Tensión (V)')
    axs[1].set_title(f"Ciclo {i+1} - Señal procesada")
    axs[1].legend()
    axs[1].grid()

    # Ajustar el layout para que no se solapen las etiquetas
    plt.tight_layout()
    Grafico_Salida = fecha_hora.strftime(f"%Y-%m-%d_%H-%M-%S_Ciclo{i+1}.jpg")
    plt.savefig(Ruta_Salida+Grafico_Salida)
    # Mostrar el gráfico
    plt.show()
############################################################################################

################################ Guardado de parámetros ####################################
archivoPendientes = Ruta_Salida+'Pendientes.txt'
with open(archivoPendientes, "w") as file:
    for element in slope_vector:
        file.write(str(element) + '\n' )
    file.close()
archivoOrdenada = Ruta_Salida+'Ordenadas.txt'
with open(archivoOrdenada, "w") as file:
    for element in intercept_vector:
        file.write(str(element) + '\n' )
    file.close()

archivoResumen = Ruta_Salida+'Resumen.txt'
with open(archivoResumen, "w") as file:
    file.write('Capacidad promedio (Cx)  : '+str(round(Cx_promedio*1e6,6)) + 'uF \n' )
    file.write('Incertidumbre expandida  : '+str(round(uc,7)) + 'uF \n' )
    file.write('Incertidumbre expandida %: '+str(round(uc_porcentual,3)) + '% \n' )
    file.write('Error respecto a patrón ('+str(Cpatron)+')  : '+str(round(abs(error_patron),3)) + 'uF \n' )
    file.write(f"derivada respecto a tau: {dC_dtau} \n" )
    file.write(f"Incertidumbre que aporta el tau: {utau} \n" )
    file.write(f"Incertidumbre que aporta el Rp : {uRp} \n" )
    file.close()
############################################################################################
'''
# Error promedio
# print(std_err_promedio)
# Incertidumbre
# print(uncertainty_slope)
# print(f"derivada respecto a tau: {dC_dtau}")
# print(f"derivada respecto a Rp: {dC_dRp}")
# print(f"incertidumbre del tipo A de tau: {utau_A} uF")
# print(f"incertidumbre del tipo B de tau: {utau_B} uF")
# print(f"Desvío estándar (Cx)         : {Cx_desv_est*1e6} uF")
# print(f"Tau                          : {tau_promedio }")
# print(f"Error promedio (Cx)          : {error_C*1e6} uF")
# print(f"R^2                          : {r2:.4f}")
# print ("promedio slope",slope_promedio)
# print ("SEm",std_err_promedio)
# print ("incert tau B",utau_B)
# print ("incert tau A",utau_A)
# utau_B  = 2.16*1e-6

'''
# Graficar el Ciclo 1
plt.figure(figsize=(8, 6))
plt.plot(Num_Muestras_de_Ciclo[0], Muestras_de_Ciclo_Lin[0],'bo', label='ln(VDIG/VM+1)')
plt.xlabel('Muestras')
plt.ylabel('Tensión (V)')
plt.title("Ciclo 1 - Señal procesada")
plt.legend()
plt.grid()
plt.show()

# Guardar datos del Ciclo 1 en un archivo de texto
with open("ciclo_1.txt", "w") as f:
    f.write("Muestras\tTensión\n")
    for muestra, valor in zip(np.round(Num_Muestras_de_Ciclo[0] * Sweep_Time, 4), Muestras_de_Ciclo_Lin[0]):
        f.write(f"{muestra}\t{valor}\n")

print("Datos del Ciclo 1 guardados en 'ciclo_1.txt'.")'''
######################################################################################



