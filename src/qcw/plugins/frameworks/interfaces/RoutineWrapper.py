"""Declaration of the interface for the main RoutineWrapper class."""

# =============================================================================
#
# Copyright: CERFACS, LIRMM, Total S.A. - the quantum computing team (March
#            2021).
# Contributor: Adrien Suau (adrien.suau@cerfacs.fr)
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your discretion)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
#
# See the GNU Lesser General Public License for more details. You should have
# received a copy of the GNU Lesser General Public License along with this
# program. If not, see https://www.gnu.org/licenses/lgpl-3.0.txt
#
# =============================================================================
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Iterable, Iterator

from qcw.exceptions import UnsupportedEqualityTesting


@dataclass
class Register:
    """Base class representing a generic register.

    A register is characterised by a name and its size.
    """

    def __hash__(self) -> int:
        """Return a hash of self."""
        return hash((self.name, self.size))

    name: str
    size: int


@dataclass
class QuantumRegister(Register):
    """Representation of a quantum register.

    A quantum register is characterised by a name and its size.
    """

    def __hash__(self) -> int:
        """Return a hash of self."""
        return super().__hash__()


@dataclass
class ClassicalRegister(Register):
    """Representation of a classical register.

    A classical register is characterised by a name and its size.
    """

    def __hash__(self) -> int:
        """Return a hash of self."""
        return super().__hash__()


@dataclass
class Bit:
    """Base class representing a generic bit.

    A generic bit is characterised by the register it belongs to and its index
    in this register.
    """

    def __hash__(self) -> int:
        """Return a hash of self."""
        return hash((self.reg, self.index))

    def __repr__(self) -> str:
        """Return a textual representation of a bit."""
        return f"{self.reg.name}[{self.reg.size}]({self.index})"

    def __str__(self) -> str:
        """Return a user-readable representation of a bit."""
        return self.__repr__()

    reg: Register
    index: int


@dataclass
class Qubit(Bit):
    """Base class representing a quantum bit.

    A quantum bit is characterised by the register it belongs to and its index
    in this register.
    """

    def __hash__(self) -> int:
        """Return a hash of self."""
        return super().__hash__()

    def __repr__(self) -> str:
        """Return a textual representation of a qubit."""
        return super().__repr__()

    def __str__(self) -> str:
        """Return a user-readable representation of a qubit."""
        return super().__str__()


@dataclass
class Clbit(Bit):
    """Base class representing a classical bit.

    A classical bit is characterised by the register it belongs to and its
    index in this register.
    """

    def __hash__(self) -> int:
        """Return a hash of self."""
        return super().__hash__()

    def __repr__(self) -> str:
        """Return a user-readable representation of a classical bit."""
        return super().__repr__()

    def __str__(self) -> str:
        """Return a user-readable representation of a classical bit."""
        return super().__str__()


class RoutineWrapper(abc.ABC, Iterable["RoutineWrapper"]):
    """Wrapper around the framework-specific routine type.

    This class should be subclassed and implemented for each framework. It
    helps providing a unique API for all the frameworks that can then be used
    by other libraries.
    """

    _main_bit_suffix: str = "main"
    _hardware_bit_suffix: str = "hardware"

    @abc.abstractmethod
    def __init__(self, routine: Any, parent: Any | None):
        """Initialise the wrapper with the given routine.

        :param routine: a framework-specific routine that will be wrapped.
        """
        self._routine = routine
        self._parent = parent

    @property
    def routine(self) -> Any:
        """Return the framework-specific routine given at initialisation."""
        return self._routine

    @property
    def parent(self) -> Any | None:
        """Return the framework-specific parent given at initialisation."""
        return self._parent

    @abc.abstractmethod
    def __iter__(self) -> Iterator[RoutineWrapper]:
        """Magic Python method to make the RoutineWrapper object iterable.

        :return: an iterable over all the subroutines called by the wrapped
            routine. The subroutines should be wrapped by the RoutineWrapper.
        """
        pass

    @property
    def ops(self) -> tuple[RoutineWrapper, ...]:
        """Return a list of the subroutines called by self."""
        return tuple(self)

    @property
    @abc.abstractmethod
    def is_base(self) -> bool:
        """Check if the wrapped routine is a "base" routine.

        Base routines are routines that are considered as primitive, i.e. that
        do not call any subroutine.
        The concept of base routine is essential for qprof as only base
        routines should have an entry in the "gate_times" dictionary provided
        to the "profile" method and base routines are used to stop the
        recursion into the call-tree.

        :return: True if the wrapped routine is considered as a "base" routine,
            else False.
        """
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of the wrapped subroutine."""
        pass

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self.name}')"

    def __hash__(self) -> int:
        """Compute the hash of the wrapped routine.

        __hash__ and __eq__ methods are used by qprof to cache routines and
        re-use already computed data. This optimisation gives impressive
        results on some circuits and is expected to improve the runtime of
        qprof on nearly all quantum circuits, because routines are most of the
        time re-used.

        By default the hash function will return the id of the stored routine,
        effectively disabling the caching mechanism. It is up to the plugin
        developers to implement an efficient hash for the framework-specific
        routine type if they want such a caching mechanism to be used.

        :return: int representing a hash of the wrapper routine.
        """
        return id(self._routine)

    def __eq__(self, other) -> bool:
        """Equality testing for wrapped routines.

        __hash__ and __eq__ methods are used by qprof to cache routines and
        re-use already computed data. This optimisation gives impressive
        results on some circuits and is expected to improve the runtime of
        qprof on nearly all quantum circuits, because routines are most of the
        time re-used.

        Two routines should be considered equal if and only if they generate
        exactly the same circuit.

        Comparing the generated circuits might be a costly task, but other
        methods can be used. For example, routines with the same name and the
        same parameters might be considered as equal (may be
        framework-dependent).

        By default the equality test will test for ids equality of the stored
        routines, effectively disabling the caching mechanism. It is up to the
        plugin developers to implement an efficient equality test for the
        framework-specific routine type if they want such a caching mechanism
        to be used.

        :param other: instance of RoutineWrapper to test for equality with
            self.
        :return: True if self and other are equal (i.e. generate the exact same
            quantum circuit) else False.
        """
        if not isinstance(other, RoutineWrapper):
            raise UnsupportedEqualityTesting(type(self), type(other))
        return id(self._routine) == id(other._routine)

    @property
    @abc.abstractmethod
    def qubits(self) -> Iterable[Qubit]:
        """Return the qubits self is applied on."""
        pass

    @property
    @abc.abstractmethod
    def clbits(self) -> Iterable[Clbit]:
        """Return the classical bits self is applied on."""
        pass

    @property
    def bits(self) -> Iterable[Bit]:
        """Return the bits self is applied on."""
        yield from self.qubits
        yield from self.clbits

    @abc.abstractmethod
    def get_parent_bit(self, bit: Bit) -> Bit:
        """Return the bit of the calling subroutine bound to the given bit.

        :param bit: a bit this routine is called on. "bit in self.bits" should
            be True.
        :returns: the corresponding bit in the calling subroutine.
        """
        pass

    def get_bit_global_index(self, bit: Bit) -> int:
        """Return the global index of the given bit.

        The global index is the index of the main routine bit bound to the
        given bit.

        :param bit: one of the bits self is applied on.
        :returns: the global index of the given bit.
        """
        current_bit: Bit = bit
        current_routine: RoutineWrapper = self
        while current_routine.parent is not None:
            current_bit = current_routine.get_parent_bit(current_bit)
            current_routine = current_routine.parent
        return current_bit.index
