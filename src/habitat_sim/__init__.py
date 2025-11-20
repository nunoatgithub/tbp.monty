# Copyright 2025 Thousand Brains Project
# Copyright 2021-2024 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import pickle
import socket
import sys
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
from types import ModuleType

# Register the proxy module as 'habitat_sim' in sys.modules so all imports are routed through the proxy.
sys.modules["habitat_sim"] = sys.modules[__name__]

class Client:
    """Handles communication with a remote module server."""
    def __init__(self, host='localhost', port=9998):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def send_request(self, request):
        import threading
        data = pickle.dumps(request)
        self.socket.send(len(data).to_bytes(4, 'big') + data)
        length_data = self.socket.recv(4)
        length = int.from_bytes(length_data, 'big')
        response_data = self.socket.recv(length)

        # Set flag to prevent __getattr__ calls during unpickling
        threading.current_thread()._in_pickle_loads = True
        try:
            response = pickle.loads(response_data)
        finally:
            threading.current_thread()._in_pickle_loads = False

        if isinstance(response, dict) and 'error' in response:
            raise Exception(f"{response['type']}: {response['error']}\n{response.get('traceback', '')}")
        return response

# ---- AUTO-PROXY START ----
class _ProxyModule(ModuleType):
    """Proxy module that dynamically proxies submodules and classes from the remote server.

    It presents itself as a package (PEP 451) so that Python's import machinery can
    resolve dotted imports without requiring explicit stub submodules in this file.
    """

    def __init__(self, name, client, parent=None):
        # Initialize as a normal module
        super().__init__(name)
        self._proxy_name = name
        self._proxy_client = client
        self._proxy_parent = parent
        # Make this module look like a namespace package so that it can have
        # submodules discovered by the import system.
        self.__path__ = []  # type: ignore[attr-defined]
        self.__package__ = name

    @staticmethod
    def _handle_class_attr(client, class_name, name):
        """Handle attribute access for proxied classes."""
        # Special attributes that don't exist on classes (only on modules)
        if name in ('__file__', '__path__', '__spec__', '__loader__', '__cached__', '__builtins__'):
            raise AttributeError(f"type object '{class_name}' has no attribute '{name}'")

        response = client.send_request(
            {'action': 'get_class_attr', 'class_name': class_name, 'name': name})
        if isinstance(response, dict) and "__proxy_id__" in response:
            return _AutoProxy(client, response["__proxy_id__"])
        elif callable(response):
            def call(*args, **kwargs):
                return client.send_request(
                    {'action': 'call_class_method', 'class_name': class_name, 'method': name,
                     'args': args, 'kwargs': kwargs})
            return call
        else:
            return response

    def _proxy_submodule(self, fullname):
        """Create, register, and return a proxy submodule for ``fullname``."""
        mod = sys.modules.get(fullname)
        if isinstance(mod, _ProxyModule):
            return mod
        mod = _ProxyModule(fullname, self._proxy_client, parent=self)
        # Mark submodules as namespace packages too
        mod.__path__ = []  # type: ignore[attr-defined]
        mod.__package__ = fullname
        sys.modules[fullname] = mod
        # Attach to parent so attribute access also works
        parent_name, _, child_name = fullname.rpartition(".")
        parent = sys.modules.get(parent_name, self)
        setattr(parent, child_name, mod)
        return mod

    def _proxy_class(self, name, fullname, doc=None):
        """Create a proxy class for a remote class."""
        client = self._proxy_client
        proxy_cls = type(name, (), {
            "__module__": self.__name__,
            "__doc__": doc or '',
            "__call__": lambda *args, **kwargs: _AutoProxy(client, client.send_request({'action': 'create', 'class_name': fullname, 'args': args, 'kwargs': kwargs})),
            "__getattr__": lambda self, n: _ProxyModule._handle_class_attr(client, fullname, n)
        })
        setattr(self, name, proxy_cls)
        return proxy_cls

    def _query_server_type(self, fullname):
        """Query the server for the type of a name (module/class/etc)."""
        return self._proxy_client.send_request({'action': 'get_type', 'name': fullname})

    def __getattr__(self, name):
        import threading

        # If we're in pickle.loads, don't try to query the server
        if getattr(threading.current_thread(), '_in_pickle_loads', False):
            raise AttributeError(f"module '{self.__name__}' has no attribute '{name}'")

        if not hasattr(threading.current_thread(), '_getattr_depth'):
            threading.current_thread()._getattr_depth = 0

        if threading.current_thread()._getattr_depth > 10:
            raise AttributeError(f"module '{self.__name__}' has no attribute '{name}'")

        threading.current_thread()._getattr_depth += 1
        try:
            # Build fully qualified name: parent.child
            fullname = f"{self.__name__}.{name}"

            existing = sys.modules.get(fullname)
            if isinstance(existing, _ProxyModule):
                return existing

            response = self._query_server_type(fullname)
        finally:
            threading.current_thread()._getattr_depth -= 1

        if response.get("type") == "module":
            return self._proxy_submodule(fullname)
        elif response.get("type") == "attribute":
            value = response.get("value")
            # Check if the value is a proxy reference
            if isinstance(value, dict) and "__proxy_id__" in value:
                return _AutoProxy(self._proxy_client, value["__proxy_id__"])
            return value

        try:
            value = super().__getattribute__(name)
            if isinstance(value, type):
                mod = getattr(value, "__module__", "")
                if mod == __name__ or mod.startswith(__name__ + "."):
                    return self._proxy_class(value.__name__, value.__name__, value.__doc__)
            return value
        except AttributeError:
            if response.get("type") == "class":
                return self._proxy_class(name, fullname, response.get("doc", ""))
            elif response.get("type") == "not_found":
                raise AttributeError(f"module '{self.__name__}' has no attribute '{name}'")
            else:
                raise AttributeError(f"'{name}' is not a proxyable class or module")

