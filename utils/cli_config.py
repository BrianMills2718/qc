#!/usr/bin/env python3
"""
CLI Configuration Management
Handles configuration files, argument parsing integration, and validation
"""

import yaml
import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


@dataclass
class AnalysisConfig:
    """Configuration for qualitative analysis"""
    
    # Input/Output Settings
    input_dir: Optional[str] = None
    input_file: Optional[str] = None
    output_dir: str = "./output"
    output_format: str = "markdown"  # markdown, json, csv
    
    # Analysis Settings
    session_name: Optional[str] = None
    model: str = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    confidence_threshold: float = 0.7
    max_quotes_per_code: int = 5
    
    # Processing Options
    batch_process: bool = False
    verbose: bool = False
    quiet: bool = False
    dry_run: bool = False
    
    # Advanced Settings
    prompt_template: Optional[str] = None
    
    # File Processing
    supported_extensions: List[str] = field(default_factory=lambda: ['.txt', '.docx'])
    max_file_size_mb: int = 10
    
    # Qualitative Coding Settings
    coding_mode: str = "HYBRID"  # OPEN, CLOSED, HYBRID
    generate_policy_brief: bool = True
    detect_contradictions: bool = True
    
    @classmethod
    def from_args(cls, args):
        """Create config from argparse arguments"""
        config = cls()
        
        # Map argparse namespace to config fields
        arg_dict = vars(args)
        
        for field_name in config.__dataclass_fields__:
            if field_name in arg_dict and arg_dict[field_name] is not None:
                setattr(config, field_name, arg_dict[field_name])
        
        # Load from config file if specified
        if hasattr(args, 'config') and args.config:
            config.load_from_file(args.config)
            
            # Command line args override config file
            for field_name in config.__dataclass_fields__:
                if field_name in arg_dict and arg_dict[field_name] is not None:
                    setattr(config, field_name, arg_dict[field_name])
        
        # Generate session name if not provided
        if not config.session_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            config.session_name = f"Analysis_{timestamp}"
        
        return config
    
    @classmethod
    def from_file(cls, config_path: str):
        """Create config from file"""
        config = cls()
        config.load_from_file(config_path)
        return config
    
    def load_from_file(self, config_path: str):
        """Load configuration from YAML or JSON file"""
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {path.suffix}. Use .yaml, .yml, or .json")
            
            if not data:
                raise ValueError(f"Configuration file is empty: {config_path}")
            
            # Update config with file data
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    print(f"Warning: Unknown configuration key '{key}' ignored")
                    
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")
    
    def save_to_file(self, config_path: str):
        """Save configuration to file"""
        path = Path(config_path)
        
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary, excluding None values
        data = {}
        for key, value in asdict(self).items():
            if value is not None:
                data[key] = value
        
        # Add metadata
        data['_metadata'] = {
            'created_by': 'qualitative-coding-cli',
            'created_at': datetime.now().isoformat(),
            'version': '2.1.0'
        }
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(data, f, default_flow_style=False, indent=2, sort_keys=True)
                elif path.suffix.lower() == '.json':
                    json.dump(data, f, indent=2, sort_keys=True)
                else:
                    # Default to YAML
                    path = path.with_suffix('.yaml')
                    yaml.dump(data, f, default_flow_style=False, indent=2, sort_keys=True)
        except Exception as e:
            raise ValueError(f"Error saving config file: {e}")
    
    def validate(self):
        """Validate configuration settings"""
        errors = []
        warnings = []
        
        # Input validation
        if not self.input_dir and not self.input_file:
            errors.append("Must specify either input_dir or input_file")
        
        if self.input_dir and not Path(self.input_dir).exists():
            errors.append(f"Input directory does not exist: {self.input_dir}")
        
        if self.input_file and not Path(self.input_file).exists():
            errors.append(f"Input file does not exist: {self.input_file}")
        
        # Validate numeric ranges
        if not 0 <= self.confidence_threshold <= 1:
            errors.append("confidence_threshold must be between 0 and 1")
        
        if self.max_quotes_per_code < 1:
            errors.append("max_quotes_per_code must be >= 1")
        
        if self.max_file_size_mb < 1:
            errors.append("max_file_size_mb must be >= 1")
        
        # Validate choices
        valid_formats = ['markdown', 'json', 'csv']
        if self.output_format not in valid_formats:
            errors.append(f"output_format must be one of: {', '.join(valid_formats)}")
        
        # Model validation removed - trust .env configuration
        
        # Environment checks
        if not os.getenv('GEMINI_API_KEY'):
            warnings.append("GEMINI_API_KEY environment variable not set")
        
        # Output validation
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create output directory '{self.output_dir}': {e}")
        
        
        # Report errors and warnings
        if warnings:
            print("⚠️  Configuration warnings:")
            for warning in warnings:
                print(f"   • {warning}")
        
        if errors:
            error_msg = "Configuration errors:\n" + "\n".join(f"   • {error}" for error in errors)
            raise ValueError(error_msg)
        
        return True
    
    def get_file_list(self) -> List[Path]:
        """Get list of files to process based on configuration"""
        files = []
        
        if self.input_file:
            files = [Path(self.input_file)]
        elif self.input_dir:
            input_path = Path(self.input_dir)
            for ext in self.supported_extensions:
                files.extend(input_path.glob(f"*{ext}"))
        
        # Filter by file size
        max_size = self.max_file_size_mb * 1024 * 1024
        valid_files = []
        
        for file in files:
            if file.exists():
                if file.stat().st_size <= max_size:
                    valid_files.append(file)
                else:
                    print(f"⚠️  Skipping large file: {file.name} ({file.stat().st_size / 1024 / 1024:.1f}MB > {self.max_file_size_mb}MB)")
        
        return valid_files
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding None values)"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def __str__(self) -> str:
        """String representation for debugging"""
        lines = ["AnalysisConfig:"]
        for key, value in asdict(self).items():
            if value is not None:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)


