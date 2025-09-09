import pyvisa

class UT880EE:
    """
    Clase de control para multímetro UT880EE (UT8802/UT8803) vía pyVISA.
    Requiere que el instrumento se exponga como puerto COM o USBTMC.
    """

    def __init__(self, resource_name: str, baudrate: int = 9600, timeout: int = 2000):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(resource_name,
                                          baud_rate=baudrate,
                                          data_bits=7,
                                          parity=pyvisa.constants.Parity.none,
                                          stop_bits=pyvisa.constants.StopBits.one)
        self.inst.timeout = timeout

    # ---------------------------
    # Métodos básicos de comunicación
    # ---------------------------
    def write(self, command: str) -> None:
        """Escribe un comando en el buffer de salida."""
        self.inst.write(command)

    def query(self, command: str) -> str:
        """Envía un comando y retorna la respuesta como string."""
        return self.inst.query(command)

    def read(self) -> str:
        """Lee directamente del buffer de entrada."""
        return self.inst.read()

    def write_raw(self, data: bytes) -> None:
        """Escribe bytes crudos (para binario)."""
        self.inst.write_raw(data)

    def read_bytes(self, count: int) -> bytes:
        """Lee un número fijo de bytes crudos."""
        return self.inst.read_bytes(count)

    # ---------------------------
    # Métodos específicos del multímetro
    # ---------------------------
    def get_data(self) -> float:
        """Lee solo el valor numérico actual (comando data?)."""
        try:
            return float(self.query("data?;"))
        except Exception:
            return float("nan")

    def get_display(self) -> dict:
        """
        Lee la información de pantalla (disp?) y parsea Flags.
        Devuelve un diccionario con valor, unidad y estado.
        """
        raw = self.query("disp?;")
        parts = raw.split(",")
        if len(parts) < 5:
            return {"raw": raw}

        main_disp = parts[0].strip()
        aux_disp = parts[1].strip()
        try:
            main_val = float(parts[2])
        except:
            main_val = None
        try:
            aux_val = float(parts[3])
        except:
            aux_val = None
        try:
            flags = int(parts[4], 16)
        except:
            flags = 0

        parsed_flags = self._parse_flags(flags)

        return {
            "main_display": main_disp,
            "aux_display": aux_disp,
            "main_value": main_val,
            "aux_value": aux_val,
            "flags_raw": flags,
            **parsed_flags
        }

    def hold(self, enable: bool = True) -> None:
        """Activa o desactiva HOLD (si el modelo lo soporta)."""
        cmd = "hold on;" if enable else "hold off;"
        self.write(cmd)

    def rel(self, enable: bool = True) -> None:
        """Activa o desactiva la medición relativa (REL)."""
        cmd = "rel on;" if enable else "rel off;"
        self.write(cmd)

    def beep(self, enable: bool = True) -> None:
        """Activa o desactiva el beep (si el modelo lo soporta)."""
        cmd = "beep on;" if enable else "beep off;"
        self.write(cmd)

    def reset(self) -> None:
        """Resetea el instrumento a configuración por defecto."""
        self.write("*RST;")

    def identify(self) -> str:
        """Consulta la identificación del multímetro (si soporta *IDN?)."""
        try:
            return self.query("*IDN?")
        except Exception:
            return "UT880EE (no *IDN? support)"

    # ---------------------------
    # Parsing de Flags
    # ---------------------------
    def _parse_flags(self, flags: int) -> dict:
        """Decodifica los bits de Flags según manual UT8802/8803."""
        unit_types = {
            0: "V", 1: "A", 2: "Ω", 3: "Hz", 4: "°C", 5: "°F",
            6: "rpm", 7: "F", 8: "β", 9: "%", 0xF: ""
        }
        scales = {0: "n", 1: "μ", 2: "m", 3: "", 4: "k", 5: "M", 6: "G"}
        acdc_status = {0: "OFF", 1: "AC", 2: "DC", 3: "AC+DC"}

        acdc = (flags >> 4) & 0x3
        unit_type = (flags >> 8) & 0xF
        unit_scale = (flags >> 12) & 0x7
        overload = (flags >> 7) & 0x1
        autorange = (flags >> 6) & 0x1
        battery_low = (flags >> 15) & 0x1
        hold = (flags >> 31) & 0x1
        rel = (flags >> 30) & 0x1
        min_flag = (flags >> 29) & 0x1
        max_flag = (flags >> 28) & 0x1

        unit = f"{scales.get(unit_scale,'')}{unit_types.get(unit_type,'')}"

        return {
            "unit": unit,
            "acdc": acdc_status.get(acdc, "?"),
            "overload": bool(overload),
            "autorange": bool(autorange),
            "battery_low": bool(battery_low),
            "hold": bool(hold),
            "rel": bool(rel),
            "min": bool(min_flag),
            "max": bool(max_flag)
        }

"""
dmm = UT880EE("ASRL3::INSTR")  # si está en COM3
print("Valor:", dmm.get_data())
print("Pantalla:", dmm.get_display())
dmm.close()
"""
"""
dmm = UT880EE("ASRL3::INSTR")  # si está en COM3

print("ID:", dmm.identify())
print("Valor:", dmm.get_data())
print("Pantalla:", dmm.get_display())

dmm.hold(True)    # activa HOLD
dmm.rel(False)    # desactiva REL
dmm.beep(True)    # habilita beep
dmm.reset()       # reset

dmm.close()
"""