
#########################################################################################
# Las pruebas para este script fueron hechos con el generador 3245A configurado: 
# CANAL A = SQR de 1V, f= 4 Hz ; OFFSET = 0.5V
# CANAL B = SQR de 5V, f= 4 Hz ; OFFSET = 2.5V
# El objetivo es apartir de un trigger externo obtener una medición
#########################################################################################
import numpy as np
import pyvisa
import time
import struct
import matplotlib.pyplot as plt
import datetime
import paho.mqtt.client as mqtt
import json
import threading


# Configuración de guardado 
fecha_hora = datetime.datetime.now()
nombre_archivo = fecha_hora.strftime("Medicion_%Y-%m-%d_%H-%M-%S.txt")

Ruta_Carga_G = "E:\\Data\\INTI\\Proyectos\\Escaner\\Escaner_v1\\datos\\Generador\\"
Ruta_Carga_C = "E:\\Data\\INTI\\Proyectos\\Escaner\\Escaner_v1\\datos\\Carga\\"
Ruta_Carga_D = "E:\\Data\\INTI\\Proyectos\\Escaner\\Escaner_v1\\datos\\Debug\\"

Ruta_Carga_G_Archivo = Ruta_Carga_G + nombre_archivo
Ruta_Carga_C_Archivo = Ruta_Carga_C + nombre_archivo
Ruta_Carga_D_Archivo = Ruta_Carga_D + nombre_archivo

# Constantes
Rp       = 9.999938e03      # Rp en ohmios (ejemplo)
V_de_Tau = 0.6321205588     # V_de_Tau para el cálculo

Lista_de_maximos=[]
Lista_de_minimos=[]

Paso_de_Secuencia = 0       # Para funcionamiento normal Paso_de_Secuencia=2 #Para debug

# Configura la comunicación del intrumento
rm = pyvisa.ResourceManager()
Keysight_3458A = rm.open_resource('GPIB0::22::INSTR') 
# Depende de cada dispositivo pero sin esto no comunica
Keysight_3458A.read_termination = '\n'  
Keysight_3458A.write_termination = '\n' 
Keysight_3458A.timeout  = 50000
print(Keysight_3458A)

#Chequea comunicación PC <-->DVM
print('Keysight_3458A.query(\'ID?\') --> ' + Keysight_3458A.query('ID?'))  
time.sleep(5)

#Resetea el instrumento
#Keysight_3458A.write('RESET')
print('Instrumento reseteado')
time.sleep(3)

# Valores para parametrización
Cant_Muestras           = 10000
Sweep_Time              = 20E-6 # para cap de 1 uF y R de 10 K
Aper_Time               = 3E-6
bytes_por_lectura       = 2
Muestras_Empaquetadas=np.zeros(Cant_Muestras,dtype=int)
 
 
######################################################################################
#CODIGO PARA CONEXION MQTT
######################################################################################




def obtener_datos_mqtt():
    mqtt_broker = "10.3.1.157"  # IP del servidor
    topichead = "PlutonTHB/live/"
    device_id = "THB1L1D9"
    mqtt_topic = topichead + device_id
    datos_recibidos = {}

    # Variable global para detener el loop después de recibir un mensaje
    message_received = False

    # Función que se ejecuta cuando no se recibe mensaje dentro del tiempo límite
    def timeout():
        nonlocal message_received
        if not message_received:  # Si no se recibieron datos en 20 segundos
            print("No se pudo conectar con el broker, se deben modificar los datos de temperatura, fecha y humedad manualmente.")
            datos_recibidos["timestamp"] = "aaa-mm-dd/hh:mm:ss"
            datos_recibidos["temp"] = 0.0
            datos_recibidos["hum"] = 0.0
            message_received = True  # Cambiar estado para detener el bucle
            client.disconnect()
             
    # Temporizador para esperar 20 segundos
    timer = threading.Timer(20.0, timeout)
    timer.start()

    def on_connect(client, userdata, flags, rc):
        print("Esperando los datos de temperatura y humedad: ")
        client.subscribe(mqtt_topic)  # Suscribirse al topic deseado

    def on_message(client, userdata, msg):
        nonlocal message_received  # Indicar que se usará la variable global
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)  # Cargar el contenido del mensaje como JSON
        print(f"Valores obtenidos desde {data['id']} -\n {data['timestamp']}\nTemperatura: {data['temp']}\nHumedad: {data['hum']}")
        # Almacenar los datos recibidos
        datos_recibidos["timestamp"] = data["timestamp"].replace(' ', '/')
        datos_recibidos["temp"] = data["temp"]
        datos_recibidos["hum"] = data["hum"]
        message_received = True  # Marcar que ya se recibió un mensaje
        client.disconnect()  # Desconectar el cliente después del primer mensaje

    # Crear un cliente MQTT
    client = mqtt.Client()
    client.username_pw_set(username="inti", password="inti")
    client.on_connect = on_connect
    client.on_message = on_message

    # Conectar al broker
    client.connect(mqtt_broker, 1883, 60)

    # Iniciar el loop para procesar mensajes
    client.loop_forever()

    # Detener el temporizador después de que se haya recibido el mensaje
    timer.cancel()

    # Devolver los datos recibidos
    return datos_recibidos


######################################################################################### 
#CODIGO PARA REALIZAR LA MEDICION   
################################################################################### 
 

