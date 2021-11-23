"""Declaration of several customised exceptions for the library."""

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
import types


class QCWException(BaseException):
    """Base for all qcw exceptions."""

    def __init__(self, message: str):
        """Forward the message to BaseException.__init__."""
        super(QCWException, self).__init__(message)


class UnsupportedPluginAPI(QCWException):
    """Thrown when a plugin does not implement the required interface."""

    def __init__(self, plugin_module_name: str):
        """Insert the provided plugin name into an explanatory message."""
        super(UnsupportedPluginAPI, self).__init__(
            f"The plugin '{plugin_module_name}' does not implement the "
            f"required interface correctly."
        )


class UnsupportedEqualityTesting(QCWException):
    """Thrown when someone compare a RoutineWrapper with a non-RoutineWrapper.

    RoutineWrapper does not support equality testing with instances of other
    types. When this happens, the UnsupportedEqualityTesting exception is
    thrown.
    """

    def __init__(self, self_type: ty.Type, other_type: ty.Type):
        """Insert the provided types into an explanatory message."""
        super(UnsupportedEqualityTesting, self).__init__(
            f"Cannot compare an instance of'{self_type.__name__}' with "
            f"an instance of '{other_type.__name__}'."
        )


class NotAPackage(QCWException):
    """Thrown when a module that is not a package is given to LazyModuleLoader.

    The LazyModuleLoader only supports packages as input. If a module that is
    not a package (i.e. that has no '__path__') is given, this exception will
    be thrown.
    """

    def __init__(self, module: types.ModuleType):
        """Insert the provided module name into an explanatory message."""
        super(NotAPackage, self).__init__(
            f"Module '{module.__name__}' is not a package (no '__path__' "
            f"found in the variables declared in the given module)."
        )


class NoCompatiblePluginFound(QCWException):
    """Thrown when no plugin supports the given routine instance."""

    def __init__(self, routine_type: ty.Type, reasons: ty.Dict[str, str]):
        """Build a useful message to understand why no framework was used."""
        longest_framwork_name: int = max(map(len, reasons))
        super(NoCompatiblePluginFound, self).__init__(
            f"No plugin found for routine type '{routine_type.__name__}'."
            + "\nExplanations:"
            + "\n    "
            + "\n    ".join(
                (
                    ("{:<" + f"{longest_framwork_name}" + "}").format(name)
                    + f": {reason}"
                    for name, reason in reasons.items()
                )
            )
        )
