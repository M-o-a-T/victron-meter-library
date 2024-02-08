# VenusOS module for support of Eastron SDM120-Modbus
# might work also with other Eastron devices > Product code on 0x001c (type u16b) to be added into models overview
# 

import logging
import Eastron_device as device
import probe
from register import *

log = logging.getLogger()

class Reg_f32b(Reg_num):
    coding = ('>f', '>2H')
    count = 2
    rtype = float
		
nr_phases = [ 1, 1, 3, 3 ]

phase_configs = [
    '1P',
    '1P',
    '3P.1',
    '3P.n',
]

class Eastron_SDM120(device.EnergyMeter):
    productid = 0xB023 # id assigned by Victron Support
    productname = 'Eastron SDM120-Modbus'
    min_timeout = 0.5
    hardwareversion = '1'
    firmwareversion = '0'
    serial = '0'

    def __init__(self, *args):
        super().__init__(*args)

        self.info_regs = [
            Reg_u16( 0xfc02, '/HardwareVersion'),
            Reg_u16( 0xfc03, '/FirmwareVersion'),
            Reg_f32b(0x000a, '/PhaseConfig', text=phase_configs, write=(0, 3)),
            Reg_u32b(0xfc00, '/Serial'),
        ]

    def phase_regs(self, n):
        s = 0x0002 * (n - 1)
        return [
            Reg_f32b(0x0000 + s, '/Ac/L%d/Voltage' % n,        1, '%.1f V'),
            Reg_f32b(0x0006 + s, '/Ac/L%d/Current' % n,        1, '%.1f A'),
            Reg_f32b(0x000c + s, '/Ac/L%d/Power' % n,          1, '%.1f W'),
            Reg_f32b(0x0048 + s, '/Ac/L%d/Energy/Forward' % n, 1, '%.1f kWh'),
            Reg_f32b(0x004a + s, '/Ac/L%d/Energy/Reverse' % n, 1, '%.1f kWh'),
        ]

    def device_init(self):

        self.read_info()

        phases = nr_phases[int(self.info['/PhaseConfig'])]

        regs = [
            Reg_f32b(0x000c, '/Ac/Power',          1, '%.1f W'),
            Reg_f32b(0x0006, '/Ac/Current',        1, '%.1f A'),
            Reg_f32b(0x0046, '/Ac/Frequency',      1, '%.1f Hz'),
            Reg_f32b(0x0048, '/Ac/Energy/Forward', 1, '%.1f kWh'),
            Reg_f32b(0x004a, '/Ac/Energy/Reverse', 1, '%.1f kWh'),
        ]

        for n in range(1, phases + 1):
            regs += self.phase_regs(n)

        self.data_regs = regs

    def get_ident(self):
        return 'cg_%s' % self.info['/Serial']



# identifier to be checked, if register identical on all SDM120 (only first 16 bytes in u16b of 32 bit register 0xfc02)
models = {
    32: {
        'model':    'SDM120Modbus',
        'handler':  Eastron_SDM120,
    },
}

probe.add_handler(probe.ModelRegister(Reg_u16(0xfc02), models,
                                      methods=['tcp','rtu'],
                                      units=[1]))
