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

import inspect

import tbp.monty.simulators.habitat as habitat
import tbp.monty.simulators.habitat_proxy as habitat_proxy
from tbp.monty.simulators.habitat import configs as habitat_configs
from tbp.monty.simulators.habitat import environment as habitat_environment
from tbp.monty.simulators.habitat_proxy import configs as proxy_configs
from tbp.monty.simulators.habitat_proxy import environment as proxy_environment


def test_proxy_exports_same_symbols_as_habitat():
    _assert_symbols_match(habitat, habitat_proxy, "package")
    _assert_symbols_match(habitat_environment, proxy_environment, "environment")
    _assert_symbols_match(habitat_configs, proxy_configs, "configs")


def test_proxy_callables_have_matching_signatures():
    _assert_callable_signatures_match(habitat, habitat_proxy, "package")
    _assert_callable_signatures_match(habitat_environment, proxy_environment, "environment")
    _assert_callable_signatures_match(habitat_configs, proxy_configs, "configs")


def test_proxy_classes_come_from_proxy_modules():
    _assert_classes_from_proxy(habitat, habitat_proxy, "package", "habitat_proxy")
    _assert_classes_from_proxy(habitat_environment, proxy_environment, "environment", "habitat_proxy.environment")
    _assert_classes_from_proxy(habitat_configs, proxy_configs, "configs", "habitat_proxy.configs")


def _assert_symbols_match(habitat_module, proxy_module, module_name):
    """Helper to verify that proxy module exports the same symbols as habitat module."""
    habitat_symbols = set(dir(habitat_module))
    proxy_symbols = set(dir(proxy_module))

    # Filter out _habitat_* symbols from proxy - these are internal delegation imports
    proxy_symbols_public = {s for s in proxy_symbols if not s.startswith('_habitat_')}

    missing_in_proxy = habitat_symbols - proxy_symbols_public
    extra_in_proxy = proxy_symbols_public - habitat_symbols

    assert missing_in_proxy == set(), (
        f"Proxy {module_name} is missing symbols from habitat {module_name}: {missing_in_proxy}"
    )
    assert extra_in_proxy == set(), (
        f"Proxy {module_name} has extra symbols not in habitat {module_name}: {extra_in_proxy}"
    )


def _assert_callable_signatures_match(habitat_module, proxy_module, module_name):
    """Helper to verify that callable signatures match between habitat and proxy modules.

    This checks both module-level callables AND public methods of classes.
    """
    habitat_symbols = dir(habitat_module)

    mismatches = []
    missing_callables = []

    for symbol_name in habitat_symbols:
        if symbol_name.startswith('_'):
            continue

        habitat_attr = getattr(habitat_module, symbol_name)

        if not callable(habitat_attr):
            continue

        proxy_attr = getattr(proxy_module, symbol_name, None)

        if proxy_attr is None:
            missing_callables.append(symbol_name)
            continue

        if callable(proxy_attr):
            try:
                habitat_sig = inspect.signature(habitat_attr)
                proxy_sig = inspect.signature(proxy_attr)

                if habitat_sig != proxy_sig:
                    mismatches.append(
                        f"{symbol_name}: habitat{habitat_sig} != proxy{proxy_sig}"
                    )
            except (ValueError, TypeError):
                pass

            # If it's a class, also check its public methods
            if inspect.isclass(habitat_attr) and inspect.isclass(proxy_attr):
                _check_class_methods(
                    habitat_attr, proxy_attr, symbol_name, mismatches, missing_callables
                )

    assert missing_callables == [], (
        f"Proxy {module_name} is missing callables from habitat {module_name}: {missing_callables}"
    )
    assert mismatches == [], (
        f"{module_name} signature mismatches found:\n" + "\n".join(mismatches)
    )


def _check_class_methods(habitat_class, proxy_class, class_name, mismatches, missing_callables):
    """Check that public methods of a class match between habitat and proxy."""
    habitat_methods = dir(habitat_class)

    for method_name in habitat_methods:
        # Skip private/protected methods
        if method_name.startswith('_'):
            continue

        habitat_method = getattr(habitat_class, method_name)

        # Only check callable methods (not properties, class vars, etc.)
        if not callable(habitat_method):
            continue

        # Check if proxy has this method
        proxy_method = getattr(proxy_class, method_name, None)

        if proxy_method is None:
            missing_callables.append(f"{class_name}.{method_name}")
            continue

        if callable(proxy_method):
            try:
                habitat_sig = inspect.signature(habitat_method)
                proxy_sig = inspect.signature(proxy_method)

                if habitat_sig != proxy_sig:
                    mismatches.append(
                        f"{class_name}.{method_name}: habitat{habitat_sig} != proxy{proxy_sig}"
                    )
            except (ValueError, TypeError):
                # Some methods may not have inspectable signatures (built-ins, etc.)
                pass


def _assert_classes_from_proxy(habitat_module, proxy_module, module_name, expected_proxy_module_prefix):
    """Verify that classes in proxy module come from proxy, not original habitat.

    This catches cases where proxy modules accidentally import classes from the
    original habitat package instead of from the proxy package.
    """
    # Known external modules that are OK to come from outside habitat_proxy
    external_allowlist = {
        'tbp.monty.frameworks',
        'dataclasses',
        'typing',
        'typing_extensions',
        '__builtin__',
        'builtins',
        'os',
    }

    habitat_module_name = habitat_module.__name__
    proxy_symbols = dir(proxy_module)
    habitat_symbols = set(dir(habitat_module))

    wrong_origin = []

    for symbol_name in proxy_symbols:
        if symbol_name.startswith('_'):
            continue

        # Only check symbols that are also in habitat (i.e., should be proxied)
        if symbol_name not in habitat_symbols:
            continue

        proxy_attr = getattr(proxy_module, symbol_name)

        # Only check classes
        if not isinstance(proxy_attr, type):
            continue

        # Check where the class is defined
        if hasattr(proxy_attr, '__module__'):
            attr_module = proxy_attr.__module__

            # Check if it's from an allowed external module
            is_external = any(attr_module.startswith(ext) for ext in external_allowlist)
            if is_external:
                continue

            # Check if it's from habitat_proxy (correct) or habitat (wrong)
            if 'habitat_proxy' not in attr_module:
                # It's not from proxy - check if it's from the original habitat
                if 'habitat' in attr_module and 'habitat_proxy' not in attr_module:
                    wrong_origin.append(
                        f"{symbol_name}: comes from {attr_module}, "
                        f"should be from module containing '{expected_proxy_module_prefix}'"
                    )

    assert wrong_origin == [], (
        f"Proxy {module_name} has classes from wrong origin (should import from proxy, not habitat):\n"
        + "\n".join(wrong_origin)
    )



