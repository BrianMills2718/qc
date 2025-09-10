#!/usr/bin/env python3
"""
QC Clean Configuration Manager

Simplified configuration management for the QC Clean architecture.
Handles core system configuration and plugin configurations.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SystemConfig:
    """Core system configuration"""
    methodology: str
    neo4j_uri: str
    database_name: str
    enable_auto_discovery: bool
    plugin_directory: str
    auto_activate: bool


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str
    model: str
    api_timeout: int


@dataclass
class GTWorkflowConfig:
    """Grounded Theory workflow configuration"""
    theoretical_sensitivity: str
    coding_depth: str
    enable_hierarchy: bool
    enable_memos: bool


@dataclass
class PluginConfig:
    """Plugin-specific configuration"""
    enabled_plugins: List[str]
    plugin_configs: Dict[str, Dict[str, Any]]


@dataclass
class QCCleanConfig:
    """Main QC Clean configuration"""
    system: SystemConfig
    llm: LLMConfig
    gt_workflow: GTWorkflowConfig
    plugins: PluginConfig
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> 'QCCleanConfig':
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Parse system config
            system_data = config_data.get('system', {})
            db_data = system_data.get('database', {})
            plugins_data = system_data.get('plugins', {})
            
            system_config = SystemConfig(
                methodology=system_data.get('methodology', 'grounded_theory'),
                neo4j_uri=db_data.get('neo4j_uri', 'bolt://localhost:7687'),
                database_name=db_data.get('database_name', 'qc_analysis'),
                enable_auto_discovery=plugins_data.get('enable_auto_discovery', True),
                plugin_directory=plugins_data.get('plugin_directory', 'plugins'),
                auto_activate=plugins_data.get('auto_activate', True)
            )
            
            # Parse LLM config
            llm_data = config_data.get('llm', {})
            llm_config = LLMConfig(
                provider=llm_data.get('provider', 'gemini'),
                model=llm_data.get('model', 'gemini-2.0-flash-exp'),
                api_timeout=llm_data.get('api_timeout', None)  # No timeout limits
            )
            
            # Parse GT workflow config
            gt_data = config_data.get('gt_workflow', {})
            gt_config = GTWorkflowConfig(
                theoretical_sensitivity=gt_data.get('theoretical_sensitivity', 'medium'),
                coding_depth=gt_data.get('coding_depth', 'focused'),
                enable_hierarchy=gt_data.get('enable_hierarchy', True),
                enable_memos=gt_data.get('enable_memos', False)
            )
            
            # Parse plugin config
            plugins_section = config_data.get('plugins', {})
            plugin_config = PluginConfig(
                enabled_plugins=plugins_section.get('enabled_plugins', []),
                plugin_configs=plugins_section.get('plugin_configs', {})
            )
            
            return cls(
                system=system_config,
                llm=llm_config,
                gt_workflow=gt_config,
                plugins=plugin_config
            )
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin"""
        return self.plugins.plugin_configs.get(plugin_name, {})
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled"""
        return plugin_name in self.plugins.enabled_plugins


class QCCleanConfigManager:
    """Configuration manager for QC Clean architecture"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager"""
        if config_path is None:
            # Default to qc_clean config directory
            self.config_path = Path(__file__).parent / 'qc_core.yaml'
        else:
            self.config_path = config_path
        
        self._config: Optional[QCCleanConfig] = None
        logger.info(f"QCCleanConfigManager initialized with config path: {self.config_path}")
    
    def load_config(self) -> QCCleanConfig:
        """Load and cache configuration"""
        if self._config is None:
            self._config = QCCleanConfig.from_yaml(self.config_path)
            logger.info(f"Loaded QC Clean configuration: {self._config.system.methodology} methodology")
        
        return self._config
    
    def reload_config(self) -> QCCleanConfig:
        """Force reload configuration"""
        self._config = None
        return self.load_config()
    
    def get_system_config(self) -> SystemConfig:
        """Get system configuration"""
        return self.load_config().system
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration"""
        return self.load_config().llm
    
    def get_gt_workflow_config(self) -> GTWorkflowConfig:
        """Get GT workflow configuration"""
        return self.load_config().gt_workflow
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin"""
        return self.load_config().get_plugin_config(plugin_name)
    
    def get_enabled_plugins(self) -> List[str]:
        """Get list of enabled plugins"""
        return self.load_config().plugins.enabled_plugins
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled"""
        return self.load_config().is_plugin_enabled(plugin_name)
    
    def get_plugin_directory(self) -> str:
        """Get plugin directory path"""
        return self.load_config().system.plugin_directory
    
    def should_auto_discover_plugins(self) -> bool:
        """Check if plugin auto-discovery is enabled"""
        return self.load_config().system.enable_auto_discovery
    
    def should_auto_activate_plugins(self) -> bool:
        """Check if plugin auto-activation is enabled"""
        return self.load_config().system.auto_activate