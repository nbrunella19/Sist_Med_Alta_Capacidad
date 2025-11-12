
import pyvisa
import time
import numpy as np
import struct
import matplotlib.pyplot as plt

class HP3458A:
    def __init__(self, gpib_address: str = "GPIB0::22::INSTR", do_reset=True, verbose=True):
        self.gpib_address = gpib_address
        self.verbose = verbose
        self.rm = pyvisa.ResourceManager()
        try:
            self.instrument = self.rm.open_resource(self.gpib_address)
            self.instrument.timeout = 30000
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            if self.verbose:
                print(f"[INFO] Conectado a {self.gpib_address}")
            if do_reset:
                self.reset()
        except pyvisa.VisaIOError as e:
            raise ConnectionError(f"[ERROR] No se pudo abrir el recurso {self.gpib_address}: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if hasattr(self, 'instrument'):
            self.instrument.close()
        if hasattr(self, 'rm'):
            self.rm.close()
        if self.verbose:
            print("[INFO] Conexión cerrada correctamente.")

    def reset(self):
        self.instrument.write("*RST")
        self.instrument.write("*CLS")
        time.sleep(1)
        if self.verbose:
            print("[INFO] Multímetro reseteado.")

    def identify(self) -> str:
        try:
            return self.instrument.query("ID?").strip()
        except pyvisa.errors.VisaIOError:
            return "ID desconocido (no se pudo obtener respuesta)"
    
    
    def measure_once(self) -> float:
        self.instrument.write("INIT")
        self.instrument.write("*WAI")
        return float(self.instrument.query("FETCH?"))

    def measure_and_print(self, delay=1.0, max_samples=None):
        count = 0
        try:
            while max_samples is None or count < max_samples:
                valor = self.measure_once()
                print(f"Medición {count+1}: {valor}")
                count += 1
                time.sleep(delay)
        except KeyboardInterrupt:
            print("\n[INFO] Medición interrumpida por el usuario.")

    def read_buffer(self, count=10) -> list:
        self.instrument.write("MFORMAT ASCII")
        self.instrument.write(f"MEM {count}")
        self.instrument.write("TARM SGL,1")
        self.instrument.write("TRIG")
        time.sleep(0.5)
        data = self.instrument.query("RMEM?")
        return [float(val) for val in data.strip().split(",") if val]
        
#####################################################################################################################

    def configure_measurement(self, cant_muestras, sweep_time,  aper_time):
        """
        Configura el multímetro HP3458A para mediciones de voltaje DC en modo barrido (sweep).
        Usa tiempo de apertura, tiempo entre muestras y cantidad de muestras.
        """
        mode ="DCV"
        self.instrument.clear()
        time.sleep(0.2)
        
        if mode == "DCV":
            # Comandos originales del HP3458A
            self.instrument.write("PRESET FAST")
            self.instrument.write("DCV 10,0.00001")  # rango 10 V, resolución 10 µV
            self.instrument.write("AZERO OFF")       # sin autozero para velocidad
            self.instrument.write(f"APER {aper_time}")  # tiempo de apertura
            self.instrument.write(f"SWEEP {sweep_time},{cant_muestras}")  # barrido
            self.instrument.write("MEM FIFO")
            self.instrument.write("MFORMAT SINT")
            self.instrument.write("OFORMAT SINT")
            self.instrument.write("TBUFF OFF")
            self.instrument.write("TRIG HOLD")
            self.instrument.write("TARM HOLD")
            self.instrument.write("DISP OFF, SAMPLING")
            self.instrument.write("MATH OFF")
        else:
            raise ValueError(f"Modo de medición '{mode}' no soportado.")

        if self.verbose:
            print(f"[INFO] Configuración completa: APER={aper_time}s, SWEEP={sweep_time}s, N={cant_muestras}")
    
#####################################################################################################################
    
    def configurar_y_medir_tension(self, Cant_Muestras, Sweep_time, Aper_Time):
        """
        Configura el HP3458A con las variables del usuario y realiza el sweep.
        """
        self.reset()
        print("Identificación:", self.identify())

        # Configurar medición basada en tiempos
        #self.configure_measurement(Cant_Muestras, Sweep_time, Aper_Time)
        print("[INFO] Iniciando medición ...")
        
        # Gráfico de los datos
        datos = self.Medir_y_Graficar(Cant_Muestras, Sweep_time, Aper_Time)
        
        return datos
    
 #####################################################################################################################
        """
    def Medicion_de_Tension(self, cant_muestras, sweep_time, aper_time) -> np.ndarray:
        
        Entrada: La clase, Cantidad de muestras, Separación entre muestras, Tiempo de apertura.
        Esta función configura el HP3458A para realizar una medición en modo sweep
        y devuelve un array de numpy con las muestras obtenidas.
        Salida: Vector con las muestras medidas.
        
        
        # Configuración el tiempo de espera máximo.
        self.instrument.timeout = 30000

        # Configuración del multímetro para medición en modo sweep
        self.instrument.write('TRIG HOLD')
        self.instrument.write('TARM HOLD')
         #Se crea un comando con todas las configuraciones necesarias.
        cmd = (
            f"AZERO OFF; PRESET FAST; MEM FIFO; MFORMAT SINT; OFORMAT SINT; TBUFF OFF; DELAY 0; "
            f"TRIG HOLD; TARM HOLD; DISP OFF, SAMPLING; "
            f"APER {aper_time}; DCV 1; SWEEP {sweep_time}, {cant_muestras}; "
            f"TARM SYN; TRIG EXT; MATH OFF"
        )
        self.instrument.write(cmd)

        # Inicia la medición
        self.instrument.write("TARM")
        time.sleep(0.2)
        self.instrument.write("MEM:START?")
        raw_data = self.instrument.read_bytes(cant_muestras * 2)

        # Procesamiento y formateo de los datos binarios recibidos
        muestras = struct.unpack(">" + "h" * cant_muestras, raw_data)

        # Obtener el factor de escala
        escala = float(self.instrument.query("ISCALE?"))

        mediciones = np.asarray(muestras) * escala
        
        # Devolver las muestras escaladas
        return mediciones

        
        """
#####################################################################################################################    
    
    def Medir_y_Graficar(self, cant_muestras, sweep_time, aper_time):
            """
            Entrada: La clase, Cantidad de muestras, Separación entre muestras, Tiempo de apertura.
            Salida: Vector con las muestras medidas y gráfico de las mismas.
            """
            print("[INFO] Iniciando medición ...")

            # Realizar la medición
            datos = self.Medicion_de_Tension(cant_muestras, sweep_time, aper_time)
            
            self.Graficar_datos(datos, sweep_time)

            return datos

#####################################################################################################################   
    
    def Medicion_de_Tension(self, cant_muestras, sweep_time, aper_time) -> np.ndarray:
        """
        Configura y ejecuta una medición de voltaje DC en modo barrido (sweep)
        en el multímetro HP3458A, y devuelve los datos como un array de NumPy.
        """

        # Tiempo máximo de espera (ajustar si es necesario)
        self.instrument.timeout = 30000

        # Limpiar y preparar el instrumento
        self.instrument.clear()
        time.sleep(0.2)

        # Configuración del modo DCV y parámetros de medición
        self.instrument.write("PRESET FAST")
        self.instrument.write("DCV 10,0.00001")   # Rango 10 V, resolución 10 µV
        self.instrument.write("AZERO OFF")        # Sin autozero para mayor velocidad
        self.instrument.write(f"APER {aper_time}") # Tiempo de apertura
        self.instrument.write(f"SWEEP {sweep_time},{cant_muestras}") # Sweep
        self.instrument.write("MEM FIFO")
        self.instrument.write("MFORMAT SINT")
        self.instrument.write("OFORMAT SINT")
        self.instrument.write("TBUFF OFF")
        self.instrument.write("TRIG HOLD")
        self.instrument.write("TARM HOLD")
        self.instrument.write("DISP OFF, SAMPLING")
        self.instrument.write("MATH OFF")

        if self.verbose:
            print(f"[INFO] Configuración completa: APER={aper_time}s, SWEEP={sweep_time}s, N={cant_muestras}")

        # Inicia la medición
        self.instrument.write("TARM SYN")
        self.instrument.write("TRIG EXT")
        self.instrument.write("TARM")  # Dispara la adquisición
        time.sleep(0.2)

        # Lectura de datos binarios
        self.instrument.write("MEM:START?")
        raw_data = self.instrument.read_bytes(cant_muestras * 2)

        # Decodificar datos binarios (signed 16-bit integers)
        muestras = struct.unpack(">" + "h" * cant_muestras, raw_data)

        # Obtener factor de escala y aplicar
        escala = float(self.instrument.query("ISCALE?"))
        mediciones = np.asarray(muestras) * escala

        return mediciones
#####################################################################################################################
  
    
    def Graficar_datos(self,datos, sweep_time):
        """
        Grafica los datos medidos en función del tiempo.
        """
        cant_muestras = len(datos)
        tiempo = np.arange(cant_muestras) * sweep_time
        
        plt.figure(figsize=(10, 5))
        plt.plot(tiempo, datos)
        plt.title("Medición Sweep Binary del HP3458A")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("Tensión (V)")
        plt.grid(True)
        plt.show()

 #####################################################################################################################