while Paso_de_Secuencia < 3:
    
    if Paso_de_Secuencia==0:
        print("Conectar DVM a entrada de Generador.")
        Avance = input("Oprima Enter para continuar: ")
    if Paso_de_Secuencia==1:
        print("Conectar DVM a Cx.")
        Avance = input("Oprima Enter para continuar: ")
    
    #Configura el instrumento
    Keysight_3458A.write('TRIG HOLD')
    Keysight_3458A.write('TARM HOLD')
    Command ='AZERO OFF; PRESET FAST; MEM FIFO; MFORMAT SINT; OFORMAT SINT; TBUFF OFF; DELAY 0; TRIG HOLD; TARM HOLD; DISP OFF, SAMPLING;'
    Command = Command + 'APER '+str(Aper_Time)+';DCV 1; SWEEP '+str(Sweep_Time)+', '+str(Cant_Muestras)+'; TARM SYN; TRIG EXT; MATH OFF'
    Keysight_3458A.write(Command)  
    time.sleep(3)
   
    #Muestras_Empaquetadas=np.zeros(Cant_Muestras,dtype=int)
    Muestras_Empaquetadas  = Keysight_3458A.read_bytes(Cant_Muestras*bytes_por_lectura)
    #Desempaqueta la informacion del buffer y devuelve una tupla
    Muestras = struct.unpack('>'+'h'*Cant_Muestras, Muestras_Empaquetadas) 
    Muestras_Escaladas = np.asarray(Muestras)*float(Keysight_3458A.query('ISCALE?'))
    del Muestras_Empaquetadas

    Medicion_Realizada = Muestras_Escaladas
    Eje_de_Muestras = np.arange(len(Medicion_Realizada))
    
    Keysight_3458A.write('TRIG HOLD')
    Keysight_3458A.write('TARM HOLD')
    Keysight_3458A.write('TBUFF OFF') 

    def Determinacion_Valor_Maximo (Medicion):
 # Recorrer y castear
        for Muestra in Medicion:
            valor_cast = float(Muestra)  
            if   valor_cast > 0.980 and valor_cast < 1.020:  
                    Lista_de_maximos.append(valor_cast)
            elif valor_cast>-0.020 and valor_cast < 0.020:
                    Lista_de_minimos.append(valor_cast)   
    
        Vm = np.mean(Lista_de_maximos)-np.mean(Lista_de_minimos)
        Desvio_del_Maximo=np.std(Lista_de_maximos)
        print(f"El valor Vmaximo es: {round(np.mean(Lista_de_maximos),7)}V")
        print(f"El valor Vminimo es: {round(np.mean(Lista_de_minimos),7)}V")
        Desvio_del_Minimo=np.std(Lista_de_minimos)
        if Desvio_del_Maximo>=Desvio_del_Minimo:
            Desvio_Vm = Desvio_del_Maximo
        else:
            Desvio_Vm = Desvio_del_Minimo 
        return Vm,Desvio_Vm
    
    if Paso_de_Secuencia==0:
        V_max,Desvio_Vm= Determinacion_Valor_Maximo (Medicion_Realizada)
        print(f"El valor Vm es: {round(V_max,7)}V")

############################ Visualizador de gráficos ##################################    
    # Graficar los datos en función de las muestras
    plt.figure(figsize=(12, 6)) 
    plt.plot(Eje_de_Muestras,Medicion_Realizada, 'b.-'  )
    plt.xlabel('nro muestras')
    plt.ylabel('Tensión medida [V]')
    plt.title('Datos de Medición en Función de las Muestras')
    plt.grid(True)
    plt.show()    

    # Graficar los datos en función del tiempo
    plt.figure(figsize=(12, 6))  
    plt.plot(Eje_de_Muestras*Sweep_Time, Medicion_Realizada, 'bo',label='Datos Medidos'  )
    plt.xlabel('Tiempo [s]')
    plt.ylabel('Tensión medida [V]')
    plt.title('Datos de Medición en Función del tiempo')
    plt.legend()
    plt.grid(True)
    plt.show()    
#######################################################################################

######################### Crear y escribir el archivo de texto ########################
    if Paso_de_Secuencia==0:
        Ruta_Completa=Ruta_Carga_G_Archivo
    if Paso_de_Secuencia==1:
        Ruta_Completa=Ruta_Carga_C_Archivo
        Paso_de_Secuencia=3
    if Paso_de_Secuencia==2:
         Ruta_Completa=Ruta_Carga_D_Archivo
    with open(Ruta_Completa, "w") as file:
        datos = obtener_datos_mqtt()
            # Escribir los datos de fecha, temperatura y humedad en el archivo
        file.write("Fecha:\n")
        file.write(f"{datos['timestamp']}\n")
        file.write("Temp:\n")
        file.write(f"{datos['temp']}\n")
        file.write("Humedad:\n")
        file.write(f"{datos['hum']}\n")
        file.write("V maxima:\n")
        file.write(f"{round(np.mean(Lista_de_maximos),7)}\n")
        file.write("V minima:\n")
        file.write(f"{round(np.mean(Lista_de_minimos),7)}\n")
        file.write("sweep time:\n")
        file.write(f"{Sweep_Time}\n")
        file.write("Mediciones:\n") 
        
        
           
        for dato in Medicion_Realizada:
            file.write(f"{dato}\n")  
#######################################################################################
 
    Paso_de_Secuencia=Paso_de_Secuencia+1




