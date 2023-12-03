#!/usr/bin/env python3

from ..asn1.snmp import Version
from .client_base import SnmpBase


class Snmpv1(SnmpBase):
    version = Version.V1
