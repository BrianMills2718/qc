"""
Integration test for Grounded Theory workflow
This test validates the core functionality is working
"""
import pytest
import asyncio
from pathlib import Path
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.config.methodology_config import MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow

class TestGTWorkflow:
    """Test the complete GT workflow"""
    
    @pytest.mark.asyncio
    async def test_minimal_gt_workflow(self):
        """Test GT workflow with minimal data"""
        # Use proven working configuration
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(
            Path("config/methodology_configs/grounded_theory_reliable.yaml")
        )
        
        # Initialize operations
        operations = RobustCLIOperations(config=config)
        init_success = await operations.initialize_systems()
        assert init_success, "System initialization failed"
        
        # Load test interviews
        interviews = operations.robust_load_interviews(
            Path("data/interviews/ai_interviews_3_for_test")
        )
        assert len(interviews) == 3, f"Expected 3 interviews, got {len(interviews)}"
        
        # Create workflow
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        # Run workflow
        result = await workflow.execute_complete_workflow(interviews)
        
        # Validate results
        assert result is not None, "Workflow returned None"
        assert hasattr(result, 'open_codes'), "Result missing open_codes"
        assert hasattr(result, 'theoretical_model'), "Result missing theoretical_model"
        assert len(result.open_codes) > 0, "No open codes generated"
        
        print(f"SUCCESS: Generated {len(result.open_codes)} codes")
        print(f"Model: {result.theoretical_model.model_name if result.theoretical_model else 'None'}")

    @pytest.mark.asyncio  
    async def test_memo_generation(self):
        """Test that memos are generated correctly"""
        # Check memo files exist after workflow
        memo_dir = Path("data/memos")
        json_memos = list(memo_dir.glob("theoretical_memo_*.json"))
        assert len(json_memos) > 0, "No memo files found"
        
        # Verify memo content
        import json
        latest_memo = max(json_memos, key=lambda p: p.stat().st_mtime)
        with open(latest_memo) as f:
            memo_data = json.load(f)
        
        assert 'patterns' in memo_data, "Memo missing patterns"
        assert 'insights' in memo_data, "Memo missing insights"
        assert len(memo_data.get('patterns', [])) > 0, "No patterns in memo"