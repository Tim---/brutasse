ASN.1
=====

.. py:currentmodule:: brutasse.asn1

Brutasse comes with a minimal and incomplete ASN.1 implementation.
Its initial goal is to contain just enough features to implement SNMP.
Also, it is built with type annotations in mind.

Primitive types
---------------

The ASN.1 module implements the four primitive types: :class:`Integer`,
:class:`OctetString`, :class:`Null`, and :class:`ObjectIdentifier`.

>>> from brutasse.asn1 import *
>>> integer = Integer(1)
>>> octet_string = OctetString(b'test')
>>> null = Null()
>>> oid1 = ObjectIdentifier((1, 3, 6, 1))
>>> oid2 = ObjectIdentifier.from_string('1.3.6.1')

Note that :class:`Integer` and :class:`OctetString`
are subclasses of :class:`int` and :class:`bytes` respectively.

BER encoding and decoding
-------------------------

Instances of ASN.1 types can be encoded and decoded in BER format:

>>> ber_build(Integer(1))
b'\x02\x01\x01'
>>> ber_parse(b'\x02\x01\x01', Integer)
Integer(1)

Note that we need to provide the expected type to :func:`ber_parse`.

Sequence
--------

We can create a custom sequence by subclassing the :class:`Sequence` class:

>>> from dataclasses import dataclass
>>> @dataclass
... class MySequence(Sequence):
...     number: Integer
...     data: OctetString
... 
>>> seq = MySequence(Integer(123), OctetString(b'test'))

The type annotations are needed for serialization and deserialization.

Choice
------

An ASN.1 choice is implemented using an :class:`types.UnionType` types:

>>> ber_parse(b'\x02\x01\x01', OctetString | Integer)
Integer(1)

Tagging
-------

We can create a type with a different implicit tag using the
:func:`identifier` decorator.

>>> @identifier(TagClass.APPLICATION, 1)
... class CustomInteger(Integer):
...     pass
>>> ber_build(CustomInteger(1))
b'A\x01\x01'

Enumeration
-----------

Enumerated types can be created with multiple inheritance:

>>> import enum
>>> class Boolean(Integer, enum.Enum):
...     FALSE = 0
...     TRUE = 1
>>> ber_build(Boolean.TRUE)
b'\x02\x01\x01'
>>> ber_parse(b'\x02\x01\x01', Boolean)
<Boolean.TRUE: Integer(1)>

>>> class Perm(Integer, enum.Flag):
...     READ = 4
...     WRITE = 2
...     EXECUTE = 1
>>> ber_build(Perm.READ | Perm.WRITE)
b'\x02\x01\x06'
>>> ber_parse(b'\x02\x01\x06', Perm)
<Perm.READ|WRITE: int(6)>
