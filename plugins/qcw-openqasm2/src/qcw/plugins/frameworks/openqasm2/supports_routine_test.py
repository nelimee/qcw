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

import logging
import typing as ty

logger = logging.getLogger(__file__)


def supports_routine(routine) -> ty.Tuple[bool, ty.Optional[str]]:
    """Check plugin compatibility with the given routine.

    :param routine: framework-specific routine instance.
    :return: True if the plugin supports this type of routine, else False. If
        False, the second entry in the returned tuple is not None and explains
        why this plugin does not support the given routine type.
    """
    # An instance is supported if it is a string representing a valid
    # OpenQASM 2.0 program

    # If it is not a string we can exit early without importing qiskit.
    if not isinstance(routine, str):
        return False, f"Instance of '{type(routine).__name__}' is not a string."

    from qiskit.qasm import Qasm, QasmError

    try:
        Qasm(data=routine).parse()
    except QasmError:
        # Invalid OpenQASM 2.0 file
        return False, "Could not parse OpenQASM 2.0."
    except Exception as e:
        # Another exception was raised! This is not expected, so log it and
        # return False
        printed_routine: str = "    " + routine.replace("\n", "\n    ")
        logger.error(
            f"Exception of type {type(e)} has been raised when giving "
            f"\n{printed_routine}\n\nMessage: {e}"
        )
        return False, f"{e}"
    else:
        # If nothing was raised, the file has been successfully parsed so
        # it is a valid OpenQASM 2.0 file.
        return True, None
