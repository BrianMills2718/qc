"""
Pytest configuration and shared fixtures for validation system tests.

This module provides shared test fixtures and configuration for all
validation system integration and end-to-end tests.
"""

import pytest
import asyncio
import tempfile
import os
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure test logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable noisy loggers during tests
logging.getLogger('neo4j').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for validation configs"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set environment variable to use temp directory
        original_home = os.environ.get('HOME')
        os.environ['QC_CONFIG_DIR'] = temp_dir
        
        yield Path(temp_dir)
        
        # Restore original environment
        if original_home:
            os.environ['HOME'] = original_home
        elif 'QC_CONFIG_DIR' in os.environ:
            del os.environ['QC_CONFIG_DIR']


@pytest.fixture
def sample_interview_files():
    """Create sample interview files for testing"""
    interviews = {
        "researcher_interview.txt": """
        I'm Dr. Emily Rodriguez, a senior researcher at the National Institute of Health.
        I've been working in computational biology for over 12 years, focusing primarily
        on genomics and bioinformatics applications.
        
        My primary tools are R and Python, though I also use specialized bioinformatics
        software like BLAST and Bioconductor. I collaborate extensively with the
        statistics department at Johns Hopkins University.
        
        I'm generally supportive of AI tools for research acceleration, particularly
        for literature review and hypothesis generation. However, I'm somewhat skeptical
        of using AI for critical analysis without proper validation.
        
        I manage a team of 6 postdoctoral researchers and we work closely with
        Dr. Michael Chen from Stanford on several joint projects.
        """,
        
        "engineer_interview.txt": """
        Hello, I'm Alex Thompson, a machine learning engineer at Tesla. I've been
        with the company for 3 years, working primarily on autonomous driving
        perception systems.
        
        I use Python extensively, along with TensorFlow and PyTorch for deep learning.
        Our team also relies heavily on CUDA for GPU acceleration and Docker for
        containerization. Version control through Git is absolutely essential
        for our distributed development process.
        
        I'm quite optimistic about the potential of large language models like
        GPT-4 and Claude for code generation and debugging assistance. We've been
        experimenting with GitHub Copilot with promising results.
        
        I collaborate regularly with the data science team and report directly
        to Sarah Kim, our AI research director.
        """,
        
        "academic_interview.txt": """
        I'm Professor Janet Williams from the University of Chicago, where I lead
        the Social Science Research Methods lab. I've been in academia for 18 years,
        specializing in mixed-methods research and survey methodology.
        
        My research toolkit includes SPSS, R, and increasingly Python for statistical
        analysis. I also use qualitative analysis software like NVivo and Atlas.ti
        for coding interview data.
        
        I maintain a cautious but interested perspective on AI tools for research.
        While I see potential for efficiency gains, I emphasize the importance of
        methodological rigor and human interpretation in social science research.
        
        I frequently collaborate with Dr. Robert Zhang from MIT and supervise
        8 graduate students in our research methods program.
        """
    }
    
    # Create temporary files
    temp_files = {}
    temp_dirs = []
    
    for filename, content in interviews.items():
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(content)
        temp_file.close()
        temp_files[filename] = temp_file.name
        temp_dirs.append(Path(temp_file.name).parent)
    
    yield temp_files
    
    # Cleanup
    for filepath in temp_files.values():
        Path(filepath).unlink(missing_ok=True)


@pytest.fixture
def validation_test_configs():
    """Provide test validation configurations"""
    return {
        "strict_academic": {
            "entities": "closed",
            "relationships": "closed", 
            "quality_threshold": 0.8,
            "confidence_auto_approve": 0.9,
            "auto_reject_unknown": True,
            "standard_entity_types": ["Person", "Organization", "Tool", "Method"],
            "standard_relationship_types": ["WORKS_AT", "USES", "MANAGES", "COLLABORATES_WITH"]
        },
        
        "permissive_exploratory": {
            "entities": "open",
            "relationships": "open",
            "quality_threshold": 0.5,
            "confidence_auto_approve": 0.7,
            "auto_reject_unknown": False,
            "auto_merge_similar": True
        },
        
        "balanced_hybrid": {
            "entities": "hybrid",
            "relationships": "hybrid",
            "quality_threshold": 0.7,
            "confidence_auto_approve": 0.85,
            "consolidation_threshold": 0.8,
            "auto_merge_similar": True,
            "require_evidence": True
        }
    }


