"""
Defines the instructions and macros for the program
"""

from typing import Dict, List, Optional
import re

write = print

vector_regex = re.compile(r'^q(?P<id>\d+)$')


def vector_to_typed_vector(name: str, type: str='8b') -> str:
    m = vector_regex.match(name)
    if not m:
        raise ValueError(f"Invalid input {name}, expected qi")
    return f"v{m.group('id')}.{type}"


class Register(object):
    names: Dict[str, List[str]] = {'x': [f'x{i}' for i in range(0, 32)],
                                   'v': [f'q{i}' for i in range(0, 32)]}
    __loaded: List['Register'] = []
    __stored: List['Register'] = []
    name: str
    type: str
    offset: Optional[int]
    pointer: Optional['Register']
    register_name: str

    def __init__(self,
                 name: str,
                 type: str = 'v',
                 register: str = None,
                 pointer: 'Register' = None,
                 offset: int = None) -> None:
        self.name = name
        if type not in self.names.keys():
            raise ValueError("invalid type")
        self.register_name = register
        self.type = type
        self.pointer = pointer
        self.offset = offset

    def __str__(self) -> str:
        return f"Register {self.name}"

    def __check_registers(self) -> None:
        if len(self.__loaded) >= 32:
            raise Exception("Too many registers loaded: f{self.__loaded}")

    def load(self) -> None:
        if self not in self.__stored:
            raise Exception("Register {src!s} is not stored!")
        if self.pointer not in self.__loaded:
            raise Exception(
                "Register {self!s}'s pointer {self.pointer!s} isn't loaded")
        reg = self._get_free_name()
        if self.offset is not None:
            write(f"ldr {reg}, [{self.pointer.register_name}, #{self.offset}]")
        else:
            write(f"ldr {reg}, [{self.pointer.register_name}]")

    def and_(self, i1: 'Register', i2: 'Register') -> None:
        self._operand('and', i1, i2)

    def xor(self, i1: 'Register', i2: 'Register') -> None:
        self._operand('xor', i1, i2)

    def _operand(self, operator: str, i1: 'Register', i2: 'Register') -> None:
        if i1 not in self.__loaded:
            raise Exception("Input {i1!s} isn't loaded!")
        if i2 not in self.__loaded:
            raise Exception("Input {i2!s} isn't loaded!")

        reg = self._get_free_name()
        write(f"{operator} {reg}, {i1.register_name}, {i2.register_name}")

    def store_register(self) -> None:
        raise Exception("Todo")

    def _get_free_name(self) -> str:
        if self.register_name is not None:
            return self.register_name
        self.__check_registers()
        registers = [r.register_name for r in self.__loaded]
        for name in self.names[self.type]:
            if name not in registers:
                self.register_name = name
                break
        else:
            raise Exception("Why couldn't I find a register?")
        return self.register_name

    @classmethod
    def reset(cls) -> None:
        cls.__loaded = []
        cls.__stored = []

    @classmethod
    def _prepare(cls, inputs: List['Register'],
                 stored: List['Register']) -> None:
        assert not cls.__loaded, "Still loaded registers! Reset first"
        assert not cls.__stored, "Still stored registers! Reset first"
        for i in inputs:
            if i.register_name is None:
                raise Exception("Claimed input {i} should have a register!")
        cls.__loaded = inputs
        cls.__stored = stored


def start_file() -> None:
    write(".text")


def start_function(name: str,
                   input_assumptions: List[Register],
                   store_assumptions: List[Register]) -> None:
    """Start a function of name"""
    write(".align 2")
    write(f".global {name}")
    write(f".type {name}, %function")
    Register._prepare(input_assumptions, store_assumptions)


def end_function() -> None:
    """End a function"""
    write("ret")
    Register.reset()
