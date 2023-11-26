#!/usr/bin/env python3

from typing import overload, TypeVar
from types import UnionType, GenericAlias
from ..univ import Asn1Type
from .framing import build_ber_tags, parse_ber_tags
from .encoding import build, parse, T, U


Q = TypeVar('Q', bound=Asn1Type)
@overload
def ber_parse(raw: bytes, cls: type[Q]) -> Q: ...


def ber_parse(raw: bytes, cls: UnionType | GenericAlias | type[T]) -> T:
    tag, = parse_ber_tags(raw)
    return parse(tag, cls)


def ber_build(obj: U) -> bytes:
    tag = build(obj)
    return build_ber_tags([tag])
