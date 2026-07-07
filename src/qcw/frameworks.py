"""Implementation of lazy-loaders for plugins along with auto-discovery."""

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

# See
# https://packaging.python.org/guides/creating-and-discovering-plugins/#using-namespace-packages
import importlib
import inspect
import pkgutil
import types
from collections.abc import ItemsView, Iterator, MutableMapping
from typing import Any, Callable

import qcw.plugins.frameworks as qcw_frameworks_namespace_package
from qcw.exceptions import NotAPackage, UnsupportedPluginAPI


class LazyQCWPluginModuleWrapper:
    """Implement a lazy-loading interface around qcw plugins.

    This class implements a simple interface to access the important functions
    and classes provided by qcw plugins.
    Imports are performed at the very last moment, when the functions / classes
    are needed by the user, and the strict minimum is imported to avoid long
    import times.
    """

    def __init__(self, module_name: str):
        """Create an instance representing the given module name."""
        self._module_name: str = module_name
        self._supports_routine: Callable[[Any], tuple[bool, str | None]] | None = None
        self._routine_wrapper: type | None = None

    @staticmethod
    def _import_component(module_name: str, component_name: str) -> Any:
        """Import the module module_name and returns component_name from this module.

        :param module_name: an importable python module.
        :param component_name: name of an object that is declared (or imported)
            in module_name.
        :return: the object that would be obtained with the line
            "from [module_name] import [component_name]".
        :raises ImportError: when the given module_name is not an importable
            module.
        :raises UnsupportedPluginAPI: when the given module_name is an
            importable module that does not comply with the expected API
            provided by the qcw.plugins.frameworks.interfaces package.
        """
        module: types.ModuleType = importlib.import_module(module_name)
        if not hasattr(module, component_name):
            raise UnsupportedPluginAPI(module_name)
        return getattr(module, component_name)

    @property
    def supports_routine(self) -> Callable[[Any], tuple[bool, str | None]]:
        """Return the supports_routine function from the plugin.

        This property imports the supports_routine function from the
        represented plugin and returns it.
        It can be used as self.supports_routine(routine) directly, as if the
        property was a class defined in LazyQCWPluginModuleWrapper.
        """
        if self._supports_routine is None:
            module_name = f"{self._module_name}.supports_routine_test"
            self._supports_routine = LazyQCWPluginModuleWrapper._import_component(
                module_name=module_name,
                component_name="supports_routine",
            )
        return self._supports_routine

    @property
    def RoutineWrapper(self) -> type:
        """Return the RoutineWrapper class from the plugin.

        This property imports the RoutineWrapper class from the represented
        plugin and returns it.
        It can be used as self.RoutineWrapper(routine) directly, as if the
        property was a method of LazyQCWPluginModuleWrapper.
        """
        if self._routine_wrapper is None:
            module_name = "{0}.{1}".format(self._module_name, "RoutineWrapper")
            self._routine_wrapper = LazyQCWPluginModuleWrapper._import_component(
                module_name=module_name,
                component_name="RoutineWrapper",
            )
        return self._routine_wrapper


class LazyModuleLoader(MutableMapping[str, LazyQCWPluginModuleWrapper]):
    """A lazy loader for qcw plugins organised as modules.

    This class implements all the necessary interface to automatically
    discover the qcw plugins and access the different needed classes
    implemented by these modules using lazy-importing.

    To rephrase, the modules (and more importantly their dependencies)
    will only be loaded at the last moment, when the user is asking for
    it and deferring the import is no more an option.
    """

    def __init__(self, namespace_package: types.ModuleType):
        """Lazy loader for runtime-discovered modules in a namespace package.

        This class acts like a lazy-initialized dictionary that associates
        string keys to modules.

        :param namespace_package: namespace package where all the modules
            should be stored.
        """
        self._namespace_package: types.ModuleType = namespace_package
        self._prefix: str = namespace_package.__name__ + "."
        self._mapping: dict[str, LazyQCWPluginModuleWrapper] = dict()

        if not hasattr(self._namespace_package, "__path__"):
            raise NotAPackage(self._namespace_package)

        for pkg_info in pkgutil.iter_modules(self._namespace_package.__path__):
            self.__setitem__(
                pkg_info.name,
                LazyQCWPluginModuleWrapper(self._prefix + pkg_info.name),
            )

    def _initialise_module_if_not_initialised(self, module_name: str) -> None:
        """
        Initialise the entry for the given key if not already initialised.

        :param module_name: the module name without the namespace package
            prefix, i.e. the name of the module within the namespace package.
        """
        if module_name not in self._mapping or not inspect.ismodule(
            self._mapping[module_name]
        ):
            self.__setitem__(
                module_name,
                LazyQCWPluginModuleWrapper(self._prefix + module_name),
            )

    def __setitem__(
        self, module_name: str, value: LazyQCWPluginModuleWrapper | None
    ) -> None:
        """Set the entry associated to the given key.

        Does not import anything.

        :param module_name: name of the module in the namespace package to set.
        :param value: either an already imported module or None.
        """
        if value is None:
            self._initialise_module_if_not_initialised(module_name)
        else:
            self._mapping[module_name] = value

    def __delitem__(self, key: str) -> None:
        """Remove an entry from the LazyModuleLoader instance."""
        del self._mapping[key]

    def __getitem__(self, module_name: str) -> LazyQCWPluginModuleWrapper:
        """Return the lazy plugin wrapper associated with the given module name.

        :param module_name: name of the module in the namespace package to get.
        :return: the associated module wrapper.
        :raises KeyError: if the given module_name is not present in the
            LazyModuleLoader instance.
        """
        return self._mapping[module_name]

    def __len__(self) -> int:
        """Get the number of modules loaded."""
        return len(self._mapping)

    def __iter__(self) -> Iterator[str]:
        """Iterate over the loaded module names."""
        return iter(self._mapping)

    def __repr__(self):
        """Return a representation of the LazyModuleLoader."""
        return f"{type(self).__name__}({self._mapping})"

    def items(self) -> ItemsView[str, LazyQCWPluginModuleWrapper]:
        """Iterate over all the registered modules, importing them if needed."""
        return self._mapping.items()


frameworks = LazyModuleLoader(namespace_package=qcw_frameworks_namespace_package)