class _AutoProxy:
    """Proxy for remote objects/classes."""
    __slots__ = ("_client", "_id")

    def __init__(self, client, id):
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "_id", id)

    def _remote_getattr(self, name):
        attr = self._client.send_request({'action': 'getattr', 'id': self._id, 'name': name})
        if isinstance(attr, dict) and "__proxy_id__" in attr:
            return _AutoProxy(self._client, attr["__proxy_id__"])
        elif callable(attr):
            def call(*args, **kwargs):
                return self._client.send_request(
                    {'action': 'call', 'id': self._id, 'method': name, 'args': args,
                     'kwargs': kwargs})
            return call
        else:
            return attr

    def __getattr__(self, name):
        return self._remote_getattr(name)

    def __setattr__(self, name, value):
        if name in ('_client', '_id'):
            object.__setattr__(self, name, value)
        else:
            self._client.send_request(
                {'action': 'setattr', 'id': self._id, 'name': name, 'value': value})

    def __repr__(self):
        return f"{self.__class__.__name__}({self._id})"

    def __dir__(self):
        return self._client.send_request({'action': 'dir', 'id': self._id})


class _ProxyModuleFinder(MetaPathFinder):
    """Import hook that intercepts submodule imports for a proxied module."""

    def __init__(self, root_module_name, client):
        self.root_module_name = root_module_name
        self.client = client

    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith(self.root_module_name):
            return None

        # Check with server if this is actually a module
        response = self.client.send_request({'action': 'get_type', 'name': fullname})
        if response.get('type') == 'module':
            return ModuleSpec(fullname, _ProxyModuleLoader(self.client), is_package=True)

        # Not a module (could be a class, attribute, or not found)
        return None


class _ProxyModuleLoader(Loader):
    """Loader that creates _ProxyModule instances for submodules."""

    def __init__(self, client):
        self.client = client

    def create_module(self, spec):
        if spec.name in sys.modules:
            return sys.modules[spec.name]
        # Create a new proxy module
        mod = _ProxyModule(spec.name, self.client)
        return mod

    def exec_module(self, module):
        # Module is already initialized by _ProxyModule.__init__
        pass


# ---- HABITAT_SIM PROXY SETUP ----
# This is the only place where "habitat_sim" is hardcoded - everything above is generic

# Create client connection to the remote server
client = Client()

# Install the import hook for this module
sys.meta_path.insert(0, _ProxyModuleFinder('habitat_sim', client))

# Turn this module object into a _ProxyModule
proxy_root = sys.modules[__name__]
proxy_root.__class__ = _ProxyModule
_ProxyModule.__init__(proxy_root, __name__, client)
proxy_root.__path__ = []
proxy_root.__package__ = 'habitat_sim'

sys.modules['habitat_sim'] = proxy_root

# ---- AUTO-PROXY END ----
