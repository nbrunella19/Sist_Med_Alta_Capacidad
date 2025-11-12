import pyvisa

class Keithley2110:
    """
    Clase para controlar el multímetro Keithley 2110 mediante PyVISA por USB.
    """

    def __init__(self, resource_name=None):
        """
        Inicializa la conexión VISA.
        Si no se proporciona 'resource_name', lista los recursos disponibles.
        """
        self.rm = pyvisa.ResourceManager()
        if resource_name is None:
            print("Instrumentos detectados:")
            for res in self.rm.list_resources():
                print(f" - {res}")
            raise ValueError("Debe especificar el resource_name del Keithley 2110.")
        self.inst = self.rm.open_resource(resource_name)
        self.inst.timeout = 5000  # ms
        self.inst.write_termination = '\n'
        self.inst.read_termination = '\n'

    def idn(self):
        """Devuelve la identificación del instrumento."""
        return self.inst.query("*IDN?")

    def reset(self):
        """Reinicia el instrumento a su configuración de encendido."""
        self.inst.write("*RST")
        self.inst.write("*CLS")  # Limpia errores previos
        print("Instrumento reseteado.")

    def medir_tension_dc(self, rango="DEF", resolucion="DEF"):
        """
        Realiza una medición de tensión DC (voltaje DC).
        Parámetros opcionales:
        - rango: en volts o 'MIN'/'MAX'/'DEF'
        - resolucion: en volts o 'MIN'/'MAX'/'DEF'
        """
        cmd = f"MEAS:VOLT:DC? {rango},{resolucion}"
        valor = float(self.inst.query(cmd))
        return valor

    def configurar_autorango(self, estado=True):
        """Activa o desactiva el autorango de tensión DC."""
        estado_str = "ON" if estado else "OFF"
        self.inst.write(f"VOLT:DC:RANG:AUTO {estado_str}")

    def leer_ultimo(self):
        """Devuelve el último valor medido sin realizar una nueva medición."""
        return float(self.inst.query("FETCh?"))

    def close(self):
        """Cierra la conexión con el instrumento."""
        self.inst.close()
        self.rm.close()

# Ejemplo de uso:
# multimetro = Keithley2110("USB0::0x05E6::0x2110::1234567::INSTR")
# print(multimetro.idn())
# multimetro.reset()
# multimetro.configurar_autorango(True)
# print(multimetro.medir_tension_dc())
# multimetro.close()
