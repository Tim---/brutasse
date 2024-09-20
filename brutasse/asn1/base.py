#!/usr/bin/env python3

import enum
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self, TypeVar


class TagClass(enum.IntEnum):
    """An ASN.1 tag class."""

    UNIVERSAL = 0
    APPLICATION = 1
    CONTEXT = 2
    PRIVATE = 3


@dataclass(frozen=True)
class Identifier:
    class_: TagClass
    constructed: bool
    number: int


Tag = tuple[Identifier, bytes | list["Tag"]]


class BaseType:
    identifier: Identifier


class PrimitiveType(BaseType):
    pass


class ConstructedType(BaseType):
    pass


T = TypeVar("T", bound=BaseType)


def identifier(tag_class: TagClass, number: int) -> Callable[[type[T]], type[T]]:
    """Change the implicit tagging on an ASN.1 type."""

    def wrap(cls: type[T]) -> type[T]:
        constructed = issubclass(cls, ConstructedType)
        cls.identifier = Identifier(tag_class, constructed, number)
        return cls

    return wrap


@dataclass
@identifier(TagClass.UNIVERSAL, 16)
class Sequence(ConstructedType):
    """An ASN.1 SEQUENCE value."""


@identifier(TagClass.UNIVERSAL, 6)
class ObjectIdentifier(tuple[int, ...], PrimitiveType):
    """An ASN.1 OBJECT IDENTIFIER value."""

    @classmethod
    def from_string(cls, s: str) -> Self:
        return cls(list(map(int, s.split("."))))

    def __str__(self) -> str:
        return ".".join(map(str, self))

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"


@identifier(TagClass.UNIVERSAL, 2)
class Integer(int, PrimitiveType):
    """An ASN.1 INTEGER value."""

    def __repr__(self):
        return f"{self.__class__.__name__}({int(self)})"


@identifier(TagClass.UNIVERSAL, 4)
class OctetString(bytes, PrimitiveType):
    """An ASN.1 OCTET STRING value."""

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"


@identifier(TagClass.UNIVERSAL, 5)
class Null(PrimitiveType):
    """An ASN.1 NULL value."""

    def __repr__(self):
        return f"{self.__class__.__name__}()"
