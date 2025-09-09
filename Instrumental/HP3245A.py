
import pyvisa
import time

class HP3245A:
    def __init__(self, resource_name, verbose=True):
        self.resource_name = resource_name
        self.verbose = verbose
        self.rm = pyvisa.ResourceManager()
        self.instrument = None

    def __enter__(self):
        try:
            self.instrument = self.rm.open_resource(self.resource_name)
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            if self.verbose:
                idn = self.instrument.query("ID?")
                print(f"[INFO] Conectado exitosamente a: {idn}")
            return self
        except Exception as e:
            print(f"[ERROR] No se pudo abrir el recurso {self.resource_name}: {e}")
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.instrument:
                self.instrument.close()
                if self.verbose:
                    print("[INFO] Conexión cerrada correctamente.")
        except Exception as e:
            print(f"[ERROR] Al cerrar el instrumento: {e}")

    def configurar_generador_full(self, Frec, Sweep_Time):

        if self.verbose:
                print(f"[INFO] Frecuencia recomendada: {Frec} Hz")
                print(f"[INFO] Sweep time recomendado: {Sweep_Time} µs")

        vpp_cha, offset_cha = 1, 0.5
        vpp_chb, offset_chb = 5, 2.5

        self.instrument.write("RESET")
        self.instrument.write("CLR")
        self.instrument.write("SCRATCH")
        self.instrument.write("BEEP OFF")

        self.instrument.write("USE CHANA")
        self.instrument.write(f"FREQ {Frec}")
        self.instrument.write(f"DCOFF {offset_cha}")
        self.instrument.write(f"APPLY SQV {vpp_cha}")

        self.instrument.write("USE CHANB")
        self.instrument.write(f"FREQ {Frec}")
        self.instrument.write(f"DCOFF {offset_chb}")
        self.instrument.write(f"APPLY SQV {vpp_chb}")

        self.instrument.write("PHSYNC")

        print(f"[INFO] CHA configurado: {vpp_cha} Vpp, {Frec} Hz, Offset {offset_cha} V")
        print(f"[INFO] CHB configurado: {vpp_chb} Vpp, {Frec} Hz, Offset {offset_chb} V")
