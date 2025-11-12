import pyvisa

class TektronixAFG1022:
    """
    Controlador para el generador de funciones Tektronix AFG1022 mediante PyVISA por USB.
    Permite configurar ambos canales, frecuencia, amplitud, forma de onda y sincronización.
    """

    def __init__(self, resource_name=None):
        self.rm = pyvisa.ResourceManager()
        if resource_name is None:
            print("Instrumentos detectados:")
            for res in self.rm.list_resources():
                print(f" - {res}")
            raise ValueError("Debe especificar el resource_name del Tektronix AFG1022.")
        self.inst = self.rm.open_resource(resource_name)
        self.inst.write_termination = '\n'
        self.inst.read_termination = '\n'
        self.inst.timeout = 5000

    def idn(self):
        """Devuelve la identificación del instrumento."""
        return self.inst.query("*IDN?")

    def reset(self):
        """Resetea el generador a valores por defecto."""
        self.inst.write("*RST")
        self.inst.write("*CLS")
        print("Instrumento reseteado.")

    def configurar_canal(self, canal=1, forma='SIN', frecuencia=1000, amplitud=1.0, offset=0.0):
        """
        Configura los parámetros básicos del canal indicado.
        canal: 1 o 2
        forma: SIN, SQU, RAMP, PULS, NOIS, DC, USER
        frecuencia: en Hz
        amplitud: en Vpp
        offset: en V
        """
        if canal not in [1, 2]:
            raise ValueError("El canal debe ser 1 o 2.")
        self.inst.write(f"SOUR{canal}:FUNC {forma}")
        self.inst.write(f"SOUR{canal}:FREQ {frecuencia}")
        self.inst.write(f"SOUR{canal}:VOLT {amplitud}")
        self.inst.write(f"SOUR{canal}:VOLT:OFFS {offset}")

    def activar_salida(self, canal=1, estado=True):
        """Activa o desactiva la salida de un canal."""
        estado_str = "ON" if estado else "OFF"
        self.inst.write(f"OUTP{canal} {estado_str}")

    def sincronizar_canales(self):
        """
        Sincroniza los canales para que empiecen al mismo tiempo,
        sin acoplar frecuencia ni amplitud.

        Este comando alinea las fases internas de los dos canales,
        pero permite que cada uno mantenga su propia configuración.
        """
        # Alinea los generadores internos (ajusta sus relojes de fase)
        self.inst.write("SOUR:PHAS:ALIGN")


    def modo_independiente(self):
        """Desbloquea los canales para configurarlos de manera independiente."""
        self.inst.write("SOUR:COUP:FREQ OFF")
        self.inst.write("SOUR:COUP:AMPL OFF")
        self.inst.write("SOUR:COUP:PHAS 0")

    def close(self):
        """Cierra la conexión con el instrumento."""
        self.inst.close()
        self.rm.close()

# Ejemplo de uso:
# afg = TektronixAFG1022("USB0::0x0699::0x0346::C000000::INSTR")
# print(afg.idn())
# afg.reset()
# afg.configurar_canal(1, forma="SQU", frecuencia=1, amplitud=2.0)
# afg.configurar_canal(2, forma="SQU", frecuencia=1, amplitud=2.0)
# afg.sincronizar_canales()
# afg.activar_salida(1, True)
# afg.activar_salida(2, True)
# afg.close()