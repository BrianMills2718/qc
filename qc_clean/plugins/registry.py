#!/usr/bin/env python3
"""
QC Clean Plugin Registry and Discovery System

This module provides plugin registry functionality, discovery mechanisms,
and lifecycle management for QC Clean plugins.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Set
import logging
from collections import defaultdict

from .base import QCPlugin, PluginStatus, PluginInterface

logger = logging.getLogger(__name__)


class PluginDependencyError(Exception):
    """Raised when plugin dependencies cannot be satisfied"""
    pass


class PluginRegistry:
    """Central registry for QC Clean plugins"""
    
    def __init__(self, config_path: Optional[str] = None):
        self._registered_plugins: Dict[str, Type[QCPlugin]] = {}
        self._active_plugins: Dict[str, QCPlugin] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._load_order: List[str] = []
        self.config_path = config_path
        self._logger = logging.getLogger(f"{__name__}.PluginRegistry")
        
        # Load plugin configurations if provided
        if config_path and os.path.exists(config_path):
            self._load_plugin_configs(config_path)
    
    def register_plugin(self, plugin_class: Type[QCPlugin], force: bool = False) -> bool:
        """Register a plugin class"""
        try:
            # Create temporary instance to get plugin info
            temp_instance = plugin_class()
            plugin_name = temp_instance.get_name()
            
            # Check for duplicate registration
            if plugin_name in self._registered_plugins and not force:
                self._logger.warning(f"Plugin '{plugin_name}' already registered. Use force=True to override.")
                return False
            
            # Validate plugin interface
            missing_methods = PluginInterface.validate_plugin_interface(temp_instance)
            if missing_methods:
                self._logger.error(f"Plugin '{plugin_name}' missing required methods: {missing_methods}")
                return False
            
            # Register the plugin
            self._registered_plugins[plugin_name] = plugin_class
            self._dependency_graph[plugin_name] = set(temp_instance.get_dependencies())
            
            self._logger.info(f"Registered plugin: {plugin_name} v{temp_instance.get_version()}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to register plugin {plugin_class}: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a plugin"""
        try:
            if plugin_name in self._active_plugins:
                self.deactivate_plugin(plugin_name)
            
            if plugin_name in self._registered_plugins:
                del self._registered_plugins[plugin_name]
                if plugin_name in self._dependency_graph:
                    del self._dependency_graph[plugin_name]
                self._logger.info(f"Unregistered plugin: {plugin_name}")
                return True
            
            self._logger.warning(f"Plugin '{plugin_name}' not registered")
            return False
            
        except Exception as e:
            self._logger.error(f"Failed to unregister plugin '{plugin_name}': {e}")
            return False
    
    def get_registered_plugins(self) -> List[str]:
        """Get list of registered plugin names"""
        return list(self._registered_plugins.keys())
    
    def get_active_plugins(self) -> List[str]:
        """Get list of active plugin names"""
        return list(self._active_plugins.keys())
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered plugin"""
        if plugin_name not in self._registered_plugins:
            return None
        
        plugin_class = self._registered_plugins[plugin_name]
        temp_instance = plugin_class()
        
        return {
            "name": temp_instance.get_name(),
            "version": temp_instance.get_version(),
            "description": temp_instance.get_description(),
            "dependencies": temp_instance.get_dependencies(),
            "is_active": plugin_name in self._active_plugins,
            "status": self._active_plugins[plugin_name].get_status() if plugin_name in self._active_plugins else PluginStatus.UNINITIALIZED
        }
    
    def _resolve_load_order(self) -> List[str]:
        """Resolve plugin load order based on dependencies"""
        # Topological sort to handle dependencies
        visited = set()
        temp_visited = set()
        load_order = []
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                raise PluginDependencyError(f"Circular dependency detected involving plugin '{plugin_name}'")
            
            if plugin_name not in visited:
                temp_visited.add(plugin_name)
                
                # Visit dependencies first
                for dependency in self._dependency_graph.get(plugin_name, set()):
                    if dependency in self._registered_plugins:
                        visit(dependency)
                    else:
                        self._logger.warning(f"Plugin '{plugin_name}' depends on unregistered plugin '{dependency}'")
                
                temp_visited.remove(plugin_name)
                visited.add(plugin_name)
                load_order.append(plugin_name)
        
        # Visit all registered plugins
        for plugin_name in self._registered_plugins:
            if plugin_name not in visited:
                visit(plugin_name)
        
        return load_order
    
    def activate_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Activate a plugin"""
        try:
            if plugin_name not in self._registered_plugins:
                self._logger.error(f"Plugin '{plugin_name}' not registered")
                return False
            
            if plugin_name in self._active_plugins:
                self._logger.warning(f"Plugin '{plugin_name}' already active")
                return True
            
            # Get configuration
            plugin_config = config or self._plugin_configs.get(plugin_name, {})
            
            # Create plugin instance
            plugin_class = self._registered_plugins[plugin_name]
            plugin_instance = plugin_class()
            
            # Check if plugin is available
            if not plugin_instance.is_available():
                self._logger.error(f"Plugin '{plugin_name}' dependencies not available")
                return False
            
            # Initialize plugin
            if not plugin_instance.initialize(plugin_config):
                self._logger.error(f"Failed to initialize plugin '{plugin_name}'")
                return False
            
            # Mark as active
            plugin_instance.status = PluginStatus.ACTIVE
            self._active_plugins[plugin_name] = plugin_instance
            
            self._logger.info(f"Activated plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to activate plugin '{plugin_name}': {e}")
            return False
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate a plugin"""
        try:
            if plugin_name not in self._active_plugins:
                self._logger.warning(f"Plugin '{plugin_name}' not active")
                return True
            
            plugin_instance = self._active_plugins[plugin_name]
            
            # Cleanup plugin
            if plugin_instance.cleanup():
                del self._active_plugins[plugin_name]
                self._logger.info(f"Deactivated plugin: {plugin_name}")
                return True
            else:
                self._logger.error(f"Failed to cleanup plugin '{plugin_name}'")
                return False
                
        except Exception as e:
            self._logger.error(f"Failed to deactivate plugin '{plugin_name}': {e}")
            return False
    
    def get_plugin_instance(self, plugin_name: str) -> Optional[QCPlugin]:
        """Get active plugin instance"""
        return self._active_plugins.get(plugin_name)
    
    def activate_all_plugins(self) -> Dict[str, bool]:
        """Activate all registered plugins in dependency order"""
        results = {}
        
        try:
            # Resolve load order
            self._load_order = self._resolve_load_order()
            
            # Activate plugins in order
            for plugin_name in self._load_order:
                results[plugin_name] = self.activate_plugin(plugin_name)
            
            return results
            
        except PluginDependencyError as e:
            self._logger.error(f"Dependency error during bulk activation: {e}")
            # Deactivate any plugins that were activated
            for plugin_name in self._active_plugins.copy():
                self.deactivate_plugin(plugin_name)
            return {name: False for name in self._registered_plugins}
    
    def deactivate_all_plugins(self) -> Dict[str, bool]:
        """Deactivate all active plugins"""
        results = {}
        
        # Deactivate in reverse order
        for plugin_name in reversed(self._load_order):
            if plugin_name in self._active_plugins:
                results[plugin_name] = self.deactivate_plugin(plugin_name)
        
        return results
    
    def _load_plugin_configs(self, config_path: str) -> None:
        """Load plugin configurations from YAML file"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'plugin_configs' in config:
                self._plugin_configs = config['plugin_configs']
                self._logger.info(f"Loaded plugin configurations from {config_path}")
                
        except Exception as e:
            self._logger.error(f"Failed to load plugin configs from {config_path}: {e}")


