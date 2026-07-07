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

import inspect
import typing as ty
from collections import deque
from types import ModuleType

from qat.core.gate_set import GateSet, GateSignature
from qat.lang.AQASM.gates import AbstractGate, Gate, ParamGate, PredefGate
from qat.lang.AQASM.routines import QRoutine

from qcw.plugins.frameworks import interfaces

GateType = ty.Union[ParamGate, AbstractGate, QRoutine, PredefGate, Gate]
GateWithName = GateType
LinkingType = ty.Union[AbstractGate, GateSet, ModuleType]
LinkingSetType = ty.Dict[str, LinkingType]
LinkingSetInitType = ty.Union[ty.Dict[str, LinkingType], ty.List[LinkingType]]
GateCtrlIterable = ty.Iterable[ty.Tuple[GateType, int]]


class RoutineWrapper(interfaces.RoutineWrapper):
    """
    Wraps a Paramgate instance and implement the RoutineWrapper interface.

    This class takes as input an instance of Paramgate and wraps it in order to
    adhere to the common interface declared in
    qcw.plugins.frameworks.interfaces.RoutineWrapper.
    """

    _GATE_TYPES = [ParamGate, AbstractGate, QRoutine, PredefGate, Gate]
    _IGNORED_GATE_NAMES = {"LOCK"}

    def _iter_from_ParamGate(self, gate: ParamGate, ctrl: int) -> GateCtrlIterable:
        if gate.name in self._linking_set:
            gate.abstract_gate.set_circuit_generator(
                self._linking_set[gate.name].circuit_generator
            )
        yield (
            gate.abstract_gate.circuit_generator(*gate.parameters),
            ctrl + (gate.nb_ctrls or 0),
        )

    def _iter_from_PredefGate(self, gate: PredefGate, ctrl: int) -> GateCtrlIterable:
        # Return an iterable containing the predefined gate only
        yield gate, ctrl

    def _iter_from_QRoutine(self, gate: QRoutine, ctrl: int) -> GateCtrlIterable:
        yield from (
            (
                op.gate,
                (
                    0
                    if self.use_protected_gates and op.ctrl_prot
                    else ctrl + (gate.nb_ctrls or 0)
                ),
            )
            # TODO: qubit information is located in op.args
            for op in gate.op_list
        )

    def _iter_from_Gate(self, gate: Gate, ctrl: int) -> GateCtrlIterable:
        yield gate.subgate, ctrl + (gate.nb_ctrls or 0)

    def _iter_from(self, gate: GateType, ctrl: int) -> GateCtrlIterable:
        type_name: str = type(gate).__name__
        if not hasattr(self, f"_iter_from_{type_name}"):
            raise RuntimeError(
                f"Can't iterate over {type_name}. Please implement "
                f"'qprof_myqlm.RoutineWrapper._iter_from_{type_name}' "
                "to avoid this error."
            )
        yield from getattr(self, f"_iter_from_{type_name}")(gate, ctrl)

    def __init__(
        self,
        gate: GateWithName,
        linking_set: ty.Optional[LinkingSetInitType] = None,
        use_protected_gates: bool = False,
        _number_of_controlled_qubits: int = 0,
        _called_by: ty.Optional["RoutineWrapper"] = None,
    ):
        """Initialise the RoutineWrapper instance.

        :param gate: the MyQLM instance to wrap.
        :param linking_set: any instance that can be used to link gate
            implementation according to MyQLM documentation.
        :param use_protected_gates: if True, take into account the gate
            "protected" gates that are gates applied via the "protected_apply"
            method and that are "protected" from controls.
        """
        super().__init__(gate, _called_by)

        self.use_protected_gates = use_protected_gates
        self._gate = gate
        # If the gate is controlled, first save the actual number of controls.
        self._num_control_qubits_without_self = _number_of_controlled_qubits
        self._num_controlled_qubits = _number_of_controlled_qubits + (
            gate.nb_ctrls or 0
        )

        # Default value
        if linking_set is None:
            linking_set = dict()

        # Get the linking set in the appropriate format
        self._linking_set: LinkingSetType = dict()
        if isinstance(linking_set, dict):
            self._linking_set = linking_set
        else:
            for link in linking_set:
                if isinstance(link, AbstractGate) or isinstance(link, GateSet):
                    self._linking_set[link.name] = link
                elif isinstance(link, ModuleType):
                    # Get all the GateSignature instances in the module
                    for _, gate in inspect.getmembers(
                        link, predicate=lambda x: isinstance(x, GateSignature)
                    ):
                        self._linking_set[gate.name] = gate

    def __iter__(self):
        """Iterate over the subroutines of self."""
        queue = deque()
        queue.extend(self._iter_from(self._gate, self._num_control_qubits_without_self))
        while queue:
            gate, ctrl = queue.popleft()
            name = getattr(gate, "name", None)
            if name is None:
                # Iterate over the provided gate
                queue.extend(self._iter_from(gate, ctrl))
            elif name in RoutineWrapper._IGNORED_GATE_NAMES:
                continue
            else:
                # yield the gate
                yield RoutineWrapper(
                    gate,
                    self._linking_set,
                    self.use_protected_gates,
                    _number_of_controlled_qubits=ctrl,
                    _called_by=self,
                )

    @staticmethod
    def is_base_gate(gate: GateType, linking_set: LinkingSetType) -> bool:
        """Return True if self is a base subroutine, else False."""
        if isinstance(gate, PredefGate):
            return True
        elif isinstance(gate, ParamGate):
            return (
                gate.abstract_gate.circuit_generator is None
                and gate.abstract_gate.name not in linking_set
            )
        return False

    @property
    def is_base(self):
        """Return True if self is a base subroutine, else False."""
        return RoutineWrapper.is_base_gate(self._gate, self._linking_set)

    @property
    def name(self):
        """Return the name of the subroutine represented by self."""
        base_name: str = getattr(self._gate, "name", "")
        if not base_name and hasattr(self._gate, "subgate"):
            base_name = getattr(self._gate.subgate, "name", "")

        if not base_name:
            raise RuntimeError(
                "Cannot extract the name of the provided routine. Ensure that "
                "the routine given has a non-empty 'name' attribute or a "
                "non-empty 'subgate' attribute that has a non-empty 'name' "
                "attribute."
            )

        if base_name.upper() == "X" and self._num_controlled_qubits > 0:
            base_name = "NOT"
        return (
            "C" * self._num_controlled_qubits
            + ("D" if self._gate.is_dag else "")
            + base_name
        )

    def __hash__(self):
        """Get the hash of the wrapped instruction.

        :return: hash of the wrapped instruction
        """
        if self.is_base:
            return hash(self.name)
        return hash(
            (
                self.name,
                getattr(self, "parameters", tuple()),
                id(getattr(self, "abstract_gate"))
                if hasattr(self, "abstract_gate")
                else 0,
            )
        )

    def __eq__(self, other):
        """Equality testing.

        :param other: right-hand side of the equality operator
        :return: True if self and other are equal, else False
        """
        if not isinstance(other, RoutineWrapper):
            return False
        if self.is_base and other.is_base:
            return self.name == other.name
        self_parameters = getattr(self._gate, "parameters", [])
        other_parameters = getattr(other._gate, "parameters", [])
        self_abstract_gate = getattr(self._gate, "abstract_gate", None)
        other_abstract_gate = getattr(other._gate, "abstract_gate", None)
        return (
            self._num_controlled_qubits == other._num_controlled_qubits
            and type(self._gate) is type(other._gate)
            and id(self_abstract_gate) == id(other_abstract_gate)
            and len(self_parameters) == len(other_parameters)
            and all(a == b for a, b in zip(self_parameters, other_parameters))
        )

    @property
    def is_controlled(self):
        """Return true if self has at least one control."""
        return self._num_controlled_qubits > 0

    @property
    def qubits(self) -> ty.List[interfaces.Qubit]:
        """Return the qubits self is applied on."""
        raise NotImplementedError()

    @property
    def clbits(self) -> ty.List[interfaces.Clbit]:
        """Return the qubits self is applied on."""
        raise NotImplementedError()

    def get_parent_bit(self, bit: interfaces.Bit) -> interfaces.Bit:
        """Return the bit of the calling subroutine bound to the given bit.

        :param bit: a bit this routine is called on. "bit in self.bits" should
            be True.
        :returns: the corresponding bit in the calling subroutine.
        """
        raise NotImplementedError()
