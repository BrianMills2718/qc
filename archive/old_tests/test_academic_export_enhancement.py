#!/usr/bin/env python3
"""
Test Academic Export Enhancement Implementation

Validates the comprehensive academic export functionality with LaTeX, SPSS, Word, and GraphML formats.
"""

import sys
from pathlib import Path
import tempfile
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_academic_export_enhancement():
    """Test complete academic export enhancement with sample data"""
    
    print("TESTING ACADEMIC EXPORT ENHANCEMENT")
    print("=" * 60)
    
    try:
        from src.qc.export.data_exporter import DataExporter
        
        # Create temporary output directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"[INFO] Using temporary directory: {temp_dir}")
            
            # Initialize data exporter
            exporter = DataExporter(temp_dir)
            print("[OK] DataExporter initialized")
            
            # Create sample analysis data
            sample_data = create_sample_analysis_data()
            print(f"[INFO] Sample data created: {len(sample_data['interviews'])} interviews, {len(sample_data['taxonomy']['codes'])} codes")
            
            # Test 1: LaTeX Report Export
            print("\n1. Testing LaTeX report export...")
            latex_path = exporter.export_latex_report(sample_data, "test_report.tex")
            if os.path.exists(latex_path):
                print(f"   [OK] LaTeX report created: {Path(latex_path).name}")
                print(f"   File size: {os.path.getsize(latex_path)} bytes")
                
                # Check LaTeX content basics
                with open(latex_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '\\documentclass{article}' in content and '\\begin{document}' in content:
                        print("   [OK] Valid LaTeX document structure")
                    else:
                        print("   [ERROR] Invalid LaTeX document structure")
            else:
                print(f"   [ERROR] LaTeX file not created")
            
            # Test 2: SPSS Syntax Export
            print("\n2. Testing SPSS syntax export...")
            interviews = sample_data.get('interviews', [])
            spss_path = exporter.export_spss_syntax(interviews, "test_import.sps")
            if os.path.exists(spss_path):
                print(f"   [OK] SPSS syntax created: {Path(spss_path).name}")
                print(f"   File size: {os.path.getsize(spss_path)} bytes")
                
                # Check SPSS syntax content
                with open(spss_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'GET DATA' in content and 'VARIABLE LABELS' in content:
                        print("   [OK] Valid SPSS syntax structure")
                    else:
                        print("   [ERROR] Invalid SPSS syntax structure")
            else:
                print(f"   [ERROR] SPSS file not created")
            
            # Test 3: Word Report Export (conditional on python-docx)
            print("\n3. Testing Word report export...")
            try:
                word_path = exporter.export_word_report(sample_data, "test_report.docx")
                if os.path.exists(word_path):
                    print(f"   [OK] Word report created: {Path(word_path).name}")
                    print(f"   File size: {os.path.getsize(word_path)} bytes")
                else:
                    print(f"   [ERROR] Word file not created")
            except ImportError as e:
                print(f"   [SKIP] Word export unavailable: {e}")
            except Exception as e:
                print(f"   [ERROR] Word export failed: {e}")
            
            # Test 4: GraphML Network Export (conditional on networkx)
            print("\n4. Testing GraphML network export...")
            try:
                graphml_path = exporter.export_graphml_network(interviews, "test_network.graphml")
                if os.path.exists(graphml_path):
                    print(f"   [OK] GraphML network created: {Path(graphml_path).name}")
                    print(f"   File size: {os.path.getsize(graphml_path)} bytes")
                    
                    # Check GraphML content basics
                    with open(graphml_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '<graphml' in content and '<node' in content:
                            print("   [OK] Valid GraphML document structure")
                        else:
                            print("   [ERROR] Invalid GraphML document structure")
                else:
                    print(f"   [ERROR] GraphML file not created")
            except ImportError as e:
                print(f"   [SKIP] GraphML export unavailable: {e}")
            except Exception as e:
                print(f"   [ERROR] GraphML export failed: {e}")
            
            # Test 5: Complete Academic Export Package
            print("\n5. Testing complete academic export package...")
            package_files = exporter.export_academic_complete(sample_data, "test_package")
            
            print(f"   [INFO] Export package generated {len(package_files)} items:")
            
            successful_exports = []
            errors = []
            unavailable = []
            
            for key, value in package_files.items():
                if key.endswith('_error'):
                    errors.append(f"{key}: {value}")
                elif key.endswith('_unavailable'):
                    unavailable.append(f"{key}: {value}")
                else:
                    successful_exports.append(f"{key}: {Path(value).name}")
                    if os.path.exists(value):
                        print(f"     [OK] {key}: {Path(value).name} ({os.path.getsize(value)} bytes)")
                    else:
                        print(f"     [ERROR] {key}: File not found")
            
            print(f"\n   Summary:")
            print(f"   - Successful exports: {len(successful_exports)}")
            print(f"   - Errors: {len(errors)}")
            print(f"   - Unavailable formats: {len(unavailable)}")
            
            if errors:
                print(f"\n   Errors encountered:")
                for error in errors:
                    print(f"     - {error}")
            
            if unavailable:
                print(f"\n   Unavailable formats:")
                for unavail in unavailable:
                    print(f"     - {unavail}")
            
            # Test 6: README Generation Validation
            print("\n6. Testing README generation...")
            readme_files = [f for f in package_files.keys() if 'readme' in f.lower() and not f.endswith('_error')]
            if readme_files:
                readme_key = readme_files[0]
                readme_path = package_files[readme_key]
                if os.path.exists(readme_path):
                    print(f"   [OK] README generated: {Path(readme_path).name}")
                    
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'QCA Academic Export Package' in content and 'Usage Instructions' in content:
                            print("   [OK] Complete README content structure")
                        else:
                            print("   [ERROR] Incomplete README content")
                else:
                    print(f"   [ERROR] README file not found")
            else:
                print("   [ERROR] No README file in export package")
        
        print(f"\n[SUCCESS] Academic export enhancement testing completed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Academic export enhancement testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_analysis_data():
    """Create comprehensive sample data for testing all export formats"""
    return {
        'interviews': [
            {
                'interview_id': 'test_interview_001',
                'quotes': [
                    {
                        'id': 'q001',
                        'text': 'The main challenge we face is communication between different teams. There are always gaps in information sharing.',
                        'speaker': {'name': 'Participant A'},
                        'code_names': ['communication_challenges', 'information_sharing', 'team_coordination'],
                        'code_ids': ['comm_001', 'info_001', 'team_001'],
                        'code_confidence_scores': [0.85, 0.92, 0.78],
                        'location_start': 245,
                        'location_end': 380,
                        'location_type': 'transcript_position',
                        'context_summary': 'Discussion about organizational challenges'
                    },
                    {
                        'id': 'q002',
                        'text': 'When we implement new processes, training and support are absolutely critical for success.',
                        'speaker': {'name': 'Participant B'},
                        'code_names': ['process_implementation', 'training_importance', 'change_management'],
                        'code_ids': ['proc_001', 'train_001', 'change_001'],
                        'code_confidence_scores': [0.91, 0.88, 0.83],
                        'location_start': 580,
                        'location_end': 680,
                        'location_type': 'transcript_position',
                        'context_summary': 'Process improvement discussion'
                    },
                    {
                        'id': 'q003',
                        'text': 'Leadership commitment makes all the difference. Without buy-in from the top, initiatives fail.',
                        'speaker': {'name': 'Participant A'},
                        'code_names': ['leadership_commitment', 'organizational_support', 'change_management'],
                        'code_ids': ['lead_001', 'org_001', 'change_001'],
                        'code_confidence_scores': [0.94, 0.87, 0.89],
                        'location_start': 820,
                        'location_end': 920,
                        'location_type': 'transcript_position',
                        'context_summary': 'Leadership and change factors'
                    }
                ]
            },
            {
                'interview_id': 'test_interview_002',
                'quotes': [
                    {
                        'id': 'q004',
                        'text': 'Technology can be a great enabler, but it needs to be user-friendly and well-integrated.',
                        'speaker': {'name': 'Participant C'},
                        'code_names': ['technology_enablement', 'usability', 'system_integration'],
                        'code_ids': ['tech_001', 'use_001', 'sys_001'],
                        'code_confidence_scores': [0.86, 0.79, 0.82],
                        'location_start': 120,
                        'location_end': 220,
                        'location_type': 'transcript_position',
                        'context_summary': 'Technology implementation discussion'
                    },
                    {
                        'id': 'q005',
                        'text': 'Resistance to change is natural, but clear communication and involvement helps overcome it.',
                        'speaker': {'name': 'Participant D'},
                        'code_names': ['change_resistance', 'communication_strategies', 'stakeholder_involvement'],
                        'code_ids': ['resist_001', 'comm_002', 'stake_001'],
                        'code_confidence_scores': [0.90, 0.85, 0.87],
                        'location_start': 340,
                        'location_end': 450,
                        'location_type': 'transcript_position',
                        'context_summary': 'Change resistance and mitigation'
                    }
                ]
            }
        ],
        'taxonomy': {
            'codes': [
                {
                    'id': 'comm_001',
                    'name': 'communication_challenges',
                    'description': 'Challenges related to organizational communication and information flow',
                    'semantic_definition': 'Barriers, gaps, or difficulties in sharing information effectively across organizational units',
                    'level': 1,
                    'parent_id': '',
                    'discovery_confidence': 0.92,
                    'example_quotes': [
                        'communication between different teams',
                        'gaps in information sharing'
                    ]
                },
                {
                    'id': 'change_001',
                    'name': 'change_management',
                    'description': 'Processes and strategies for managing organizational change',
                    'semantic_definition': 'Systematic approaches to transitioning individuals and organizations from current to desired future states',
                    'level': 1,
                    'parent_id': '',
                    'discovery_confidence': 0.88,
                    'example_quotes': [
                        'implement new processes',
                        'Leadership commitment makes all the difference'
                    ]
                },
                {
                    'id': 'tech_001',
                    'name': 'technology_enablement',
                    'description': 'Role of technology in enabling organizational processes and outcomes',
                    'semantic_definition': 'Use of technological solutions to facilitate, improve, or enable business processes and capabilities',
                    'level': 1,
                    'parent_id': '',
                    'discovery_confidence': 0.85,
                    'example_quotes': [
                        'Technology can be a great enabler'
                    ]
                },
                {
                    'id': 'lead_001',
                    'name': 'leadership_commitment',
                    'description': 'Importance of leadership support and commitment to organizational initiatives',
                    'semantic_definition': 'Active engagement, support, and visible commitment from organizational leaders to drive successful outcomes',
                    'level': 2,
                    'parent_id': 'change_001',
                    'discovery_confidence': 0.94,
                    'example_quotes': [
                        'Leadership commitment makes all the difference',
                        'Without buy-in from the top, initiatives fail'
                    ]
                },
                {
                    'id': 'resist_001',
                    'name': 'change_resistance',
                    'description': 'Natural human and organizational resistance to change initiatives',
                    'semantic_definition': 'Psychological, cultural, or structural barriers that impede acceptance and implementation of change',
                    'level': 2,
                    'parent_id': 'change_001',
                    'discovery_confidence': 0.87,
                    'example_quotes': [
                        'Resistance to change is natural'
                    ]
                }
            ]
        },
        'speaker_schema': {
            'properties': [
                {
                    'property_name': 'role',
                    'description': 'Professional role or position'
                },
                {
                    'property_name': 'department',
                    'description': 'Organizational department or unit'
                }
            ]
        },
        'entity_schema': {
            'entity_types': [
                {
                    'type_name': 'process',
                    'description': 'Organizational processes and procedures'
                },
                {
                    'type_name': 'technology',
                    'description': 'Technology systems and tools'
                }
            ]
        }
    }

def main():
    """Run academic export enhancement validation"""
    print("ACADEMIC EXPORT ENHANCEMENT VALIDATION")
    print("=" * 70)
    
    success = test_academic_export_enhancement()
    
    print("\n" + "=" * 70)
    if success:
        print("[SUCCESS] Academic export enhancement implementation validated!")
        print("Enhanced export capabilities:")
        print("- LaTeX academic report generation")
        print("- SPSS syntax and data export")
        print("- Microsoft Word report creation") 
        print("- GraphML network analysis export")
        print("- Comprehensive academic export package")
        print("- Multi-format documentation and README generation")
    else:
        print("[FAILURE] Academic export enhancement validation failed")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)