@pytest.fixture
def mock_extraction_results():
    """Provide mock extraction results for testing"""
    return {
        "entities": [
            {
                "name": "Dr. Test Researcher",
                "type": "Person",
                "properties": {
                    "role": "Senior Researcher",
                    "institution": "Test University",
                    "department": "Computer Science"
                },
                "quotes": [
                    "I'm Dr. Test Researcher from Test University",
                    "I work in the Computer Science department"
                ],
                "confidence": 0.92,
                "metadata": {
                    "interview_id": "test-001",
                    "extraction_pass": 1
                }
            },
            {
                "name": "Test University",
                "type": "Organization",
                "properties": {
                    "type": "Academic Institution",
                    "location": "Test City"
                },
                "quotes": ["I'm Dr. Test Researcher from Test University"],
                "confidence": 0.89,
                "metadata": {
                    "interview_id": "test-001",
                    "extraction_pass": 1
                }
            },
            {
                "name": "Python",
                "type": "Tool",
                "properties": {
                    "category": "Programming Language",
                    "usage_context": "Data Analysis"
                },
                "quotes": ["I primarily use Python for my research"],
                "confidence": 0.85,
                "metadata": {
                    "interview_id": "test-001",
                    "extraction_pass": 1
                }
            }
        ],
        
        "relationships": [
            {
                "source_entity": "Dr. Test Researcher",
                "target_entity": "Test University",
                "relationship_type": "WORKS_AT",
                "confidence": 0.91,
                "context": "Employment relationship at academic institution",
                "quotes": ["I'm Dr. Test Researcher from Test University"],
                "metadata": {
                    "interview_id": "test-001",
                    "relationship_strength": "strong"
                }
            },
            {
                "source_entity": "Dr. Test Researcher", 
                "target_entity": "Python",
                "relationship_type": "USES",
                "confidence": 0.87,
                "context": "Programming tool usage for research",
                "quotes": ["I primarily use Python for my research"],
                "metadata": {
                    "interview_id": "test-001",
                    "usage_frequency": "regular"
                }
            }
        ],
        
        "codes": [
            {
                "code": "TOOL_PREFERENCE",
                "description": "Expression of preference for specific research tools",
                "quotes": ["I primarily use Python for my research"],
                "confidence": 0.83,
                "metadata": {
                    "interview_id": "test-001",
                    "theme_category": "methodology"
                }
            }
        ]
    }


@pytest.fixture
def test_database_cleanup():
    """Ensure test database is cleaned up after tests"""
    # Setup: mark for cleanup
    databases_to_clean = []
    
    yield databases_to_clean
    
    # Cleanup: clear any test databases
    # Note: Actual cleanup would depend on test database configuration
    pass


@pytest.fixture
def logging_capture(caplog):
    """Capture and provide access to log messages during tests"""
    with caplog.at_level(logging.INFO):
        yield caplog


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests"""
    import time
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    start_metrics = {
        'time': time.time(),
        'memory': process.memory_info().rss / 1024 / 1024,  # MB
        'cpu_percent': process.cpu_percent()
    }
    
    yield start_metrics
    
    end_metrics = {
        'time': time.time(),
        'memory': process.memory_info().rss / 1024 / 1024,  # MB
        'cpu_percent': process.cpu_percent()
    }
    
    # Calculate deltas
    duration = end_metrics['time'] - start_metrics['time']
    memory_delta = end_metrics['memory'] - start_metrics['memory']
    
    print(f"\nPerformance metrics:")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Memory usage: {end_metrics['memory']:.1f}MB (Δ{memory_delta:+.1f}MB)")
    print(f"  CPU: {end_metrics['cpu_percent']:.1f}%")


# Test markers for different test categories
pytest.mark.integration = pytest.mark.mark("integration")
pytest.mark.e2e = pytest.mark.mark("e2e")
pytest.mark.performance = pytest.mark.mark("performance")
pytest.mark.slow = pytest.mark.mark("slow")


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow-running tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add e2e marker to end-to-end tests
        if "end_to_end" in item.nodeid or "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        
        # Add performance marker to performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker to potentially slow tests
        if any(keyword in item.nodeid for keyword in ["gemini", "neo4j", "complete"]):
            item.add_marker(pytest.mark.slow)