#!/usr/bin/env python3
"""
QC Clean Plugin Manager

Main plugin management interface that integrates the plugin registry,
discovery system, and configuration management.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .registry import PluginRegistry, PluginDiscovery
from .base import QCPlugin, PluginStatus
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import QCCleanConfigManager

logger = logging.getLogger(__name__)


class PluginManager:
    """Main plugin manager for QC Clean architecture"""
    
    def __init__(self, config_manager: Optional[QCCleanConfigManager] = None):
        """Initialize plugin manager"""
        self.config_manager = config_manager or QCCleanConfigManager()
        self.registry = PluginRegistry()
        self.discovery = PluginDiscovery(self.registry)
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.PluginManager")
    
    def initialize(self) -> bool:
        """Initialize the plugin system"""
        try:
            if self._initialized:
                self._logger.warning("Plugin system already initialized")
                return True
            
            self._logger.info("Initializing plugin system...")
            
            # Load configuration
            config = self.config_manager.load_config()
            
            # Auto-discover plugins if enabled
            if config.system.enable_auto_discovery:
                plugin_dir = Path(__file__).parent.parent / config.system.plugin_directory
                discovered = self.discovery.discover_plugins_in_directory(str(plugin_dir))
                self._logger.info(f"Auto-discovered {len(discovered)} plugins")
            
            # Auto-activate enabled plugins if configured
            if config.system.auto_activate:
                enabled_plugins = config.plugins.enabled_plugins
                activation_results = {}
                
                for plugin_name in enabled_plugins:
                    if plugin_name in self.registry.get_registered_plugins():
                        plugin_config = self.config_manager.get_plugin_config(plugin_name)
                        activation_results[plugin_name] = self.registry.activate_plugin(plugin_name, plugin_config)
                    else:
                        self._logger.warning(f"Enabled plugin '{plugin_name}' not found in registry")
                        activation_results[plugin_name] = False
                
                successful_activations = sum(1 for success in activation_results.values() if success)
                self._logger.info(f"Auto-activated {successful_activations}/{len(enabled_plugins)} enabled plugins")
            
            self._initialized = True
            self._logger.info("Plugin system initialization complete")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize plugin system: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown the plugin system"""
        try:
            if not self._initialized:
                return True
            
            self._logger.info("Shutting down plugin system...")
            
            # Deactivate all active plugins
            deactivation_results = self.registry.deactivate_all_plugins()
            successful_deactivations = sum(1 for success in deactivation_results.values() if success)
            
            self._logger.info(f"Deactivated {successful_deactivations}/{len(deactivation_results)} plugins")
            
            self._initialized = False
            self._logger.info("Plugin system shutdown complete")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to shutdown plugin system: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[QCPlugin]:
        """Get active plugin instance"""
        if not self._initialized:
            self._logger.warning("Plugin system not initialized")
            return None
        
        return self.registry.get_plugin_instance(plugin_name)
    
    def list_registered_plugins(self) -> List[Dict[str, Any]]:
        """Get list of all registered plugins with their info"""
        plugins = []
        for plugin_name in self.registry.get_registered_plugins():
            plugin_info = self.registry.get_plugin_info(plugin_name)
            if plugin_info:
                plugins.append(plugin_info)
        return plugins
    
    def list_active_plugins(self) -> List[str]:
        """Get list of active plugin names"""
        return self.registry.get_active_plugins()
    
    def activate_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Activate a specific plugin"""
        if not self._initialized:
            self._logger.error("Plugin system not initialized")
            return False
        
        plugin_config = config or self.config_manager.get_plugin_config(plugin_name)
        return self.registry.activate_plugin(plugin_name, plugin_config)
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate a specific plugin"""
        if not self._initialized:
            self._logger.error("Plugin system not initialized")
            return False
        
        return self.registry.deactivate_plugin(plugin_name)
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a specific plugin"""
        if not self._initialized:
            self._logger.error("Plugin system not initialized")
            return False
        
        # Deactivate and reactivate
        if plugin_name in self.registry.get_active_plugins():
            if not self.registry.deactivate_plugin(plugin_name):
                return False
        
        plugin_config = self.config_manager.get_plugin_config(plugin_name)
        return self.registry.activate_plugin(plugin_name, plugin_config)
    
    def discover_new_plugins(self) -> List[str]:
        """Discover new plugins in the plugin directory"""
        if not self._initialized:
            self._logger.error("Plugin system not initialized")
            return []
        
        plugin_dir = self.config_manager.get_plugin_directory()
        return self.discovery.discover_plugins_in_directory(plugin_dir)
    
    def get_plugin_status(self, plugin_name: str) -> Optional[PluginStatus]:
        """Get status of a specific plugin"""
        plugin_instance = self.registry.get_plugin_instance(plugin_name)
        if plugin_instance:
            return plugin_instance.get_status()
        
        # Check if plugin is registered but not active
        if plugin_name in self.registry.get_registered_plugins():
            return PluginStatus.UNINITIALIZED
        
        return None
    
    def validate_plugin_system(self) -> Dict[str, Any]:
        """Validate the plugin system configuration and state"""
        validation_result = {
            "system_initialized": self._initialized,
            "registered_plugins": len(self.registry.get_registered_plugins()),
            "active_plugins": len(self.registry.get_active_plugins()),
            "config_issues": [],
            "plugin_issues": []
        }
        
        try:
            # Validate configuration
            config = self.config_manager.load_config()
            enabled_plugins = config.plugins.enabled_plugins
            
            # Check if enabled plugins are registered
            registered_plugins = self.registry.get_registered_plugins()
            for plugin_name in enabled_plugins:
                if plugin_name not in registered_plugins:
                    validation_result["config_issues"].append(
                        f"Enabled plugin '{plugin_name}' not registered"
                    )
            
            # Check plugin states
            active_plugins = self.registry.get_active_plugins()
            for plugin_name in active_plugins:
                plugin_instance = self.registry.get_plugin_instance(plugin_name)
                if plugin_instance and plugin_instance.get_status() == PluginStatus.ERROR:
                    validation_result["plugin_issues"].append(
                        f"Plugin '{plugin_name}' in error state"
                    )
            
            validation_result["is_valid"] = (
                len(validation_result["config_issues"]) == 0 and
                len(validation_result["plugin_issues"]) == 0
            )
            
        except Exception as e:
            validation_result["config_issues"].append(f"Configuration validation error: {e}")
            validation_result["is_valid"] = False
        
        return validation_result
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()