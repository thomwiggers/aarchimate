"""
Defines the instructions and macros for the program
"""

from typing import Dict, List, Set, Optional, Iterable
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
    __loaded: Set['Register'] = set()
    __stored: Set['Register'] = set()
    name: str
    type: str
    offset: Optional[int]
    pointer: Optional['Register']
    register_name: Optional[str]
    stack_pointer: 'Register'
    latency: int
    cycles: int = 0
    max_registers: Dict[str, int] = {'x': 0, 'v': 0}
    last_instruction: str = 'jmp'

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
        if pointer is not None:
            assert pointer.type == 'x', \
                "Pointer needs to be a regular register"
        self.pointer = pointer
        self.offset = offset
        self.latency = 0

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (f"<Register(name={self.name}, type={self.type}, "
                f"pointer={self.pointer!r}, offset={self.offset})>")

    def __check_registers(self) -> None:
        if len([r for r in self.__loaded if r.type == 'x']) >= 32:
            regs = ', '.join(map(str, filter(lambda r: r.type == 'x',
                                             self.__loaded)))
            raise Exception(f"Too many regular registers loaded: {regs}")

        if len([r for r in self.__loaded if r.type == 'v']) >= 32:
            regs = ', '.join(map(str, filter(lambda r: r.type == 'v',
                                             self.__loaded)))
            raise Exception(f"Too many vector registers loaded: {regs}")

    def load(self) -> None:
        if self in self.__loaded:
            write(f"// Not loading {self!s} as already loaded in "
                  f"{self.register_name}")
            return
        if self not in self.__stored:
            raise Exception(f"Register {self!s} is not stored!")
        if self.pointer is None:
            raise Exception("I don't have a pointer")
        if self.pointer not in self.__loaded:
            raise Exception(
                f"Register {self!s}'s pointer {self.pointer!s} isn't loaded")
        reg = self._get_free_name()
        write(f"// Loading {self.name}")
        if self.offset is not None:
            write(f"ldr {reg}, [{self.pointer.register_name}, #{self.offset}]")
        else:
            write(f"ldr {reg}, [{self.pointer.register_name}]")
        self.__loaded.add(self)
        if self.last_instruction == 'load':
            self.cycles += 1
            write(f"// WARNING: pipeline hazard")

        self.latency = 1
        Register.last_instruction = "load"
        Register._tick()

    def store(self, pointer: 'Register' = None, offset: int = None) -> None:
        if pointer is not None:
            assert pointer.type == 'x', \
                    "Pointer needs to be a regular register"
            self.pointer = pointer
        if offset is not None:
            self.offset = offset
        if self.pointer is None or self.pointer.register_name is None:
            raise Exception("Where should I be stored?!")
        if self not in self.__loaded:
            raise Exception("I'm not even loaded!")
        if self.register_name is None:
            raise Exception("Huh, I don't have a register")

        if self.latency > 0:
            write(f"// WARNING: result not ready")
            self.cycles += self.latency

        if self.last_instruction == 'load':
            self.cycles += 1
            write(f"// WARNING: pipeline hazard")

        p = self.pointer.register_name
        write(f"// Storing {self.name}")
        if self.offset is not None:
            write(f"str {self.register_name}, [{p}, #{self.offset}]")
        else:
            write(f"str {self.register_name}, [{p}]")
        self.__stored.add(self)
        Register.last_instruction = 'load'
        self._tick()

    def store_from(self, register: 'Register') -> None:
        """Store a value from another register under self's name

        Uses this register's pointer
        """
        write(f"// Storing {self.name} via {register.name}")
        register.store(self.pointer, self.offset)

    def unload(self) -> None:
        if self not in self.__loaded:
            raise Exception("I'm not even loaded!")
        write(f"// Forgetting {self.name}")
        self.register_name = None
        self.__loaded.remove(self)

    def and_(self, i1: 'Register', i2: 'Register',
             drop: Iterable['Register'] = None) -> None:
        self._operand('and', i1, i2, drop)

    def xor(self, i1: 'Register', i2: 'Register',
            drop: Iterable['Register'] = None) -> None:
        self._operand('eor', i1, i2, drop)

    def _operand(self, operator: str, i1: 'Register', i2: 'Register',
                 drop: Iterable['Register'] = None) -> None:
        if i1 not in self.__loaded or i1.register_name is None:
            raise Exception(f"Input {i1!s} isn't loaded!")
        if i2 not in self.__loaded or i2.register_name is None:
            raise Exception(f"Input {i2!s} isn't loaded!")
        if i1.type != i2.type:
            raise Exception("Inputs should be of the same type")

        if i1.latency > 0 or i2.latency > 0:
            self.cycles += max(i1.latency, i2.latency)
            write(f"// WARNING: latency of {max(i1.latency, i2.latency)}")

        r1 = i1.register_name
        r2 = i2.register_name
        if drop is not None:
            unload(*[d for d in drop])

        reg = self._get_free_name()
        if i1.type == 'v':
            reg = vector_to_typed_vector(reg)
            r1 = vector_to_typed_vector(r1)
            r2 = vector_to_typed_vector(r2)

        write(f"// {self.name} = {i1.name} `{operator}` {i2.name}")
        write(f"{operator} {reg}, {r1}, {r2}")
        self.__loaded.add(self)
        self._tick()
        Register.last_instruction = 'op'
        self.latency = 1

    def subi(self, i1: 'Register', imm: int) -> None:
        self._opi("sub", i1, imm)

    def _opi(self, operation: str, i1: 'Register', imm: int) -> None:
        if i1 not in self.__loaded:
            raise Exception(f"Input {i1!s} isn't loaded!")
        if i1.type != 'x':
            raise ValueError("Only regular registers supported")

        if i1.latency > 0:
            self.cycles += i1.latency
            write(f"// WARNING: latency of {i1.latency}")

        reg = self._get_free_name()
        self.__loaded.add(self)
        write(f"// {self.name} = {i1.name} `{operation}` #{imm}")
        write(f"{operation} {reg}, {i1.register_name}, #{imm}")

    def addi(self, i1: 'Register', imm: int) -> None:
        self._opi('add', i1, imm)

    def store_register(self) -> None:
        raise Exception("Todo")

    def rename(self, register: 'Register') -> None:
        self.register_name = register.register_name
        self.latency = register.latency
        self.__loaded.add(self)
        self.__loaded.remove(register)
        if register in self.__stored:
            if (register.pointer != self.pointer and
                    register.offset != self.offset):
                raise Exception(
                    f"This register ({register}) has already been stored "
                    "somewhere else")
            else:
                self.__stored.add(self)

    def mov(self, register: 'Register') -> None:
        if register not in self.__loaded or register.register_name is None:
            raise Exception(f"Input {register} isn't loaded")
        reg = self._get_free_name()
        write(f"mov {reg}, {register.register_name}")
        self.__loaded.add(self)

    @classmethod
    def _tick(cls) -> None:
        for r in cls.__loaded:
            if r.latency > 0:
                r.latency -= 1
        cls.cycles += 1
        cls.max_registers['x'] = max(cls.max_registers['x'], len(
            [1 for r in cls.__loaded if r.type == 'x']))
        cls.max_registers['v'] = max(cls.max_registers['v'], len(
            [1 for r in cls.__loaded if r.type == 'v']))

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
        cls.__loaded = set()
        cls.__stored = set()

    @classmethod
    def get(cls, name: str) -> 'Register':
        for i in (cls.__loaded.union(cls.__stored)):
            if i.name == name:
                return i
        raise Exception(f"Register {name} not found")

    @classmethod
    def _prepare(cls, inputs: Iterable['Register'],
                 stored: Iterable['Register']) -> None:
        assert not cls.__loaded, "Still loaded registers! Reset first"
        assert not cls.__stored, "Still stored registers! Reset first"
        for i in inputs:
            if i.register_name is None:
                raise Exception("Claimed input {i} should have a register!")
        cls.__loaded = set(inputs)
        cls.__stored = set(stored)
        cls.__loaded.add(cls.stack_pointer)
        cls.__loaded.add(Register('fp', register='fp', type='x'))
        cls.__loaded.update([Register(f'x{i}', register=f'x{i}', type='x') for
                             i in range(16, 30)])
        cls.__loaded.update([Register(f'q{i}', register=f'q{i}')
                             for i in range(8, 16)])

    @classmethod
    def debug(cls) -> None:
        regs = sorted([r.name for r in cls.__loaded if r.type == 'x'])
        vecs = sorted([r.name for r in cls.__loaded if r.type == 'v'])
        stored = sorted([r.name for r in cls.__stored if r.type == 'v'])
        write(f"// Loaded registers: {', '.join(regs)}")
        write(f"// Loaded vectors:   {', '.join(vecs)}")
        write(f"// Stored vectors: {', '.join(stored)}")

    @classmethod
    def loaded(cls) -> Set['Register']:
        return cls.__loaded

    @classmethod
    def stored(cls) -> Set['Register']:
        return cls.__stored

    def mark_stored(self) -> None:
        self.__stored.add(self)


Register.stack_pointer = Register('sp', register='sp', type='x')


def start_file() -> None:
    write(".text")


def start_function(name: str,
                   input_assumptions: Iterable[Register],
                   store_assumptions: Iterable[Register]) -> None:
    """Start a function of name"""
    write("\n")
    write(".align 2")
    write(f".global {name}")
    write(f".type {name}, %function")
    write(f"{name}:")
    write(f"_{name}:")
    Register._prepare(input_assumptions, store_assumptions)
    Register.debug()


def end_function() -> None:
    """End a function"""
    write("ret")
    write(f"// Cycle count: {Register.cycles}")
    write(f"// Max register pressure: {Register.max_registers}")
    Register.reset()


def do_and(name: str, i1: Register, i2: Register,
           drop: Iterable[Register] = None) -> Register:
    r = Register(name)
    r.and_(i1, i2, drop)
    return r


def do_xor(name: str, i1: Register, i2: Register,
           drop: Iterable[Register] = None) -> Register:
    r = Register(name)
    r.xor(i1, i2, drop)
    return r


def unload(*regs: Register) -> None:
    for r in regs:  # type: Register
        r.unload()
