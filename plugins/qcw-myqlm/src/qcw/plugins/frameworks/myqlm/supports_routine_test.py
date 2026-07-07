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
    # If qat has not been imported, it cannot be a routine supported by this
    # plugin. This simple check avoids importing qat when it is not needed.
    if "qat" not in sys.modules:
        return (
            False,
            "'myqlm' has not been imported yet, the given routine cannot be "
            "of any MyQLM type.",
        )

    from qat.lang.AQASM.gates import ParamGate

    if not isinstance(routine, ParamGate):
        return (
            False,
            f"The provided routine of type '{type(routine).__name__}' is "
            f"not an instance of '{ParamGate.__name__}'.",
        )
    else:
        return True, None
