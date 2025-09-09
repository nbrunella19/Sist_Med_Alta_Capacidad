import pyvisa

class HP34420A:
    def __init__(self, gpib_address: str = "GPIB0::10::INSTR"):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(gpib_address)
        self.instrument.timeout = 5000
        self.reset()

    def reset(self):
        self.instrument.write("*RST")
        self.instrument.write("*CLS")

    def identify(self) -> str:
        return self.instrument.query("*IDN?")

    def configure_voltage_dc(self, range_val=0.01, resolution=1e-7):
        self.instrument.write("CONF:VOLT:DC")
        self.instrument.write(f"VOLT:DC:RANG {range_val}")
        self.instrument.write(f"VOLT:DC:RES {resolution}")

    def read(self):
        return float(self.instrument.query("READ?"))

    def close(self):
        self.instrument.close()
        self.rm.close()