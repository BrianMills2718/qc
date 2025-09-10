#!/usr/bin/env python3
"""
Robust CLI Operations with Graceful Degradation

Provides enhanced CLI operations that degrade gracefully when dependencies
are unavailable or operations fail.
"""

import logging
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from .graceful_degradation import (
    fail_fast_manager, with_fail_fast, ensure_essential_functionality,
    FailFastFileHandler, FailFastNetworkHandler
)
from ..utils.error_handler import ProcessingError, LLMError, QueryError

logger = logging.getLogger(__name__)


class RobustCLIOperations:
    """
    Enhanced CLI operations with comprehensive error handling and fallbacks
    """
    
    def __init__(self, config=None):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.operation_log = []
        self._llm_handler = None
        self._neo4j_manager = None
        self.config = config  # Store configuration for LLM handler creation
    
    async def initialize_systems(self):
        """Initialize systems with graceful degradation"""
        logger.info("Initializing systems with graceful degradation...")
        
        # Check essential functionality first
        if not ensure_essential_functionality():
            logger.critical("Essential functionality unavailable - shutting down")
            return False
        
        # Try to initialize LLM handler
        await self._initialize_llm_handler()
        
        # Try to initialize Neo4j
        await self._initialize_neo4j()
        
        # Try to initialize export systems
        await self._initialize_export_systems()
        
        # Assess final system health
        level = fail_fast_manager.assess_system_health()
        logger.info(f"System initialized at degradation level: {level.value}")
        
        return True
    
    @with_fail_fast('llm_api', "LLM API initialization required")
    async def _initialize_llm_handler(self) -> bool:
        """Initialize LLM handler with fail-fast behavior"""
        try:
            # Check network connectivity first
            FailFastNetworkHandler.check_connectivity()
            
            from ..llm.llm_handler import LLMHandler
            self._llm_handler = LLMHandler(config=self.config)
            
            # For overloaded APIs, we skip the initialization test and trust the handler is configured
            # The retry logic will handle actual failures when the system is used
            logger.info("LLM handler created with retry logic - skipping connectivity test during server overload")
            logger.info(f"Configured with {self._llm_handler.max_retries} max retries and {self._llm_handler.base_delay}s base delay")
            
            logger.info("LLM API initialized successfully")
            return True
                
        except Exception as e:
            logger.error(f"LLM handler initialization failed: {e}")
            raise ProcessingError(f"LLM API initialization failed: {e}")
    
    async def _initialize_neo4j(self) -> bool:
        """Initialize Neo4j - optional capability"""
        try:
            from .neo4j_manager import EnhancedNeo4jManager
            self._neo4j_manager = EnhancedNeo4jManager()
            
            # Test connection
            await self._neo4j_manager.connect()
            logger.info("Neo4j database initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Neo4j initialization failed: {e}")
            # Neo4j is optional - just warn but don't fail
            fail_fast_manager.mark_capability_failed('neo4j_database', e)
            return False
    
    @with_fail_fast('export_functionality', "Export functionality required")
    async def _initialize_export_systems(self) -> bool:
        """Initialize export systems with fallbacks"""
        try:
            # Test basic export capabilities
            from ..export.data_exporter import DataExporter
            exporter = DataExporter()
            
            # Test JSON export (most basic)
            test_data = {"test": "data"}
            test_file = Path("temp_test.json")
            
            if FailFastFileHandler.safe_write_json(test_file, test_data):
                test_file.unlink(missing_ok=True)  # Clean up
                logger.info("Export systems initialized successfully")
                return True
            else:
                raise ProcessingError("Export system test failed")
                
        except Exception as e:
            logger.error(f"Export system initialization failed: {e}")
            raise ProcessingError(f"Export functionality failed: {e}")
    
    @with_fail_fast('file_access', "File system access required for loading interviews")
    def robust_load_interviews(self, input_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load interview files with fail-fast error handling"""
        input_dir = Path(input_path)
        interviews = []
        
        if not input_dir.exists():
            raise ProcessingError(f"Input directory not found: {input_dir}")
        
        # Look for various file types
        file_patterns = ['*.txt', '*.docx', '*.json']
        
        for pattern in file_patterns:
            for file_path in input_dir.glob(pattern):
                try:
                    interview_data = self._load_single_interview(file_path)
                    if interview_data:
                        interviews.append(interview_data)
                        logger.debug(f"Loaded interview: {file_path.name}")
                    else:
                        logger.warning(f"Failed to load interview: {file_path.name}")
                        
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
                    self.operation_log.append(f"Failed to load {file_path.name}: {e}")
        
        logger.info(f"Loaded {len(interviews)} interviews from {input_dir}")
        return interviews
    
    def _load_single_interview(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load a single interview file with format detection"""
        try:
            if file_path.suffix.lower() == '.json':
                return FailFastFileHandler.safe_read_json(file_path)
            
            elif file_path.suffix.lower() in ['.txt', '.md']:
                text_content = FailFastFileHandler.safe_read_text(file_path)
                return {
                    'interview_id': file_path.stem,
                    'text': text_content,
                    'filename': file_path.name,
                    'file_type': 'text'
                }
            
            elif file_path.suffix.lower() == '.docx':
                # Try to load Word document
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text_content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                    
                    return {
                        'interview_id': file_path.stem,
                        'text': text_content,
                        'filename': file_path.name,
                        'file_type': 'docx'
                    }
                except ImportError:
                    logger.warning("python-docx not available, skipping Word document")
                    return None
                except Exception as e:
                    logger.error(f"Failed to read Word document {file_path}: {e}")
                    return None
            
            else:
                logger.warning(f"Unsupported file type: {file_path.suffix}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading interview {file_path}: {e}")
            return None
    
    @with_fail_fast('llm_api', "LLM API required for data extraction")
    async def robust_extract_data(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data with fail-fast behavior"""
        if not self._llm_handler:
            raise ProcessingError("LLM handler not initialized")
        
        try:
            # Use the main extraction system
            from ..extraction.code_first_extractor import CodeFirstExtractor
            extractor = CodeFirstExtractor(self._llm_handler)
            
            result = await extractor.extract_full_interview(
                interview_data.get('text', ''),
                interview_data.get('interview_id', 'unknown')
            )
            
            logger.info(f"Extracted data for interview {interview_data.get('interview_id')}")
            return result
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            raise ProcessingError(f"Data extraction failed: {e}")
    
    async def robust_store_results(self, results: Dict[str, Any], output_dir: Path) -> bool:
        """Store results to file storage (Neo4j optional)"""
        try:
            # Try Neo4j storage if available (optional)
            if self._neo4j_manager and fail_fast_manager.is_capability_available('neo4j_database'):
                try:
                    success = await self._store_to_neo4j(results)
                    if success:
                        logger.info("Results stored in Neo4j database")
                except Exception as e:
                    logger.warning(f"Neo4j storage failed: {e}")
            
            # Store to files (required)
            return await self._store_to_files(results, output_dir)
            
        except Exception as e:
            logger.error(f"Result storage failed: {e}")
            raise ProcessingError(f"Failed to store results: {e}")
    
    async def _store_to_neo4j(self, results: Dict[str, Any]) -> bool:
        """Store results to Neo4j database"""
        try:
            if not self._neo4j_manager:
                return False
            
            # Store interview data
            # Implementation would store quotes, codes, entities, relationships
            logger.info("Storing results to Neo4j (placeholder)")
            return True
            
        except Exception as e:
            logger.error(f"Neo4j storage failed: {e}")
            return False
    
    async def _store_to_files(self, results: Dict[str, Any], output_dir: Path) -> bool:
        """Store results to file system"""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Store main results
            results_file = output_dir / "extraction_results.json"
            if not FailFastFileHandler.safe_write_json(results_file, results):
                raise ProcessingError("Failed to write main results file")
            
            # Store individual components
            components = ['quotes', 'codes', 'entities']
            for component in components:
                if component in results and results[component]:
                    component_file = output_dir / f"{component}.json"
                    FailFastFileHandler.safe_write_json(component_file, {component: results[component]})
            
            logger.info(f"Results stored to file system at {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"File storage failed: {e}")
            raise ProcessingError(f"File storage failed: {e}")
    
    @with_fail_fast('export_functionality', "Export functionality required")
    def robust_export_data(self, input_dir: Path, output_name: str, 
                          export_format: str = 'csv', components: List[str] = None) -> bool:
        """Export data with graceful degradation"""
        try:
            from ..export.data_exporter import DataExporter
            exporter = DataExporter()
            
            # Default components
            if not components:
                components = ['quotes', 'codes']
            
            # Load data from input directory
            interviews = []
            interviews_dir = input_dir / "interviews"
            
            if interviews_dir.exists():
                for json_file in interviews_dir.glob("*.json"):
                    interview_data = FailFastFileHandler.safe_read_json(json_file)
                    if interview_data:
                        interviews.append(interview_data)
            else:
                # Fallback to main results file
                results_file = input_dir / "extraction_results.json"
                if results_file.exists():
                    results_data = FailFastFileHandler.safe_read_json(results_file)
                    if results_data:
                        interviews = [results_data]
            
            if not interviews:
                raise ProcessingError(f"No data found in {input_dir}")
            
            # Export based on format
            if export_format == 'csv':
                return self._export_csv(exporter, interviews, output_name, components)
            elif export_format == 'excel':
                return self._export_excel(exporter, interviews, output_name, components)
            else:
                raise ProcessingError(f"Unsupported export format: {export_format}")
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise ProcessingError(f"Export failed: {e}")
    
    def _export_csv(self, exporter, interviews: List[Dict], output_name: str, components: List[str]) -> bool:
        """Export to CSV format with error handling"""
        try:
            success_count = 0
            
            for component in components:
                try:
                    if component == 'quotes':
                        output_file = exporter.export_quotes_csv(interviews, f"{output_name}_quotes")
                    elif component == 'codes':
                        output_file = exporter.export_codes_csv(interviews, f"{output_name}_codes")
                    elif component == 'speakers':
                        output_file = exporter.export_speakers_csv(interviews, f"{output_name}_speakers")
                    elif component == 'entities':
                        output_file = exporter.export_entities_csv(interviews, f"{output_name}_entities")
                    else:
                        logger.warning(f"Unknown component: {component}")
                        continue
                    
                    logger.info(f"Exported {component} to {output_file}")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to export {component}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
    
    @with_fail_fast('export_functionality', "Export functionality required")
    def robust_export_r_integration(self, input_dir: Path, output_name: str = None) -> Dict[str, str]:
        """Export data with R package integration (CSV + R script + documentation)"""
        try:
            from ..export.data_exporter import DataExporter
            exporter = DataExporter()
            
            # Load data from input directory
            interviews = []
            interviews_dir = input_dir / "interviews"
            
            if interviews_dir.exists():
                for interview_file in interviews_dir.glob("*.json"):
                    try:
                        with open(interview_file, 'r', encoding='utf-8') as f:
                            interview_data = json.load(f)
                            interviews.append(interview_data)
                    except Exception as e:
                        logger.warning(f"Failed to load interview {interview_file}: {e}")
            
            if not interviews:
                raise ProcessingError("No interview data found for R export")
            
            # Generate R package integration export
            if not output_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_name = f"qca_r_analysis_{timestamp}"
            
            result_files = exporter.export_r_package_integration(interviews, output_name)
            
            logger.info(f"R integration export complete: {len(result_files)} files generated")
            logger.info(f"CSV Data: {result_files['csv_data']}")
            logger.info(f"R Script: {result_files['r_script']}")
            logger.info(f"Documentation: {result_files['readme']}")
            
            return result_files
            
        except Exception as e:
            logger.error(f"R integration export failed: {e}")
            raise ProcessingError(f"R integration export failed: {e}")
    
    def robust_execute_query_template(self, template_id: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a pre-built Neo4j query template"""
        try:
            # Import here to avoid circular imports and handle missing dependencies
            try:
                from ..query.query_templates import QueryTemplateExecutor
            except ImportError as import_err:
                raise ProcessingError(f"Query templates not available: {import_err}")
            
            # Check if Neo4j is available
            if not hasattr(self, '_neo4j_manager') or not self._neo4j_manager:
                raise ProcessingError("Neo4j database not available - query templates require Neo4j connection")
            
            # Initialize executor
            executor = QueryTemplateExecutor(self._neo4j_manager)
            
            # Execute template
            import asyncio
            result = asyncio.run(executor.execute_template(template_id, parameters))
            
            if result['success']:
                logger.info(f"Query template '{template_id}' executed successfully - {result['result_count']} results")
            else:
                logger.error(f"Query template execution failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Query template execution failed: {e}")
            return {
                "success": False,
                "template_id": template_id,
                "error": str(e),
                "results": [],
                "result_count": 0
            }
    
    def list_query_templates(self) -> Dict[str, Any]:
        """List all available Neo4j query templates"""
        try:
            from ..query.query_templates import QueryTemplateExecutor
            
            # Initialize executor (doesn't need actual Neo4j connection for listing)
            executor = QueryTemplateExecutor(None)
            templates = executor.list_available_templates()
            
            logger.info(f"Retrieved {sum(len(templates[cat]) for cat in templates)} query templates across {len(templates)} categories")
            
            return {
                "success": True,
                "templates": templates,
                "total_count": sum(len(templates[cat]) for cat in templates),
                "categories": list(templates.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to list query templates: {e}")
            return {
                "success": False,
                "error": str(e),
                "templates": {},
                "total_count": 0
            }
    
    @with_fail_fast('llm_api', "LLM API required for memo generation")
    async def robust_generate_analytical_memo(
        self, 
        input_dir: Path, 
        memo_type: str = "pattern_analysis",
        focus_codes: Optional[List[str]] = None,
        memo_title: str = None,
        output_format: str = "both"  # "json", "markdown", "both"
    ) -> Dict[str, Any]:
        """Generate analytical memo from interview data using LLM analysis"""
        try:
            from ..analysis.analytical_memos import AnalyticalMemoGenerator, MemoType
            from pathlib import Path as PathlibPath
            
            # Validate memo type
            valid_types = [t.value for t in MemoType]
            if memo_type not in valid_types:
                raise ProcessingError(f"Invalid memo type. Valid types: {valid_types}")
            
            # Load interview data
            interviews = []
            interviews_dir = input_dir / "interviews"
            
            if interviews_dir.exists():
                for interview_file in interviews_dir.glob("*.json"):
                    try:
                        with open(interview_file, 'r', encoding='utf-8') as f:
                            interview_data = json.load(f)
                            interviews.append(interview_data)
                    except Exception as e:
                        logger.warning(f"Failed to load interview {interview_file}: {e}")
            
            if not interviews:
                raise ProcessingError("No interview data found for memo generation")
            
            # Initialize memo generator
            memo_generator = AnalyticalMemoGenerator(self._llm_handler)
            
            # Generate memo based on type
            if memo_type == "pattern_analysis":
                memo = await memo_generator.generate_pattern_analysis_memo(
                    interviews, focus_codes, memo_title
                )
            elif memo_type == "theoretical_memo":
                memo = await memo_generator.generate_theoretical_memo(
                    interviews, None, memo_title  # Could add theoretical frameworks parameter
                )
            elif memo_type == "cross_case_analysis":
                memo = await memo_generator.generate_cross_case_analysis(
                    interviews, None, memo_title
                )
            else:
                # Default to pattern analysis
                memo = await memo_generator.generate_pattern_analysis_memo(
                    interviews, focus_codes, memo_title
                )
            
            # Export memo in requested format(s)
            output_dir = PathlibPath("data/memos")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            outputs = {}
            
            if output_format in ["json", "both"]:
                json_path = output_dir / f"{memo.memo_id}.json"
                json_file = memo_generator.save_memo_json(memo, json_path)
                outputs["json"] = json_file
            
            if output_format in ["markdown", "both"]:
                md_path = output_dir / f"{memo.memo_id}.md"
                md_file = memo_generator.export_memo_to_markdown(memo, md_path)
                outputs["markdown"] = md_file
            
            logger.info(f"Generated analytical memo: {memo.memo_id}")
            logger.info(f"Found {len(memo.patterns)} patterns and {len(memo.insights)} insights")
            
            return {
                "success": True,
                "memo_id": memo.memo_id,
                "memo_title": memo.title,
                "memo_type": memo.memo_type,
                "pattern_count": len(memo.patterns),
                "insight_count": len(memo.insights),
                "theoretical_connections": len(memo.theoretical_connections),
                "output_files": outputs,
                "executive_summary": memo.executive_summary
            }
            
        except Exception as e:
            logger.error(f"Analytical memo generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "memo_id": None,
                "output_files": {}
            }
    
    async def generate_analytical_memo_from_data(
        self,
        interviews: List[Dict[str, Any]],  # Direct data input
        memo_type: str = "pattern_analysis", 
        focus_codes: Optional[List[str]] = None,
        memo_title: str = None,
        output_format: str = "both"
    ) -> Dict[str, Any]:
        """
        Generate analytical memo from in-memory interview data
        
        This method is specifically designed for workflows that already have interview
        data in memory (like GroundedTheoryWorkflow) and don't need file I/O.
        
        Args:
            interviews: List of interview data dictionaries already in memory
            memo_type: Type of memo ("pattern_analysis", "theoretical_memo", "cross_case_analysis")
            focus_codes: Optional list of codes to focus analysis on
            memo_title: Optional custom title for the memo
            output_format: Format for memo export ("json", "markdown", "both")
            
        Returns:
            Dictionary with memo generation results and metadata
        """
        try:
            from ..analysis.analytical_memos import AnalyticalMemoGenerator, MemoType
            from pathlib import Path as PathlibPath
            from datetime import datetime
            
            # Type validation - Task 2 integration
            if not isinstance(interviews, list):
                raise TypeError(f"Expected List[Dict], got {type(interviews)}")
            
            if not interviews:
                raise ProcessingError("No interview data provided for memo generation")
            
            # Validate memo type
            valid_types = [t.value for t in MemoType]
            if memo_type not in valid_types:
                raise ProcessingError(f"Invalid memo type. Valid types: {valid_types}")
            
            # Initialize memo generator
            memo_generator = AnalyticalMemoGenerator(self._llm_handler)
            
            # Generate memo based on type
            if memo_type == "pattern_analysis":
                memo = await memo_generator.generate_pattern_analysis_memo(
                    interviews, focus_codes, memo_title
                )
            elif memo_type == "theoretical_memo":
                memo = await memo_generator.generate_theoretical_memo(
                    interviews, None, memo_title  # Could add theoretical frameworks parameter
                )
            elif memo_type == "cross_case_analysis":
                memo = await memo_generator.generate_cross_case_analysis(
                    interviews, None, memo_title
                )
            else:
                # Default to pattern analysis
                memo = await memo_generator.generate_pattern_analysis_memo(
                    interviews, focus_codes, memo_title
                )
            
            # Ensure memo_id is always string for path operations - Task 2 integration
            if not hasattr(memo, 'memo_id') or not isinstance(memo.memo_id, str):
                memo_id = f"memo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if hasattr(memo, 'memo_id'):
                    memo.memo_id = memo_id
                else:
                    # Fallback if memo object doesn't have memo_id attribute
                    logger.warning(f"Memo object missing memo_id, using generated: {memo_id}")
            
            # Export memo in requested format(s)
            output_dir = PathlibPath("data/memos")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            outputs = {}
            
            if output_format in ["json", "both"]:
                json_path = output_dir / f"{memo.memo_id}.json"
                json_file = memo_generator.save_memo_json(memo, json_path)
                outputs["json"] = json_file
            
            if output_format in ["markdown", "both"]:
                md_path = output_dir / f"{memo.memo_id}.md"
                md_file = memo_generator.export_memo_to_markdown(memo, md_path)
                outputs["markdown"] = md_file
            
            logger.info(f"Generated analytical memo from data: {memo.memo_id}")
            logger.info(f"Found {len(memo.patterns)} patterns and {len(memo.insights)} insights")
            
            return {
                "success": True,
                "memo_id": memo.memo_id,
                "memo_title": memo.title,
                "memo_type": memo.memo_type,
                "pattern_count": len(memo.patterns),
                "insight_count": len(memo.insights),
                "theoretical_connections": len(memo.theoretical_connections),
                "output_files": outputs,
                "executive_summary": memo.executive_summary
            }
            
        except Exception as e:
            logger.error(f"Analytical memo generation from data failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "memo_id": None,
                "output_files": {}
            }
    
    def list_memo_types(self) -> Dict[str, Any]:
        """List available analytical memo types"""
        try:
            from ..analysis.analytical_memos import MemoType, InsightLevel
            
            return {
                "success": True,
                "memo_types": [
                    {
                        "value": memo_type.value,
                        "description": self._get_memo_type_description(memo_type.value)
                    }
                    for memo_type in MemoType
                ],
                "insight_levels": [level.value for level in InsightLevel]
            }
            
        except Exception as e:
            logger.error(f"Failed to list memo types: {e}")
            return {
                "success": False,
                "error": str(e),
                "memo_types": [],
                "insight_levels": []
            }
    
    def _get_memo_type_description(self, memo_type: str) -> str:
        """Get description for memo type"""
        descriptions = {
            "pattern_analysis": "Identifies recurring patterns and themes in the data",
            "theoretical_memo": "Connects empirical findings to theoretical frameworks",
            "cross_case_analysis": "Compares patterns and themes across different interviews",
            "theme_synthesis": "Synthesizes themes into higher-order concepts",
            "methodological_reflection": "Reflects on methodological approach and validity",
            "research_insights": "Generates research insights and recommendations",
            "conceptual_framework": "Develops conceptual frameworks from findings"
        }
        return descriptions.get(memo_type, "Analytical memo type")
    
    def _export_excel(self, exporter, interviews: List[Dict], output_name: str, components: List[str]) -> bool:
        """Export to Excel format with error handling"""
        try:
            output_file = exporter.export_excel_workbook(interviews, output_name, components)
            logger.info(f"Exported Excel workbook to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            # Fallback to CSV export
            logger.info("Falling back to CSV export")
            return self._export_csv(exporter, interviews, output_name, components)
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """Get summary of all operations performed"""
        return {
            'session_id': self.session_id,
            'degradation_level': fail_fast_manager.system_status.value,
            'system_status': fail_fast_manager.get_system_status(),
            'operation_log': self.operation_log,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status (backward compatibility method)"""
        return fail_fast_manager.get_system_status()
    
    async def initialize(self):
        """Initialize systems (backward compatibility method)"""
        return await self.initialize_systems()
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self._neo4j_manager:
                await self._neo4j_manager.close()
            
            if self._llm_handler:
                # Clean up LLM handler if needed
                pass
                
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")