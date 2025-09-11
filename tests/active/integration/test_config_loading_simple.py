"""
Simple test for validation config loading without async dependencies.

This test verifies that the validation configuration system works
without requiring Neo4j or other external dependencies.
"""

import pytest
import tempfile
from pathlib import Path

def test_validation_config_manager_creation():
    """Test that ValidationConfigManager can be created"""
    from src.qc.validation.config_manager import ValidationConfigManager
    
    manager = ValidationConfigManager()
    assert manager is not None
    assert hasattr(manager, 'config_dir')
    assert isinstance(manager.config_dir, Path)

def test_default_config_creation():
    """Test creation of default validation configurations"""
    from src.qc.validation.config_manager import ValidationConfigManager
    
    # Use temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create manager with temp directory
        manager = ValidationConfigManager()
        # Override config directory for testing
        manager.config_dir = Path(temp_dir) / "validation"
        # Ensure directory exists
        manager.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default configs
        manager.create_default_configs()
        
        # Verify configs were created
        configs = manager.list_configs()
        assert len(configs) >= 2  # Should have at least academic and hybrid
        
        # Check specific configs exist
        expected_configs = ['academic_research', 'hybrid_default']
        for expected in expected_configs:
            assert expected in configs, f"Expected config '{expected}' not found"

def test_config_loading():
    """Test loading specific validation configurations"""
    from src.qc.validation.config_manager import ValidationConfigManager
    from src.qc.validation.validation_config import ValidationMode
    
    # Use temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ValidationConfigManager()
        manager.config_dir = Path(temp_dir) / "validation"
        # Ensure directory exists
        manager.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default configs
        manager.create_default_configs()
        
        # Test loading academic config
        academic_config = manager.load_config("academic_research")
        assert academic_config is not None
        assert academic_config.entities == ValidationMode.CLOSED
        assert academic_config.relationships == ValidationMode.CLOSED
        
        # Test loading hybrid config
        hybrid_config = manager.load_config("hybrid_default")
        assert hybrid_config is not None
        assert hybrid_config.entities == ValidationMode.HYBRID
        assert hybrid_config.relationships == ValidationMode.HYBRID

def test_config_validation():
    """Test configuration file validation"""
    from src.qc.validation.config_manager import ValidationConfigManager
    
    # Use temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ValidationConfigManager()
        manager.config_dir = Path(temp_dir) / "validation"
        # Ensure directory exists
        manager.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default configs
        manager.create_default_configs()
        
        # Test validation of existing config
        result = manager.validate_config_file("academic_research")
        assert result['valid'] is True
        assert isinstance(result['errors'], list)
        assert isinstance(result['warnings'], list)
        assert isinstance(result['suggestions'], list)

def test_validation_config_objects():
    """Test ValidationConfig object creation and properties"""
    from src.qc.validation.validation_config import ValidationConfig, ValidationMode
    
    # Test default config
    config = ValidationConfig()
    assert config is not None
    assert hasattr(config, 'entities')
    assert hasattr(config, 'relationships')
    
    # Test academic config
    academic = ValidationConfig.academic_research_config()
    assert academic.entities == ValidationMode.CLOSED
    assert academic.relationships == ValidationMode.CLOSED
    assert academic.quality_threshold >= 0.8
    
    # Test production config
    production = ValidationConfig.production_research_config()
    assert production is not None
    assert production.auto_merge_similar is True
    
    # Test exploratory config
    exploratory = ValidationConfig.exploratory_research_config()
    assert exploratory.entities == ValidationMode.OPEN
    assert exploratory.relationships == ValidationMode.OPEN

def test_validation_modes():
    """Test ValidationMode enum values"""
    from src.qc.validation.validation_config import ValidationMode
    
    # Test enum values exist
    assert ValidationMode.OPEN is not None
    assert ValidationMode.CLOSED is not None
    assert ValidationMode.HYBRID is not None
    
    # Test string values
    assert ValidationMode.OPEN.value == "open"
    assert ValidationMode.CLOSED.value == "closed"
    assert ValidationMode.HYBRID.value == "hybrid"

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])