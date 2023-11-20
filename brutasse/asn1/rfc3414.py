#!/usr/bin/env python3

from dataclasses import dataclass
from . import univ


@dataclass
class UsmSecurityParameters(univ.Sequence):
    msgAuthoritativeEngineID: univ.OctetString
    msgAuthoritativeEngineBoots: univ.Integer
    msgAuthoritativeEngineTime: univ.Integer
    msgUserName: univ.OctetString
    msgAuthenticationParameters: univ.OctetString
    msgPrivacyParameters: univ.OctetString
