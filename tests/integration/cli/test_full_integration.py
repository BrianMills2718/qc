"""
Full Integration Test for Enhanced Speaker Detection
Tests complete workflow from CLI through enhanced detection
"""
import pytest
import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add qc_clean to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qc_clean'))

from core.workflow.grounded_theory import GroundedTheoryWorkflow
from config.unified_config import UnifiedConfig
from core.llm.llm_handler import LLMHandler

class TestFullIntegration:
    """Full system integration tests for enhanced speaker detection"""
    
    @pytest.fixture
    async def setup_test_environment(self):
        """Set up test environment with temporary directories"""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        
        self.input_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)
        
        # Create test interview data
        test_interview = """
John: Hello, I'd like to discuss our research methodology.

Sarah: That sounds great. I think we should focus on qualitative approaches.

John: I agree. What are your thoughts on grounded theory?

Sarah: I believe grounded theory offers excellent systematic analysis capabilities.

Moderator: Can you both elaborate on the benefits?

John: Well, grounded theory allows for emergent themes to develop naturally from the data.

Sarah: Yes, and it provides a rigorous framework for qualitative analysis.
"""
        
        # Write test file
        test_file = self.input_dir / "test_interview.txt"
        test_file.write_text(test_interview.strip())
        
        yield {
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "test_file": str(test_file)
        }
        
        # Cleanup
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_enhanced_detection_integration(self, setup_test_environment):
        """Test enhanced speaker detection through full workflow"""
        env = await setup_test_environment
        
        # Create configuration for enhanced detection
        config = UnifiedConfig()
        gt_config = config.to_grounded_theory_config()
        
        # Override extractor to use enhanced_semantic with LLM detection
        gt_config.extractor_plugin = "enhanced_semantic"
        
        # Add speaker detection configuration
        class SpeakerDetectionConfig:
            method = "llm"
            enabled = True
        
        gt_config.speaker_detection = SpeakerDetectionConfig()
        
        # Initialize LLM handler
        llm_handler = LLMHandler(config=gt_config)
        
        # Initialize workflow
        workflow = GroundedTheoryWorkflow(config=gt_config, llm_handler=llm_handler)
        
        try:
            # Process the test interview
            result = await workflow.process_interview_file(
                input_file=env["test_file"],
                output_dir=env["output_dir"]
            )
            
            # Verify processing completed
            assert result is not None
            print(f"✅ Enhanced detection workflow completed successfully")
            
            # Check that speakers were detected
            if hasattr(result, 'speaker_analysis'):
                speakers = result.speaker_analysis
                print(f"✅ Speakers detected: {speakers}")
                # Should detect John, Sarah, and Moderator
                assert len(speakers) >= 3
            
            # Verify output files created
            output_files = list(Path(env["output_dir"]).glob("*"))
            assert len(output_files) > 0
            print(f"✅ Output files created: {len(output_files)} files")
            
            return True
            
        except Exception as e:
            print(f"❌ Enhanced detection integration test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_baseline_compatibility(self, setup_test_environment):
        """Test that baseline functionality is preserved"""
        env = await setup_test_environment
        
        # Create configuration for baseline (regex) detection
        config = UnifiedConfig()
        gt_config = config.to_grounded_theory_config()
        
        # Use original semantic extractor
        gt_config.extractor_plugin = "semantic"
        
        # Initialize LLM handler
        llm_handler = LLMHandler(config=gt_config)
        
        # Initialize workflow
        workflow = GroundedTheoryWorkflow(config=gt_config, llm_handler=llm_handler)
        
        try:
            # Process the test interview
            result = await workflow.process_interview_file(
                input_file=env["test_file"],
                output_dir=env["output_dir"]
            )
            
            # Verify processing completed
            assert result is not None
            print(f"✅ Baseline workflow compatibility preserved")
            
            # Verify output files created
            output_files = list(Path(env["output_dir"]).glob("*"))
            assert len(output_files) > 0
            print(f"✅ Baseline processing successful: {len(output_files)} files")
            
            return True
            
        except Exception as e:
            print(f"❌ Baseline compatibility test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_enhanced_vs_baseline_comparison(self, setup_test_environment):
        """Compare enhanced detection vs baseline performance"""
        env = await setup_test_environment
        
        # Test baseline
        config = UnifiedConfig()
        gt_config = config.to_grounded_theory_config()
        gt_config.extractor_plugin = "semantic"
        llm_handler = LLMHandler(config=gt_config)
        baseline_workflow = GroundedTheoryWorkflow(config=gt_config, llm_handler=llm_handler)
        
        # Test enhanced
        enhanced_config = UnifiedConfig()
        enhanced_gt_config = enhanced_config.to_grounded_theory_config()
        enhanced_gt_config.extractor_plugin = "enhanced_semantic"
        
        class SpeakerDetectionConfig:
            method = "llm"
            enabled = True
        enhanced_gt_config.speaker_detection = SpeakerDetectionConfig()
        
        enhanced_llm_handler = LLMHandler(config=enhanced_gt_config)
        enhanced_workflow = GroundedTheoryWorkflow(config=enhanced_gt_config, llm_handler=enhanced_llm_handler)
        
        try:
            # Create separate output directories
            baseline_output = Path(env["output_dir"]) / "baseline"
            enhanced_output = Path(env["output_dir"]) / "enhanced"
            baseline_output.mkdir()
            enhanced_output.mkdir()
            
            # Process with baseline
            baseline_result = await baseline_workflow.process_interview_file(
                input_file=env["test_file"],
                output_dir=str(baseline_output)
            )
            
            # Process with enhanced
            enhanced_result = await enhanced_workflow.process_interview_file(
                input_file=env["test_file"],
                output_dir=str(enhanced_output)
            )
            
            # Verify both completed
            assert baseline_result is not None
            assert enhanced_result is not None
            
            # Count output files
            baseline_files = len(list(baseline_output.glob("*")))
            enhanced_files = len(list(enhanced_output.glob("*")))
            
            print(f"✅ Baseline files: {baseline_files}")
            print(f"✅ Enhanced files: {enhanced_files}")
            
            # Both should produce output
            assert baseline_files > 0
            assert enhanced_files > 0
            
            print(f"✅ Enhanced detection comparison completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Enhanced vs baseline comparison failed: {e}")
            raise

@pytest.mark.asyncio
async def test_cli_integration():
    """Test CLI integration with enhanced detection"""
    import subprocess
    import tempfile
    
    # Create temporary test data
    temp_dir = tempfile.mkdtemp()
    input_dir = Path(temp_dir) / "input"
    output_dir = Path(temp_dir) / "output"
    
    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    
    # Create test interview
    test_interview = """
Alice: Welcome to our focus group discussion about AI methodologies.

Bob: Thanks for having me. I'm excited to share my thoughts on qualitative research.

Alice: Let's start with your experience with grounded theory approaches.

Bob: I've found grounded theory particularly useful for emergent analysis.

Facilitator: Can you both elaborate on the practical applications?

Alice: Certainly. The systematic coding process is very valuable.

Bob: Yes, and the iterative refinement helps develop robust insights.
"""
    
    test_file = input_dir / "focus_group.txt"
    test_file.write_text(test_interview.strip())
    
    try:
        # Test CLI command with enhanced detection
        cmd = [
            sys.executable, "-m", "qc_clean.core.cli.cli_robust",
            "analyze",
            "--input", str(input_dir),
            "--output", str(output_dir),
            "--extractor", "enhanced_semantic",
            "--verbose"
        ]
        
        # Run CLI command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="qc_clean")
        
        print(f"CLI Command: {' '.join(cmd)}")
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        # Verify successful execution
        assert result.returncode == 0, f"CLI command failed with code {result.returncode}"
        
        # Verify output files created
        output_files = list(output_dir.glob("*"))
        assert len(output_files) > 0, "No output files created"
        
        print(f"✅ CLI integration successful: {len(output_files)} files created")
        return True
        
    except Exception as e:
        print(f"❌ CLI integration test failed: {e}")
        raise
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # Run tests directly for development
    asyncio.run(test_cli_integration())