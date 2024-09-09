#!/usr/bin/env python3

from brutasse.snmp.client_base import SnmpBase
from brutasse.snmp.packet import Version


class Snmpv1(SnmpBase):
    version = Version.V1
