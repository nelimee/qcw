"""Implements an helper function to create RoutineWrapper instances.

This module provides the Routine function that will automatically try to 
find the correct plugin to wrap the given routine instance.

Warning: the Routine function does not follow the usual naming convention.
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

from qcw.frameworks import frameworks
from qcw.plugins.frameworks.interfaces import RoutineWrapper as BaseRoutineWrapper
from qcw.exceptions import NoCompatiblePluginFound


def Routine(routine, **framework_kwargs) -> BaseRoutineWrapper:
    """Wrap a framework-specific routine object into a RoutineWrapper instance.

    :param routine: a framework-specific routine that is supported by one of
        the qcw plugins installed in the current environment.
    :param framework_kwargs: keyword arguments forwarded to the
        framework-specific RoutineWrapper implementation.
    :return: an instance of the framework-specific RoutineWrapper
        implementation, wrapping the given routine.
    :raise NotImplementedError: if no installed plugin can handle the given
        routine.
    """
    reasons: ty.Dict[str, str] = dict()

    for name, framework in frameworks.items():
        supports_framework, reason = framework.supports_routine(routine)
        reasons[name] = reason
        if supports_framework:
            return framework.RoutineWrapper(routine, **framework_kwargs)

    longest_framwork_name: int = max(map(len, reasons))
    raise NoCompatiblePluginFound(type(routine), reasons)
