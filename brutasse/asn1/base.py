#!/usr/bin/env python3

from typing import Self, TypeVar
from dataclasses import dataclass
import enum


class TagClass(enum.IntEnum):
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


def identifier(tag_class: TagClass, number: int):
    def wrap(cls: type[T]) -> type[T]:
        constructed = issubclass(cls, ConstructedType)
        cls.identifier = Identifier(tag_class, constructed, number)
        return cls

    return wrap


@dataclass
@identifier(TagClass.UNIVERSAL, 16)
class Sequence(ConstructedType):
    pass


@identifier(TagClass.UNIVERSAL, 6)
class ObjectIdentifier(tuple[int, ...], PrimitiveType):
    @classmethod
    def from_string(cls, s: str) -> Self:
        return cls(list(map(int, s.split("."))))

    def __str__(self) -> str:
        return ".".join(map(str, self))


@identifier(TagClass.UNIVERSAL, 2)
class Integer(int, PrimitiveType):
    pass


@identifier(TagClass.UNIVERSAL, 4)
class OctetString(bytes, PrimitiveType):
    pass


@identifier(TagClass.UNIVERSAL, 5)
class Null(PrimitiveType):
    pass
