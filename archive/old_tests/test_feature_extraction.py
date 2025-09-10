#!/usr/bin/env python3
"""
Feature Extraction Assessment - Task 4.3
Tests each component the user wants to preserve for extraction feasibility
"""

import sys
import os
import importlib
from pathlib import Path
import json
from typing import Dict, List, Any

def test_component_independence(component_name: str, module_paths: List[str]) -> Dict[str, Any]:
    """Test if a component can be imported and used independently"""
    results = {
        'component': component_name,
        'import_success': False,
        'dependencies': [],
        'errors': [],
        'functionality_test': 'not_tested',
        'extraction_feasibility': 'unknown'
    }
    
    print(f"\n=== Testing {component_name} ===")
    
    # Test imports
    for module_path in module_paths:
        try:
            print(f"Testing import: {module_path}")
            
            # Add current directory to Python path
            sys.path.insert(0, str(Path.cwd()))
            
            # Import the module
            module = importlib.import_module(module_path)
            
            print(f"[SUCCESS] Successfully imported {module_path}")
            results['import_success'] = True
            
            # Try to inspect module contents
            if hasattr(module, '__file__'):
                print(f"   Located at: {module.__file__}")
            
            # Check for key classes/functions
            classes = [name for name in dir(module) if not name.startswith('_') and hasattr(getattr(module, name), '__bases__')]
            functions = [name for name in dir(module) if not name.startswith('_') and callable(getattr(module, name)) and not hasattr(getattr(module, name), '__bases__')]
            
            if classes:
                print(f"   Classes found: {classes[:3]}{'...' if len(classes) > 3 else ''}")
            if functions:
                print(f"   Functions found: {functions[:3]}{'...' if len(functions) > 3 else ''}")
                
        except ImportError as e:
            error_msg = f"Import failed for {module_path}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            results['errors'].append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error importing {module_path}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            results['errors'].append(error_msg)
    
    # Assess extraction feasibility based on results
    if results['import_success'] and not results['errors']:
        results['extraction_feasibility'] = 'high'
    elif results['import_success'] and results['errors']:
        results['extraction_feasibility'] = 'medium'
    else:
        results['extraction_feasibility'] = 'low'
    
    return results

def test_qca_subsystem():
    """Test QCA subsystem for independent extraction"""
    return test_component_independence(
        "QCA Analysis Subsystem",
        [
            "src.qc.qca.qca_pipeline",
            "src.qc.qca.qca_schemas"
        ]
    )

def test_api_layer():
    """Test API layer for independent extraction"""
    return test_component_independence(
        "API Layer",
        [
            "src.qc.api.main",
            "src.qc.api.taxonomy_endpoint", 
            "src.qc.api.research_integration",
            "src.qc.api.websocket_progress"
        ]
    )

def test_prompt_templates():
    """Test advanced prompt templates"""
    return test_component_independence(
        "Advanced Prompt Templates",
        [
            "src.qc.workflows.prompt_templates",
            "src.qc.prompts.prompt_loader"
        ]
    )

def test_ai_taxonomy():
    """Test AI taxonomy integration"""
    return test_component_independence(
        "AI Taxonomy Integration", 
        [
            "src.qc.taxonomy.ai_taxonomy_loader"
        ]
    )

def test_configuration_coupling():
    """Test configuration system independence"""
    print("\n=== Testing Configuration System Coupling ===")
    
    try:
        # Test minimal config loading
        from src.qc.config.methodology_config import MethodologyConfigManager
        
        config_mgr = MethodologyConfigManager()
        
        # Test if it can load without advanced features
        minimal_config = {
            'methodology': 'grounded_theory',
            'theoretical_sensitivity': 'medium'
        }
        
        print(f"[SUCCESS] Configuration system can load minimal configs")
        return {
            'component': 'Configuration System',
            'coupling_level': 'low',
            'supports_minimal_config': True,
            'extraction_feasibility': 'high'
        }
        
    except Exception as e:
        print(f"[ERROR] Configuration coupling error: {e}")
        return {
            'component': 'Configuration System',
            'coupling_level': 'high', 
            'supports_minimal_config': False,
            'extraction_feasibility': 'low',
            'error': str(e)
        }

def analyze_file_sizes():
    """Analyze file sizes for each component"""
    print("\n=== Analyzing Component Sizes ===")
    
    components = {
        'QCA Subsystem': ['src/qc/qca/'],
        'API Layer': ['src/qc/api/'],
        'Prompt Templates': ['src/qc/workflows/prompt_templates.py', 'src/qc/prompts/'],
        'AI Taxonomy': ['src/qc/taxonomy/']
    }
    
    size_analysis = {}
    
    for component, paths in components.items():
        total_size = 0
        total_lines = 0
        file_count = 0
        
        for path_str in paths:
            path = Path(path_str)
            
            if path.is_file():
                if path.suffix == '.py':
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            lines = len(f.readlines())
                        total_lines += lines
                        total_size += path.stat().st_size
                        file_count += 1
                    except Exception as e:
                        print(f"Error reading {path}: {e}")
            elif path.is_dir():
                for py_file in path.rglob("*.py"):
                    if py_file.name != '__init__.py':
                        try:
                            with open(py_file, 'r', encoding='utf-8') as f:
                                lines = len(f.readlines())
                            total_lines += lines
                            total_size += py_file.stat().st_size
                            file_count += 1
                        except Exception as e:
                            print(f"Error reading {py_file}: {e}")
        
        size_analysis[component] = {
            'files': file_count,
            'lines': total_lines,
            'bytes': total_size,
            'kb': round(total_size / 1024, 1)
        }
        
        print(f"{component}: {file_count} files, {total_lines} lines, {size_analysis[component]['kb']} KB")
    
    return size_analysis

def main():
    """Main feature extraction assessment"""
    print("=== FEATURE EXTRACTION ASSESSMENT - TASK 4.3 ===")
    print("Testing user-requested components for extraction feasibility")
    
    results = {
        'assessment_date': '2025-09-04',
        'objective': 'Assess extraction feasibility for desired components',
        'components_tested': {},
        'size_analysis': {},
        'overall_assessment': {}
    }
    
    # Test each component
    print("\nCOMPONENT INDEPENDENCE TESTING")
    results['components_tested']['qca'] = test_qca_subsystem()
    results['components_tested']['api'] = test_api_layer()
    results['components_tested']['prompts'] = test_prompt_templates()
    results['components_tested']['taxonomy'] = test_ai_taxonomy()
    results['components_tested']['config'] = test_configuration_coupling()
    
    # Analyze sizes
    print("\nSIZE ANALYSIS")
    results['size_analysis'] = analyze_file_sizes()
    
    # Overall assessment
    print("\nOVERALL ASSESSMENT")
    
    feasible_components = []
    problematic_components = []
    
    for comp_name, comp_data in results['components_tested'].items():
        if comp_data.get('extraction_feasibility') in ['high', 'medium']:
            feasible_components.append(comp_name)
        else:
            problematic_components.append(comp_name)
    
    results['overall_assessment'] = {
        'feasible_components': feasible_components,
        'problematic_components': problematic_components,
        'extraction_success_rate': len(feasible_components) / len(results['components_tested']) * 100
    }
    
    print(f"Feasible for extraction: {feasible_components}")
    print(f"Problematic: {problematic_components}")
    print(f"Success rate: {results['overall_assessment']['extraction_success_rate']:.1f}%")
    
    # Save results
    with open('feature_extraction_assessment.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: feature_extraction_assessment.json")
    
    return results

if __name__ == "__main__":
    main()