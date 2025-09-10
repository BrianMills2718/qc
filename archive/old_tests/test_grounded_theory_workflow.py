#!/usr/bin/env python3
"""
Test Grounded Theory Workflow Implementation

Validates the complete grounded theory analysis workflow with sample data.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_grounded_theory_workflow():
    """Test complete grounded theory workflow with sample data"""
    
    print("TESTING GROUNDED THEORY WORKFLOW")
    print("=" * 50)
    
    try:
        from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
        from src.qc.core.robust_cli_operations import RobustCLIOperations
        
        # Initialize robust operations
        operations = RobustCLIOperations()
        await operations.initialize_systems()
        print("[OK] RobustCLIOperations initialized")
        
        # Initialize grounded theory workflow
        gt_workflow = GroundedTheoryWorkflow(operations)
        print("[OK] GroundedTheoryWorkflow initialized")
        
        # Create sample interview data
        sample_interviews = [
            {
                'interview_id': 'gt_test_interview_1',
                'quotes': [
                    {
                        'id': 'gt_q1',
                        'text': 'The biggest challenge we face is communication between departments. Everyone works in silos.',
                        'speaker': {'name': 'Manager A'},
                        'code_names': ['communication', 'departmental_silos']
                    },
                    {
                        'id': 'gt_q2', 
                        'text': 'When changes happen, we have to quickly adapt our processes. Sometimes it works, sometimes it doesn\'t.',
                        'speaker': {'name': 'Employee B'},
                        'code_names': ['change_adaptation', 'process_flexibility']
                    },
                    {
                        'id': 'gt_q3',
                        'text': 'The key is having good relationships with colleagues. That makes all the difference when problems arise.',
                        'speaker': {'name': 'Team Lead C'},
                        'code_names': ['colleague_relationships', 'problem_solving']
                    }
                ]
            },
            {
                'interview_id': 'gt_test_interview_2', 
                'quotes': [
                    {
                        'id': 'gt_q4',
                        'text': 'Leadership support is crucial. When management backs you up, you can take risks and innovate.',
                        'speaker': {'name': 'Developer D'},
                        'code_names': ['leadership_support', 'innovation_enablement']
                    },
                    {
                        'id': 'gt_q5',
                        'text': 'We\'ve learned to be more proactive about communication. Regular check-ins prevent most issues.',
                        'speaker': {'name': 'Project Manager E'},
                        'code_names': ['proactive_communication', 'issue_prevention']
                    }
                ]
            }
        ]
        
        print(f"[INFO] Testing with {len(sample_interviews)} interviews, {sum(len(i['quotes']) for i in sample_interviews)} quotes")
        
        # Execute complete grounded theory workflow
        print("\n1. Executing complete grounded theory analysis workflow...")
        results = await gt_workflow.execute_complete_workflow(sample_interviews)
        
        # Validate results structure
        print(f"\n2. Validating grounded theory results...")
        print(f"   Open codes identified: {len(results.open_codes)}")
        print(f"   Axial relationships found: {len(results.axial_relationships)}")
        print(f"   Core category: {results.core_category.category_name}")
        print(f"   Theoretical model: {results.theoretical_model.model_name}")
        print(f"   Supporting memos: {len(results.supporting_memos)}")
        
        # Display key findings
        print(f"\n3. Key findings from grounded theory analysis:")
        print(f"   Core phenomenon: {results.core_category.central_phenomenon}")
        print(f"   Theoretical framework: {results.theoretical_model.theoretical_framework[:100]}...")
        print(f"   Number of propositions: {len(results.theoretical_model.propositions)}")
        
        if results.theoretical_model.propositions:
            print(f"   Sample proposition: {results.theoretical_model.propositions[0]}")
        
        # Validate analysis metadata
        metadata = results.analysis_metadata
        print(f"\n4. Analysis metadata:")
        print(f"   Duration: {metadata['duration_seconds']:.2f} seconds")
        print(f"   Interviews processed: {metadata['interview_count']}")
        print(f"   Analysis steps: {len(metadata['analysis_steps'])}")
        
        print(f"\n[SUCCESS] Grounded theory workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Grounded theory workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run grounded theory workflow test"""
    print("GROUNDED THEORY WORKFLOW VALIDATION")
    print("=" * 60)
    
    success = await test_grounded_theory_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] Grounded theory workflow implementation validated!")
    else:
        print("[FAILURE] Grounded theory workflow validation failed")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)