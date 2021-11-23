"""Main interface to test if the plugin supports a given routine type.

This module declares the interface that should be implemented by all the qcw
plugins in order to check if a given routine is supported by the plugin.
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

import typing as ty


def supports_routine(routine) -> ty.Tuple[bool, ty.Optional[str]]:
    """Check plugin compatibility with the given routine.

    :param routine: framework-specific routine instance.
    :return: True if the plugin supports this type of routine, else False. If
        False, the second entry in the returned tuple is not None and explains
        why this plugin does not support the given routine type.
    """
    return False, "'qprof_interface' module does not support any routine type."
