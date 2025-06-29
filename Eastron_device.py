from copy import copy
import dbus
from functools import partial
from pymodbus.client import *
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
    default_access="input"

class EnergyMeter(device.EnergyMeter):
    default_access="input"

__all__ = [
    'EnergyMeter',
    'ModbusDevice',
]
