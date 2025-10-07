
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
            self.instrument.timeout = 50000
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

    def configure_measurement(self, mode="DCV", range_val=10, resolution=0.00001, nplc=10):
        mode = mode.upper()
        if mode == "DCV":      
            self.instrument.write(f"DCV {range_val},{resolution}")
        elif mode == "ACV":
            self.instrument.write(f"ACV {range_val},{resolution}")
        else:
            raise ValueError(f"Modo de medición '{mode}' no soportado.")

        self.instrument.write(f"NPLC {nplc}")
        if self.verbose:
            print(f"[INFO] Medición configurada: {mode}, rango {range_val}, resolución {resolution}, NPLC {nplc}")

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

    def measure_sweep_binary(self, cant_muestras, sweep_time, aper_time) -> np.ndarray:
        """
        Entrada: La clase, Cantidad de muestras, Separación entre muestras, Tiempo de apertura.
        Esta función configura el HP3458A para realizar una medición en modo sweep
        y devuelve un array de numpy con las muestras obtenidas.
        Salida: Vector con las muestras medidas.
        """
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

        # Devolver las muestras escaladas
        return np.asarray(muestras) * escala

    def measure_and_plot_sweep(self, cant_muestras, sweep_time, aper_time):
        """
        Entrada: La clase, Cantidad de muestras, Separación entre muestras, Tiempo de apertura.
        Salida: Vector con las muestras medidas y gráfico de las mismas.
        """
        print("[INFO] Iniciando medición ...")

        # Realizar la medición
        datos = self.measure_sweep_binary(cant_muestras, sweep_time, aper_time)
        # Crear vector de tiempo
        tiempo = np.arange(cant_muestras) * sweep_time
        
        # Gráfico de los datos
        plt.figure(figsize=(10, 5))
        plt.plot(tiempo, datos)
        plt.title("Medición Sweep Binary del HP3458A")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("Voltaje (V)")
        plt.grid(True)
        plt.show()

        return datos

    def configurar_y_medir_sweep(self,Cant_Muestras, Sweep_time, Aper_Time):
        """
        Entrada: La clase, Cantidad de muestras, Separación entre muestras, Tiempo de apertura.
        Salida: Vector con las muestras medidas.
        """
        # Siempre empezar con un reset
        self.reset()
        print("Identificación:", self.identify())
        
        # Configurar el multímetro para medir DCV con un rango de 10V y resolución de 0.00001V
        self.configure_measurement(mode="DCV", range_val=10, resolution=0.00001)
        
        # Realizar la medición, graficar y obtener los datos
        datos = self.measure_and_plot_sweep(Cant_Muestras, Sweep_time, Aper_Time)
        
        # Finalizar con un reset
        self.reset()

        #Array de tuplas (tiempo, dato)
        return datos
