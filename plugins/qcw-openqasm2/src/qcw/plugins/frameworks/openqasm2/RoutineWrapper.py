"""Implement the RoutineWrapper interface for OpenQASM 2.0."""

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

import re
import typing as ty
from typing import Iterable, Union

from qiskit import QuantumCircuit
from qcw.plugins.frameworks.qiskit.RoutineWrapper import (
    RoutineWrapper as QiskitRoutineWrapper,
)


class RoutineWrapper(QiskitRoutineWrapper):
    """
    Wraps an OpenQASM 2.0 circuit and implements the RoutineWrapper interface.

    This class takes as input a string containing a valid OpenQASM 2.0
    program and wraps it in order to adhere to the common interface declared in
    qcw.plugins.frameworks.interfaces.RoutineWrapper.
    """

    def __init__(self, routine: str):
        """Initialise the RoutineWrapper instance.

        :param routine: a string containing a valid OpenQASM 2.0 program.
        """
        qiskit_circuit: QuantumCircuit = QuantumCircuit.from_qasm_str(routine)
        super().__init__(qiskit_circuit)
