"""Provides the interface to check if the plugin supports the given instance.

This module implements the qcw interface to check if a given instance is
supported by the plugin or not.
"""

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

import sys
import typing as ty


def supports_routine(routine) -> ty.Tuple[bool, ty.Optional[str]]:
    """Check plugin compatibility with the given routine.

    :param routine: framework-specific routine instance.
    :return: True if the plugin supports this type of routine, else False. If
        False, the second entry in the returned tuple is not None and explains
        why this plugin does not support the given routine type.
    """
    # If xacc has not been imported, it is impossible that the given instance
    # is of any xacc type, so we can already return False.
    if "xacc" not in sys.modules:
        return (
            False,
            "'xacc' has not been imported yet, the given routine cannot be of "
            "an XACC type.",
        )

    # An instance is supported if its type is CompositeInstruction
    from xacc import CompositeInstruction

    if not isinstance(routine, CompositeInstruction):
        return (
            False,
            f"The given routine type '{type(routine).__name__}' is not "
            f"'{CompositeInstruction.__name__}'.",
        )

    # Check if the OpenQASM2 code is valid
    from qcw.plugins.frameworks.xacc._utils import xacc2openqasm2
    from qcw.plugins.frameworks.openqasm2.supports_routine_test import (
        supports_routine as openqasm2_plugin_supports_routine,
    )

    return openqasm2_plugin_supports_routine(xacc2openqasm2(routine))