class PluginDiscovery:
    """Plugin discovery system for automatic plugin loading"""
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._logger = logging.getLogger(f"{__name__}.PluginDiscovery")
    
    def discover_plugins_in_directory(self, directory: str, recursive: bool = True) -> List[str]:
        """Discover plugins in a directory"""
        discovered_plugins = []
        plugin_dir = Path(directory)
        
        if not plugin_dir.exists():
            self._logger.warning(f"Plugin directory does not exist: {directory}")
            return discovered_plugins
        
        # Search for Python files
        pattern = "**/*.py" if recursive else "*.py"
        python_files = plugin_dir.glob(pattern)
        
        for py_file in python_files:
            # Skip __init__.py and base.py files
            if py_file.name in ['__init__.py', 'base.py', 'registry.py']:
                continue
            
            plugin_name = self._load_plugin_from_file(py_file)
            if plugin_name:
                discovered_plugins.append(plugin_name)
        
        return discovered_plugins
    
    def _load_plugin_from_file(self, file_path: Path) -> Optional[str]:
        """Load a plugin from a Python file"""
        try:
            # Create module spec
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            
            if not spec or not spec.loader:
                self._logger.warning(f"Could not create spec for {file_path}")
                return None
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find plugin classes
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, QCPlugin) and 
                    attr != QCPlugin):
                    
                    # Register plugin
                    if self.registry.register_plugin(attr):
                        plugin_instance = attr()
                        plugin_name = plugin_instance.get_name()
                        self._logger.info(f"Discovered plugin '{plugin_name}' in {file_path}")
                        return plugin_name
            
            return None
            
        except Exception as e:
            self._logger.error(f"Failed to load plugin from {file_path}: {e}")
            return None
    
    def auto_discover_plugins(self, base_directory: str = "plugins") -> List[str]:
        """Automatically discover all plugins in the base directory"""
        discovered = []
        
        # Get absolute path to plugins directory
        if not os.path.isabs(base_directory):
            current_dir = Path(__file__).parent.parent
            plugin_dir = current_dir / base_directory
        else:
            plugin_dir = Path(base_directory)
        
        if plugin_dir.exists():
            discovered = self.discover_plugins_in_directory(str(plugin_dir))
            self._logger.info(f"Auto-discovered {len(discovered)} plugins")
        
        return discovered