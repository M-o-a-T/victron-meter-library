# VenusOS module for support of Carlo Gavazzi EM24 PFB- and X-Models with Modbus-RTU-support
# - Meter has be be connected by a ModbusTCP gateway and cannot be connected directly by serial interface to VenusGX
# - Library might work also with PFA devices, but generate an error for application setting.
# 
# Community contribution by Thomas Weichenberger
# Version 1.0 - 2022-01-02
#
# Thanks to Victron for their open platform and especially for the support of Matthijs Vader
# For any usage a donation to seashepherd.org with an amount of 5 USD/EUR/GBP or equivalent is expected

import logging
import EM24RTU_device as device
import probe
from register import *

log = logging.getLogger()

nr_phases = [ 3, 3, 2, 1, 3 ]

phase_configs = [
    '3P.n',
    '3P.1',
    '2P',
    '1P',
    '3P',
]

hardware_version = [
    'EM24DINAV93XO2PFA',
    'unknown',
    'EM24DINAV93XISPFA',
    'EM24DINAV93XXXPFA',
    'EM24DINAV23XO2PFA',
    'EM24DINAV23XISPFA',
    'EM24DINAV23XXXPFA',
    'EM24DINAV53xO2PFA',
    'unknown',
    'EM24DINAV53xISPFA',
    'EM24DINAV53xXXPFA',
    'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown',
    'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown',
    'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown',
    'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown',
    'unknown', 'unknown', 'unknown', 'EM24DINAV93XISX', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'EM24DINAV53DISX', 'unknown', 'unknown',
    'EM24DINAV63xO2X',
    'EM24DINAV63xR2X',
    'EM24DINAV63xISX',
    'EM24DINAV63xXXX',
]

switch_positions = [
    'kVARh',
    '2',
    '1',
    'Locked',
]

class EM24RTU_Meter(device.EnergyMeter):
    productid = 0xb017
    productname = 'Carlo Gavazzi EM24RTU Energy Meter'
    min_timeout = 0.5

    def __init__(self, *args):
        super(EM24RTU_Meter, self).__init__(*args)

        self.info_regs = [
            Reg_u16( 0x0302, '/HardwareVersion', text=hardware_version, write=(0, 78)),
            Reg_u16( 0x0303, '/FirmwareVersion'),
            Reg_u16( 0x1102, '/PhaseConfig', text=phase_configs, write=(0, 4)),
            Reg_text(0x1300, 7, '/Serial'),
        ]

    def phase_regs(self, n):
        s = 2 * (n - 1)
        return [
            Reg_s32l(0x0000 + s, '/Ac/L%d/Voltage' % n,        10, '%.1f V'),
            Reg_s32l(0x000c + s, '/Ac/L%d/Current' % n,      1000, '%.1f A'),
            Reg_s32l(0x0012 + s, '/Ac/L%d/Power' % n,          10, '%.1f W'),
            Reg_s32l(0x0046 + s, '/Ac/L%d/Energy/Forward' % n, 10, '%.1f kWh'),
        ]

    def device_init(self):
        # make sure application is set to H
        appreg = Reg_u16(0x1101)
        if self.read_register(appreg) != 7:
            self.write_register(appreg, 7)

            # read back the value in case the setting is not accepted
            # for some reason
            if self.read_register(appreg) != 7:
                log.error('%s: failed to set application to H', self)
                return

        self.read_info()

        phases = nr_phases[int(self.info['/PhaseConfig'])]

        regs = [
            Reg_s32l(0x0028, '/Ac/Power',          10, '%.1f W'),
            Reg_u16(0x0037, '/Ac/Frequency',      10, '%.1f Hz'),
            Reg_s32l(0x003e, '/Ac/Energy/Forward', 10, '%.1f kWh'),
            Reg_s32l(0x005c, '/Ac/Energy/Reverse', 10, '%.1f kWh'),
        ]

        if phases == 3:
            regs += [
                Reg_mapu16(0x0036, '/PhaseSequence', { 0: 0, 0xffff: 1 }),
            ]

        for n in range(1, phases + 1):
            regs += self.phase_regs(n)

        self.data_regs = regs

    def dbus_write_register(self, reg, path, val):
        super(EM24RTU_Meter, self).dbus_write_register(reg, path, val)
        self.sched_reinit()

    def get_ident(self):
        return 'cg_%s' % self.info['/Serial']

models = {
    70: {
        'model':    'EM24-DIN AV9',
        'handler':  EM24RTU_Meter,
    },
    71: {
        'model':    'EM24-DIN AV2',
        'handler':  EM24RTU_Meter,
    },
    72: {
        'model':    'EM24-DIN AV5',
        'handler':  EM24RTU_Meter,
    },
    73: {
        'model':    'EM24-DIN AV6',
        'handler':  EM24RTU_Meter,
    },
}

probe.add_handler(probe.ModelRegister(Reg_u16(0x000b), models,
                                      methods=['tcp','rtu'],
                                      units=[1]))