def create_sample_config(output_path: str = "analysis_config.yaml"):
    """Create a sample configuration file with documentation"""
    config = AnalysisConfig(
        session_name="Remote Work Study - Wave 1",
        model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
        confidence_threshold=0.8,
        max_quotes_per_code=3,
        output_format="markdown",
        verbose=True
    )
    
    # Add comments as a separate structure
    config_with_comments = {
        # Core settings
        'session_name': config.session_name,
        'model': config.model,
        'output_format': config.output_format,
        
        # Analysis parameters
        'confidence_threshold': config.confidence_threshold,
        'max_quotes_per_code': config.max_quotes_per_code,
        
        # Processing options
        'verbose': config.verbose,
        'max_file_size_mb': config.max_file_size_mb,
        
        # Qualitative Coding
        'coding_mode': config.coding_mode,
        'generate_policy_brief': config.generate_policy_brief,
        'detect_contradictions': config.detect_contradictions,
        
        # Documentation
        '_comments': {
            'session_name': 'Descriptive name for your analysis session',
            'model': 'LLM model: configured via GEMINI_MODEL environment variable',
            'output_format': 'Output format: markdown, json, or csv',
            'confidence_threshold': 'Minimum confidence for including codes (0.0-1.0)',
            'max_quotes_per_code': 'Maximum supporting quotes per code',
            'verbose': 'Show detailed progress information',
            'coding_mode': 'Qualitative coding approach: OPEN, CLOSED, or HYBRID',
            'generate_policy_brief': 'Generate actionable policy recommendations',
            'detect_contradictions': 'Flag contradictory findings across interviews'
        }
    }
    
    # Save with comments
    with open(output_path, 'w') as f:
        f.write("# Qualitative Coding Analysis Configuration\n")
        f.write("# Generated by CLI tool - modify as needed\n\n")
        
        # Write main config
        yaml.dump({k: v for k, v in config_with_comments.items() if not k.startswith('_')}, 
                 f, default_flow_style=False, indent=2)
        
        f.write("\n# Configuration Guide:\n")
        for key, comment in config_with_comments['_comments'].items():
            f.write(f"# {key}: {comment}\n")
    
    print(f"✅ Sample configuration created: {output_path}")


# CLI helper functions
def load_config_with_fallback(config_path: Optional[str] = None) -> AnalysisConfig:
    """Load config with fallback to default locations"""
    search_paths = []
    
    if config_path:
        search_paths.append(config_path)
    
    # Default search paths
    search_paths.extend([
        'analysis_config.yaml',
        'analysis_config.yml', 
        'config.yaml',
        'config.yml',
        '~/.qualitative_coding.yaml',
        '~/.qualitative_coding.yml'
    ])
    
    for path in search_paths:
        expanded_path = Path(path).expanduser()
        if expanded_path.exists():
            print(f"📋 Loading configuration from: {expanded_path}")
            return AnalysisConfig.from_file(str(expanded_path))
    
    # No config file found, use defaults
    print("📋 Using default configuration (no config file found)")
    return AnalysisConfig()


if __name__ == "__main__":
    # Test configuration functionality
    print("🧪 Testing Configuration Management")
    
    # Create sample config
    create_sample_config("test_config.yaml")
    
    # Load and validate
    config = AnalysisConfig.from_file("test_config.yaml")
    print(f"\n✅ Loaded configuration:")
    print(config)
    
    # Test validation
    try:
        config.validate()
        print("\n✅ Configuration validation passed")
    except ValueError as e:
        print(f"\n❌ Configuration validation failed: {e}")
    
    print(f"\n🎉 Configuration management ready!")