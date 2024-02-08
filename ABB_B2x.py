# VenusOS module for support of ABB B21, B23 and B24 meters
# 
# Community contribution by Thomas Weichenberger
# Version 1.0 - 2022-01-06
# 
# Thanks to Victron for their open platform and especially for the support of Matthijs Vader
# For any usage a donation to seashepherd.org with an amount of 5 USD/EUR/GBP or equivalent is expected

import logging
import device
import probe
from register import *

log = logging.getLogger()

class Reg_u64b(Reg_num):
    coding = ('>Q', '>4H')
    count = 4
    rtype = float

nr_phases = [ 1, 3, 3 ]

phase_configs = [
    '1P',
    '3P.n',
    '3P',
]

class ABB_B2x_Meter(device.EnergyMeter):
    productid = 0xb017
    productname = 'ABB B2x-Series Power Meter'
    min_timeout = 0.5

    def __init__(self, *args):
        super(ABB_B2x_Meter, self).__init__(*args)

        self.info_regs = [
            Reg_text(0x8960, 6, '/HardwareVersion'),
            Reg_text(0x8908, 8, '/FirmwareVersion'),
            Reg_u32b(0x8900, '/Serial'),
        ]

    def phase_regs(self, n):
        s2 = 0x0002 * (n - 1)
        s4 = 0x0004 * (n - 1)

        return [
            Reg_u32b(0x5b00 + s2, '/Ac/L%d/Voltage' % n,         10, '%.1f V'),
            Reg_u32b(0x5b0c + s2, '/Ac/L%d/Current' % n,        100, '%.1f A'),
            Reg_s32b(0x5b16 + s2, '/Ac/L%d/Power' % n,          100, '%.1f W'),
            Reg_u64b(0x5460 + s4, '/Ac/L%d/Energy/Forward' % n, 100, '%.1f kWh'),
            Reg_u64b(0x546c + s4, '/Ac/L%d/Energy/Reverse' % n, 100, '%.1f kWh'),
        ]

    def device_init(self):
        self.read_info()

        phases = 3
		#phases = nr_phases[int(self.info['/PhaseConfig'])]

        regs = [
            Reg_s32b(0x5b14, '/Ac/Power',          100, '%.1f W'),
            Reg_u16(0x5b2c, '/Ac/Frequency',       100, '%.1f Hz'),
            Reg_u64b(0x5000, '/Ac/Energy/Forward', 100, '%.1f kWh'),
            Reg_u64b(0x5004, '/Ac/Energy/Reverse', 100, '%.1f kWh'),
        ]


        for n in range(1, phases + 1):
            regs += self.phase_regs(n)

        self.data_regs = regs

    def get_ident(self):
        return 'cg_%s' % self.info['/Serial']


models = {
    16946: {
        'model':    'ABB_B2x',
        'handler':  ABB_B2x_Meter,
    },
}


probe.add_handler(probe.ModelRegister(Reg_u16(0x8960), models,
                                      methods=['tcp','rtu'],
                                      units=[1]))
