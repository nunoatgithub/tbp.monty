# Copyright 2025 Thousand Brains Project
# Copyright 2022-2024 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from __future__ import annotations

import importlib
import inspect
import unittest
from types import ModuleType

import tbp.monty.simulators.habitat_impl as habitat_impl
import tbp.monty.simulators.habitat_proxy as habitat_proxy

NAMES = ["actions", "actuator", "agents", "configs", "environment", "sensors", "simulator"]

impl_modules = [importlib.import_module(f"{habitat_impl.__name__}.{name}") for name in NAMES]
proxy_modules = [importlib.import_module(f"{habitat_proxy.__name__}.{name}") for name in NAMES]

assert len(impl_modules) == 7 and len(proxy_modules) == 7


class HabitatProxyTest(unittest.TestCase):

    def test_proxy_exports_same_symbols_as_habitat_impl(self):
        self._assert_symbols_match(habitat_impl, habitat_proxy, "package")
        for (impl_module, proxy_module, name) in zip(impl_modules, proxy_modules, NAMES):
            self._assert_symbols_match(impl_module, proxy_module, name)

    def test_proxy_callables_have_matching_signatures(self):
        self._assert_callable_signatures_match(habitat_impl, habitat_proxy, "package")
        for (impl_module, proxy_module, name) in zip(impl_modules, proxy_modules, NAMES):
            self._assert_callable_signatures_match(impl_module, proxy_module, name)

    @staticmethod
    def is_defined_in_this_module(obj):
        module = getattr(obj, '__module__', None)

        # Case 1: Has __module__ → compare it
        if module is not None:
            return module == __name__  # __name__ is current module name

        # Case 2: No __module__ attribute
        # → It's either a builtin OR a simple object (int, str, list, etc.)
        # → Simple objects defined here have no __module__, but builtins usually in 'builtins'
        if hasattr(obj, '__name__') and obj is getattr(__builtins__, obj.__name__, None):
            return False  # it's a builtin like len, print, etc.

        # Otherwise: probably a local variable, lambda without module, etc.
        return True

    @staticmethod
    def _is_imported_symbol(symbol: str, module: ModuleType) -> bool:
        obj = getattr(module, symbol)
        if obj is None:
            return True
        else:
            defining_module = inspect.getmodule(obj)
            return defining_module is not module

    @staticmethod
    def _ignore_symbol(symbol: str, module: ModuleType, module_name: str):
        _SYMBOLS_TO_IGNORE = {
            "ActuationVecSpec"
        }
        return (symbol.startswith("_") or (symbol in _SYMBOLS_TO_IGNORE) or
                (module_name != "package" and HabitatProxyTest._is_imported_symbol(symbol, module)))

    @staticmethod
    def _assert_symbols_match(impl_module: ModuleType, proxy_module: ModuleType, module_name: str):
        """Helper to verify that proxy module exports the same symbols as impl module."""
        impl_symbols = {s for s in dir(impl_module) if
                        not HabitatProxyTest._ignore_symbol(s, impl_module, module_name)}
        proxy_symbols = {s for s in dir(proxy_module) if
                         not HabitatProxyTest._ignore_symbol(s, proxy_module, module_name)}

        missing_in_proxy = impl_symbols - proxy_symbols
        extra_in_proxy = proxy_symbols - impl_symbols

        assert missing_in_proxy == set(), (
            f"Proxy {module_name} is missing symbols from impl {module_name}: "
            f"{missing_in_proxy}"
        )
        assert extra_in_proxy == set(), (
            f"Proxy {module_name} has extra symbols not in impl {module_name}: "
            f"{extra_in_proxy}"
        )

    @staticmethod
    def _assert_callable_signatures_match(impl_module: ModuleType,
                                          proxy_module: ModuleType,
                                          module_name: str):
        """
        Helper to verify that callable signatures match between habitat_impl and proxy modules.
        This checks both module-level callables AND public methods of classes.
        """
        # Action classes decorated with @registry.register_move_fn have signatures
        # modified by the decorator in habitat_impl-sim, making exact matching impossible.
        # We skip signature verification for these but still check they exist.
        _DECORATOR_MODIFIED_ACTIONS = {
            "SetYaw",
            "SetSensorPitch",
            "SetAgentPitch",
            "SetSensorPose",
            "SetSensorRotation",
            "SetAgentPose",
        }

        impl_symbols = dir(impl_module)

        mismatches = []
        missing_callables = []

        for symbol in impl_symbols:

            if ((HabitatProxyTest._ignore_symbol(symbol, impl_module, module_name) or
                 symbol in _DECORATOR_MODIFIED_ACTIONS)):
                continue

            impl_obj = getattr(impl_module, symbol)
            if not callable(impl_obj):
                continue

            proxy_obj = getattr(proxy_module, symbol)
            if proxy_obj is None or not callable(proxy_obj):
                missing_callables.append(symbol)
                continue

            if callable(proxy_obj):
                try:
                    impl_sig = inspect.signature(impl_obj)
                    proxy_sig = inspect.signature(proxy_obj)

                    if impl_sig != proxy_sig:
                        # Special case: dataclass signatures may differ only in default class
                        # references
                        # (e.g., habitat_impl.implEnvironment vs habitat_proxy.implEnvironment)
                        # Check if they match structurally (param names, types, annotations)
                        if not HabitatProxyTest._signatures_match_structurally(
                                impl_sig,
                                proxy_sig,
                                module_name):
                            mismatches.append(
                                f"{symbol}: impl{impl_sig} != proxy{proxy_sig}"
                            )
                except (ValueError, TypeError):
                    pass

                # If it's a class, also check its public methods
                if inspect.isclass(impl_obj) and inspect.isclass(proxy_obj):
                    HabitatProxyTest._check_class_methods(
                        impl_obj, proxy_obj, symbol, mismatches, missing_callables
                    )

        assert missing_callables == [], (
            f"Proxy {module_name} is missing callables from habitat_impl {module_name}: "
            f"{missing_callables}"
        )
        assert mismatches == [], (
                f"{module_name} signature mismatches found:\n" + "\n".join(mismatches)
        )

    @staticmethod
    def _signatures_match_structurally(impl_sig: inspect.Signature,
                                       proxy_sig: inspect.Signature,
                                       module_name: str):
        """Check if two signatures match structurally, allowing parallel class defaults.
        This handles cases where dataclass default values reference parallel classes
        (e.g., habitat_impl.habitat_implEnvironment vs habitat_proxy.habitat_implEnvironment).
        """
        # Compare parameters
        i_params = list(impl_sig.parameters.values())
        p_params = list(proxy_sig.parameters.values())

        if len(i_params) != len(p_params):
            return False

        for i_param, p_param in zip(i_params, p_params):
            # Check parameter name
            if i_param.name != p_param.name:
                return False

            # Check annotation (type hint)
            if i_param.annotation != p_param.annotation:
                return False

            # Check kind (POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, etc.)
            if i_param.kind != p_param.kind:
                return False

            # For defaults, allow parallel class references
            i_default = i_param.default
            p_default = p_param.default

            if i_default is inspect.Parameter.empty and p_default is inspect.Parameter.empty:
                continue

            if i_default is inspect.Parameter.empty or p_default is inspect.Parameter.empty:
                return False

            # If defaults are classes with same name from parallel modules, accept
            if (inspect.isclass(i_default) and inspect.isclass(p_default) and
                    i_default.__name__ == p_default.__name__ and
                    'habitat_impl.environment' in getattr(i_default, '__module__', '') and
                    'habitat_proxy.environment' in getattr(p_default, '__module__', '')):
                continue

            # For other cases, defaults must match exactly
            if i_default != p_default:
                return False

        # Check return annotation
        if impl_sig.return_annotation != proxy_sig.return_annotation:
            return False

        return True

    @staticmethod
    def _check_class_methods(impl_class, proxy_class, class_name, mismatches, missing_callables):
        """Check that public methods of a class match between impl and proxy."""
        impl_methods = dir(impl_class)

        for method_name in impl_methods:
            # Skip private/protected methods
            if method_name.startswith('_'):
                continue

            impl_method = getattr(impl_class, method_name)

            # Only check callable methods (not properties, class vars, etc.)
            if not callable(impl_method):
                continue

            # Check if proxy has this method
            proxy_method = getattr(proxy_class, method_name, None)

            if proxy_method is None:
                missing_callables.append(f"{class_name}.{method_name}")
                continue

            if callable(proxy_method):
                try:
                    impl_sig = inspect.signature(impl_method)
                    proxy_sig = inspect.signature(proxy_method)

                    if impl_sig != proxy_sig:
                        mismatches.append(
                            f"{class_name}.{method_name}: impl{impl_sig} != proxy"
                            f"{proxy_sig}"
                        )
                except (ValueError, TypeError):
                    # Some methods may not have inspectable signatures (built-ins, etc.)
                    pass
