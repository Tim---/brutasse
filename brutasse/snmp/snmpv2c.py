#!/usr/bin/env python3

from brutasse.asn1.snmp import Version
from brutasse.snmp.client_base import SnmpBase


class Snmpv2c(SnmpBase):
    version = Version.V2C
