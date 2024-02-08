from copy import copy
import dbus
from functools import partial
from pymodbus.client import *
from pymodbus.register_read_message import ReadHoldingRegistersResponse, ReadInputRegistersResponse
import logging
import os
import time
import traceback
import device

from settingsdevice import SettingsDevice
from vedbus import VeDbusService

import __main__
from register import Reg
from utils import *

log = logging.getLogger()

class ModbusDevice(device.ModbusDevice):
    min_timeout = 0.1

    def read_data_regs(self, regs, d):
        now = time.time()

        if all(now - r.time < r.max_age for r in regs):
            return

        start = regs[0].base
        count = regs[-1].base + regs[-1].count - start

        rr = self.modbus.read_input_registers(start, count, unit=self.unit)

        latency = time.time() - now

        if rr.isError():
            log.error('Error reading registers %#04x-%#04x: %s',
                      start, start + count - 1, rr)
            raise Exception(rr)

        for reg in regs:
            base = reg.base - start
            end = base + reg.count

            if now - reg.time > reg.max_age:
                if reg.decode(rr.registers[base:end]):
                    d[reg.name] = copy(reg) if reg.isvalid() else None
                reg.time = now

        return latency


class CustomName(device.CustomName):
    pass


class EnergyMeter(ModbusDevice):
    allowed_roles = ['grid', 'pvinverter', 'genset', 'acload']
    default_role = 'grid'
    default_instance = 40
    nr_phases = None

    def position_setting_changed(self, service, path, value):
        self.dbus['/Position'] = value['Value']

    def init_device_settings(self, dbus):
        super().init_device_settings(dbus)

        self.pos_item = None
        if self.role == 'pvinverter':
            self.pos_item = self.settings.addSetting(
                self.settings_path + '/Position', 0, 0, 2,
                callback=self.position_setting_changed)

    def device_init_late(self):
        super().device_init_late()

        if self.pos_item is not None:
            self.dbus.add_path('/Position', self.pos_item.get_value(),
                               writeable=True,
                               onchangecallback=self.position_changed)

    def position_changed(self, path, val):
        if not 0 <= val <= 2:
            return False
        self.pos_item.set_value(val)
        return True

__all__ = [
    'EnergyMeter',
    'ModbusDevice',
]
