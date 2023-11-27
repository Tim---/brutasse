#!/usr/bin/env python3

from dataclasses import dataclass
from .base import Sequence, OctetString, Integer


@dataclass
class UsmSecurityParameters(Sequence):
    msgAuthoritativeEngineID: OctetString
    msgAuthoritativeEngineBoots: Integer
    msgAuthoritativeEngineTime: Integer
    msgUserName: OctetString
    msgAuthenticationParameters: OctetString
    msgPrivacyParameters: OctetString
