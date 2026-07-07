"""Implement the RoutineWrapper interface for XACC."""

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

from ._utils import xacc2openqasm2
from qcw.plugins.frameworks.openqasm2.RoutineWrapper import (
    RoutineWrapper as OpenQASM2RoutineWrapper,
)


class RoutineWrapper(OpenQASM2RoutineWrapper):
    """
    Wraps a XACC instance and implements the RoutineWrapper interface.

    This class takes as input an instance of CompositeInstruction and
    wraps it in order to adhere to the common interface declared in
    qcw.plugins.frameworks.interfaces.RoutineWrapper.
    """

    def __init__(self, routine: xacc.CompositeInstruction):
        """Initialise the RoutineWrapper instance.

        :param routine: the XACC instance to wrap.
        """
        super().__init__(xacc2openqasm2(routine))
