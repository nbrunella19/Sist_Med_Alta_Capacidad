#########################################################################################################
# Este Código configura los canales de las fuente HP3245
# Canal A = Señal cuadrada de 1 Vpp con 4 Hz y 0.5 V de offset. Generación de escalón
# Canal B = Señal cuadrada de 5 Vpp con 4 Hz y 2.5 V de offset. Conectar para trigger externo de HP3458A
#########################################################################################################

import pyvisa
import time
import numpy as np


valor_capacitor=  1  # en microfaradios
valor_resistencia= 1000 # en ohms
cantidad_de_ciclos = 7
tau_por_ciclo_on   = 8

tau= (valor_capacitor/1000000)*valor_resistencia
periodo=tau_por_ciclo_on*2*tau

frec_recomendada=round((1/periodo),2)

sweep_time= round((periodo*cantidad_de_ciclos/10000)*1000000,0)



if sweep_time < 20:
  sweep_time = 20 
  cantidad_de_ciclos=0.2/(tau*2*tau_por_ciclo_on)
  print("Cantidad de ciclos por muestra = ",(cantidad_de_ciclos))
   
else:
  sweep_time=sweep_time
  print("Cantidad de ciclos por muestra = ",(cantidad_de_ciclos)) 

    
print("Taus por ciclo on = ",tau_por_ciclo_on)
print("La frecuencia recomendada para el capacitor de "+str(valor_capacitor)+" uF y la resistencia de "+str(valor_resistencia)+" ohms es de "+str(frec_recomendada)+" Hz")
print("El sweep time recomendado es de " +str(sweep_time) + " microsegundos")   

Proteccion_DVM_CHA = 1
Proteccion_DVM_CHB = 1



VPP_CHA=1
FREC_CHA = frec_recomendada
#FREC_CHA = 0.4 # para 207 uF
#FREC_CHA = 4   # para 1 uF CON R DE 10 K
#FREC_CHA = 40  # para 1 uF CON R DE 1 K
#FREC_CHA = 80  # para 1 uF CON R DE 100
OFFSET_CHA=0.5

VPP_CHB=5
FREC_CHB = frec_recomendada
#FREC_CHB = 0.4 # Para 207 uF
#FREC_CHB = 4   # para 1 uF con R de 10 K
#FREC_CHB = 40  # para 1 uF CON R DE 1 K
#FREC_CHB = 80  # para 1 uF CON R DE 100

OFFSET_CHB=2.5


print("\n")
rm = pyvisa.ResourceManager()
HP3245A=rm.open_resource("GPIB0::9::INSTR")
#Set the end of the line 
HP3245A.read_termination = '\n'
HP3245A.write_termination = '\n'

#Chequea comunicación PC <-->DVM
print('Keysight_3245A.query(\'ID?\') --> ' + HP3245A.query('ID?'))  
time.sleep(5)

try:
  HP3245A.write("RESET")
  HP3245A.write("CLR")
  HP3245A.write("SCRATCH")
  HP3245A.write("BEEP OFF")
  #ACI,ACV,DCI,DCV,DCMEMI,DCMEMV,RPI,RPV,SQI,SQV,WFI,WFV
  print("APPLY? command: ",HP3245A.query("APPLY?"))
  
  #Configuración de canal A
  HP3245A.write("USE CHANA") 
  # Valor de frecuencia en Hz
  HP3245A.write("FREQ "+str(FREC_CHA))
  # Valor de offset en V, max 50 % del rango
  HP3245A.write("DCOFF "+str(OFFSET_CHA))
  # Valor pico a pico en V 
  HP3245A.write("APPLY SQV "+str(VPP_CHA)) 

  #Configuración de canal B
  HP3245A.write("USE CHANB")
  #Idem canal A 
  HP3245A.write("FREQ "+str(FREC_CHB))
  HP3245A.write("DCOFF "+str(OFFSET_CHB))
  HP3245A.write("APPLY SQV "+str(VPP_CHB)) 
  
  #Sincroniza los canales.
  HP3245A.write("PHSYNC")
 
  print("Se Configuró CHA con una señal cuadrada: "+str(VPP_CHA)+" V, Frecuencia: "+str(FREC_CHA)+" Hz, OFFSET: "+str(OFFSET_CHA)+" V")
  print("Se Configuró CHB con una señal cuadrada: "+str(VPP_CHB)+" V, Frecuencia: "+str(FREC_CHB)+" Hz, OFFSET: "+str(OFFSET_CHB)+" V")
  time.sleep(5)
except:
  HP3245A.write("APPLY DCV 0.0")
  
