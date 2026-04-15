"""
Plugin Registry - External plugin discovery and loading

Inspired by claw-code's plugin system:
- Discover plugins from paths
- Plugin lifecycle management
- Tool registration from plugins
"""

from __future__ import annotations

import logging
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Plugin:
    """
    Plugin definition.

    Attributes:
        id: Unique plugin identifier
        name: Human-readable name
        version: Plugin version
        description: Plugin description
        tools: Tools provided by plugin
        on_load: Optional load callback
        on_unload: Optional unload callback
    """
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    tools: List[str] = field(default_factory=list)
    on_load: Callable = None
    on_unload: Callable = None


class PluginRegistry:
    """
    Plugin discovery and management.

    Discovers plugins from:
    - Built-in plugins
    - plugins/ directory
    - PYTHONPATH
    """

    def __init__(self, plugins_dir: str = None):
        self.plugins_dir = Path(plugins_dir or "./plugins")
        self.plugins: Dict[str, Plugin] = {}
        self._logger = logging.getLogger(__name__)

    def discover_plugins(self) -> int:
        """Discover plugins from directory"""
        if not self.plugins_dir.exists():
            return 0

        count = 0
        for plugin_path in self.plugins_dir.iterdir():
            if plugin_path.is_dir() and (plugin_path / "__init__.py").exists():
                try:
                    plugin = self._load_plugin(plugin_path)
                    if plugin:
                        self.plugins[plugin.id] = plugin
                        count += 1
                except Exception as e:
                    self._logger.warning(f"Failed to load plugin from {plugin_path}: {e}")

        return count

    def _load_plugin(self, plugin_path: Path) -> Optional[Plugin]:
        """Load a plugin module"""
        spec = importlib.util.spec_from_file_location(
            f"plugins.{plugin_path.name}",
            plugin_path / "__init__.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        if hasattr(module, "plugin"):
            return module.plugin
        return None

    def get(self, plugin_id: str) -> Optional[Plugin]:
        """Get plugin by ID"""
        return self.plugins.get(plugin_id)

    def list_plugins(self) -> List[Plugin]:
        """List all plugins"""
        return list(self.plugins.values())

    def enable(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        plugin = self.get(plugin_id)
        if plugin and plugin.on_load:
            plugin.on_load()
            return True
        return False

    def disable(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        plugin = self.get(plugin_id)
        if plugin and plugin.on_unload:
            plugin.on_unload()
            return True
        return False
