"""Implement the RoutineWrapper interface for qiskit."""

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

import logging
import re
from collections.abc import Mapping
from typing import Any, Callable, Final, Iterator, Union

import numpy

from qcw.exceptions import UnsupportedEqualityTesting
from qcw.plugins.frameworks import interfaces
from qiskit.circuit import Instruction, QuantumCircuit
from qiskit.circuit.classicalregister import Clbit as QiskitClbit
from qiskit.circuit.parameterexpression import ParameterExpression
from qiskit.circuit.quantumregister import Qubit as QiskitQubit

logger = logging.getLogger(__file__)


def _get_parameters(instr: Instruction | QuantumCircuit):
    if isinstance(instr, Instruction):
        return instr.params
    elif isinstance(instr, QuantumCircuit):
        return instr.parameters
    else:
        raise NotImplementedError(type(instr).__name__)


class RoutineWrapper(interfaces.RoutineWrapper):
    """
    Wraps a QuantumCircuit instance and implement the RoutineWrapper interface.

    This class takes as input an instance of QuantumCircuit, or Instruction and
    wraps it in order to adhere to the common interface declared in
    qcw.plugins.frameworks.interfaces.RoutineWrapper.
    """

    _circuit_name_update_regex = re.compile(r"^(.*)-\d+?$")
    _ROUNDING: Final[int] = 10

    _HASH_FUNCTIONS: Mapping[type[Any], Callable[[Any], int]] = {
        int: lambda i: hash(i),
        float: lambda f: hash(round(f, RoutineWrapper._ROUNDING)),
        numpy.float64: lambda f: hash(round(f, RoutineWrapper._ROUNDING)),
        numpy.ndarray: lambda arr: hash(arr.data),
        ParameterExpression: lambda p: hash(p),
    }
    _EQUALITY_FUNCTIONS: Mapping[type[Any], Callable[[Any, Any], bool]] = {
        int: lambda i1, i2: i1 == i2,
        float: lambda f1, f2: (
            round(f1, RoutineWrapper._ROUNDING) == round(f2, RoutineWrapper._ROUNDING)
        ),
        numpy.float64: lambda f1, f2: (
            round(f1, RoutineWrapper._ROUNDING) == round(f2, RoutineWrapper._ROUNDING)
        ),
        numpy.ndarray: lambda arr1, arr2: numpy.allclose(
            arr1, arr2, atol=10 ** (-RoutineWrapper._ROUNDING)
        ),
        ParameterExpression: lambda p1, p2: p1 == p2,
    }

    def __init__(
        self,
        routine: Union[QuantumCircuit, Instruction],
        called_on_qubits: list[interfaces.Qubit] | None = None,
        called_on_clbits: list[interfaces.Clbit] | None = None,
        called_by: RoutineWrapper | None = None,
    ):
        """Initialise the RoutineWrapper instance.

        The only required public parameter is "routine", all the other
        parameters have sensible defaults explained below.

        :param routine: the Qiskit instance to wrap.
        :param called_on_qubits: the qubits the given routine is called on. If
            None, the routine is considered as the main routine.
        :param called_on_clbits: the classical bits the given routine is called
            on. If None, the routine is considered as the main routine.
        :param called_by: the RoutineWrapper instance that called this
            subroutine. If None, the routine is considered as the main routine.
        """
        # Invariant:
        # self.routine is always of type QuantumCircuit
        self._main_instruction: Instruction | QuantumCircuit = routine
        if isinstance(self._main_instruction, Instruction):
            super().__init__(self._main_instruction.definition, called_by)
        elif isinstance(self._main_instruction, QuantumCircuit):
            super().__init__(self._main_instruction, called_by)

        # Handle qubits
        qubits = self.qubits
        if called_on_qubits is None:
            main_qreg = interfaces.QuantumRegister(
                f"q{RoutineWrapper._main_bit_suffix}", len(qubits)
            )
            called_on_qubits = [
                interfaces.Qubit(main_qreg, i) for i in range(len(qubits))
            ]
        self._reversed_qubits_mapping: dict[interfaces.Qubit, interfaces.Qubit] = {
            q1: q2 for q1, q2 in zip(qubits, called_on_qubits)
        }
        # Handle clbits
        clbits = self.clbits
        if called_on_clbits is None:
            main_creg = interfaces.ClassicalRegister(
                f"c{RoutineWrapper._main_bit_suffix}", len(clbits)
            )
            called_on_clbits = [
                interfaces.Clbit(main_creg, i) for i in range(len(clbits))
            ]
        self._reversed_clbits_mapping: dict[interfaces.Clbit, interfaces.Clbit] = {
            c1: c2 for c1, c2 in zip(clbits, called_on_clbits)
        }

    def __iter__(self) -> Iterator["RoutineWrapper"]:
        """Iterate over the subroutines of self."""
        qmap: dict[QiskitQubit, interfaces.Qubit] = {
            q1: q2 for q1, q2 in zip(self.routine.qubits, self.qubits)
        }
        cmap: dict[QiskitClbit, interfaces.Clbit] = {
            q1: q2 for q1, q2 in zip(self.routine.clbits, self.clbits)
        }
        for instr, qubits, clbits in self.routine.data:
            yield RoutineWrapper(
                instr, [qmap[q] for q in qubits], [cmap[c] for c in clbits], self
            )

    @property
    def is_base(self):
        """Return True if self is a base subroutine, else False."""
        return self.routine is None

    @staticmethod
    def _name_unupdate(name: str) -> str:
        while re.match(RoutineWrapper._circuit_name_update_regex, name):
            name = re.sub(
                RoutineWrapper._circuit_name_update_regex, r"\1", name, count=1
            )
        return name

    @property
    def name(self):
        """Return the name of the subroutine represented by self."""
        return RoutineWrapper._name_unupdate(self._main_instruction.name)

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self.name}({{}})')".format(
            ",".join(map(str, _get_parameters(self._main_instruction)))
        )

    def __hash__(self) -> int:
        """Get the hash of the wrapped instruction.

        The hash depends on the name of the intruction and the hash of its
        parameters. All the parameter types of the represented instruction
        should be registered in RoutineWrapper._HASH_FUNCTIONS.

        :return: hash of the wrapped instruction
        """
        instr: Instruction | QuantumCircuit = self._main_instruction
        parameters = _get_parameters(instr)

        return hash(
            (
                instr.name,
                tuple(RoutineWrapper._HASH_FUNCTIONS[type(p)](p) for p in parameters),
            )
        )

    def __eq__(self, other: object):
        """Equality testing.

        :param other: right-hand side of the equality operator
        :return: True if self and other are equal, else False
        """
        if not isinstance(other, RoutineWrapper):
            raise UnsupportedEqualityTesting(type(self), type(other))

        sinstr: Instruction | QuantumCircuit = self._main_instruction
        oinstr: Instruction | QuantumCircuit = other._main_instruction
        sinstr_params = _get_parameters(sinstr)
        oinstr_params = _get_parameters(oinstr)

        return (
            sinstr.name == oinstr.name
            and len(sinstr_params) == len(oinstr_params)
            and all(
                type(sp) is type(op) for sp, op in zip(sinstr_params, oinstr_params)
            )
            and all(
                RoutineWrapper._EQUALITY_FUNCTIONS[type(sp)](sp, op)
                for sp, op in zip(sinstr_params, oinstr_params)
            )
        )

    @property
    def qubits(self) -> list[interfaces.Qubit]:
        """Return the qubits self is applied on."""
        if self.is_base:
            qreg = interfaces.QuantumRegister(
                f"q{RoutineWrapper._hardware_bit_suffix}",
                self._main_instruction.num_qubits,
            )
            return [
                interfaces.Qubit(qreg, i)
                for i in range(self._main_instruction.num_qubits)
            ]
        return [
            interfaces.Qubit(qreg, i)
            for qreg in self.routine.qregs
            for i in range(qreg.size)
        ]

    @property
    def clbits(self) -> list[interfaces.Clbit]:
        """Return the qubits self is applied on."""
        if self.is_base:
            creg = interfaces.QuantumRegister(
                f"c{RoutineWrapper._hardware_bit_suffix}",
                self._main_instruction.num_clbits,
            )
            return [
                interfaces.Clbit(creg, i)
                for i in range(self._main_instruction.num_clbits)
            ]
        return [
            interfaces.Clbit(creg, i)
            for creg in self.routine.cregs
            for i in range(creg.size)
        ]

    def get_parent_bit(self, bit: interfaces.Bit) -> interfaces.Bit:
        """Return the bit of the calling subroutine bound to the given bit.

        :param bit: a bit this routine is called on. "bit in self.bits" should
            be True.
        :returns: the corresponding bit in the calling subroutine.
        """
        if isinstance(bit, interfaces.Clbit):
            return self._reversed_clbits_mapping[bit]
        elif isinstance(bit, interfaces.Qubit):
            return self._reversed_qubits_mapping[bit]
        else:
            msg = f"Unsupported bit type: {type(bit).__name__}."
            raise RuntimeError(msg)
