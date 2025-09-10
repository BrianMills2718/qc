#!/usr/bin/env python3
"""
Robust CLI Module with Graceful Degradation

Enhanced CLI interface that provides comprehensive error handling, 
graceful degradation, and system monitoring capabilities.
"""

import logging
import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from .graceful_degradation import fail_fast_manager, ensure_essential_functionality
from .robust_cli_operations import RobustCLIOperations
from ..utils.error_handler import ProcessingError, ErrorHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('qca_robust.log')
    ]
)

logger = logging.getLogger(__name__)

# Monitoring functions removed - no lazy implementations allowed

# SystemMonitor removed - no lazy implementations allowed


class RobustCLI:
    """
    Robust CLI interface with comprehensive error handling and monitoring
    """
    
    def __init__(self, config=None):
        self.cli_ops = RobustCLIOperations(config=config)
        self.session_id = None
        self.start_time = datetime.now()
        self.config = config
    
    async def initialize(self):
        """Initialize the robust CLI system"""
        print("Initializing Qualitative Coding Analysis Tool (Robust Mode)")
        print("=" * 60)
        
        # Check essential functionality
        if not ensure_essential_functionality():
            print("[ERROR] CRITICAL: Essential system functionality unavailable")
            print("   System cannot continue. Please check logs and dependencies.")
            return False
        
        # Initialize CLI operations
        success = await self.cli_ops.initialize_systems()
        if not success:
            print("[WARNING]  WARNING: System initialized with limited functionality")
            print("   Some features may be unavailable.")
        else:
            print("[OK] System initialized successfully")
        
        # Monitoring functions removed - no lazy implementations
        print("[WARNING]  System monitoring unavailable")
        
        # Display system status
        status = fail_fast_manager.get_system_status()
        system_status = status['system_status']
        
        if system_status == 'full':
            print("[HEALTHY] System Status: Full functionality available")
        elif system_status == 'limited':
            print("[WARNING] System Status: Limited functionality (some features disabled)")
        elif system_status == 'essential':
            print("[DEGRADED] System Status: Essential functionality only")
        else:
            print("[CRITICAL] System Status: Emergency mode (system will fail on critical errors)")
        
        print()
        return True
    
    async def process_interviews_robust(self, input_dir: str, output_dir: str = None,
                                     validation_mode: str = "balanced") -> bool:
        """
        DEPRECATED: This command uses the old extraction system.
        Please use 'analyze' command instead for Grounded Theory analysis.
        """
        print("[DEPRECATED] The 'process' command is deprecated.")
        print("[INFO] Please use the 'analyze' command for Grounded Theory analysis:")
        print("      python -m src.qc.cli_robust analyze --input data/interviews/folder --output reports/output")
        print()
        print("[INFO] Attempting to redirect to 'analyze' command...")
        
        # Redirect to the new analyze command
        return await self.analyze_grounded_theory(input_dir, output_dir)
        
        # Original implementation commented out but preserved for reference
        """
        try:
            print(f"[DIR] Processing interviews from: {input_dir}")
            
            # Set default output directory
            if not output_dir:
                output_dir = "outputs/current"
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Load interviews with robust handling
            interviews = self.cli_ops.robust_load_interviews(input_dir)
            
            if not interviews:
                print(f"[ERROR] No interviews found in {input_dir}")
                return False
            
            print(f"[FILES] Found {len(interviews)} interviews to process")
            
            # Process each interview
            processed_count = 0
            failed_count = 0
            all_results = []
            
            for i, interview_data in enumerate(interviews, 1):
                interview_id = interview_data.get('interview_id', f'interview_{i}')
                
                print(f"\n[PROCESSING] Processing interview {i}/{len(interviews)}: {interview_id}")
                
                try:
                    # Extract data with graceful degradation
                    result = await self.cli_ops.robust_extract_data(interview_data)
                    
                    if result and ('quotes' in result or 'codes' in result):
                        all_results.append(result)
                        processed_count += 1
                        
                        # Show brief summary
                        quotes_count = len(result.get('quotes', []))
                        codes_count = len(result.get('codes', []))
                        entities_count = len(result.get('entities', []))
                        
                        print(f"   [OK] Extracted: {quotes_count} quotes, {codes_count} codes, {entities_count} entities")
                        
                        if 'warning' in result:
                            print(f"   [WARNING]  {result['warning']}")
                            
                    else:
                        failed_count += 1
                        print(f"   [ERROR] Failed to process interview {interview_id}")
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = str(e)
                    print(f"   [ERROR] Error processing interview {interview_id}: {error_msg}")
                    ErrorHandler.handle_llm_error(e, f"interview_processing_{interview_id}")
            
            # Store results
            if all_results:
                print(f"\n[SAVING] Storing results to {output_path}")
                
                # Combine all results
                combined_results = {
                    'session_id': self.cli_ops.session_id,
                    'processing_summary': {
                        'total_interviews': len(interviews),
                        'processed_successfully': processed_count,
                        'failed': failed_count,
                        'timestamp': datetime.now().isoformat()
                    },
                    'interviews': all_results
                }
                
                storage_success = await self.cli_ops.robust_store_results(combined_results, output_path)
                
                if storage_success:
                    print("   [OK] Results stored successfully")
                else:
                    print("   [WARNING]  Results storage had issues (check logs)")
            
            # Print summary
            print(f"\n[HEALTH] Processing Complete")
            print(f"   Processed: {processed_count}/{len(interviews)} interviews")
            print(f"   Failed: {failed_count}/{len(interviews)} interviews")
            
            if failed_count > 0:
                print(f"   [WARNING]  Some interviews failed - check logs for details")
            
            return processed_count > 0
            
        except Exception as e:
            logger.error(f"Interview processing failed: {e}")
            print(f"[ERROR] Processing failed: {e}")
            return False
        """
    
    async def export_data_robust(self, input_dir: str = None, output_name: str = None,
                               export_format: str = 'csv', components: List[str] = None) -> bool:
        """Export data with robust error handling"""
        try:
            # Set defaults
            if not input_dir:
                input_dir = "outputs/current"
            
            if not output_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"qca_export_{timestamp}"
            
            if not components:
                components = ['quotes', 'codes', 'speakers']
            
            print(f"[EXPORT] Exporting data from: {input_dir}")
            print(f"   Format: {export_format}")
            print(f"   Components: {', '.join(components)}")
            
            # Check if input directory exists
            input_path = Path(input_dir)
            if not input_path.exists():
                print(f"[ERROR] Input directory not found: {input_dir}")
                return False
            
            # Export with graceful degradation
            success = self.cli_ops.robust_export_data(
                input_path, output_name, export_format, components
            )
            
            if success:
                print("[OK] Export completed successfully")
                print(f"   Files created in data/exports/")
            else:
                print("[ERROR] Export failed (check logs for details)")
            
            return success
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            print(f"[ERROR] Export failed: {e}")
            return False
    
    async def system_health_check(self) -> bool:
        """Perform comprehensive system health check"""
        try:
            print("[CHECK] System Health Check")
            print("=" * 30)
            
            # System monitor removed - using basic health status
            health_report = {"status": "monitoring_not_implemented"}
            
            # Display overall status
            status_emoji = {
                'healthy': '[HEALTHY]',
                'warning': '[WARNING]',
                'critical': '[CRITICAL]',
                'unknown': '[UNKNOWN]'
            }
            
            overall_emoji = status_emoji.get(health_report.overall_status.value, '[UNKNOWN]')
            print(f"{overall_emoji} Overall Status: {health_report.overall_status.value.upper()}")
            
            # Display degradation level
            degradation_emoji = {
                'full': '[HEALTHY]',
                'limited': '[WARNING]',
                'essential': '[DEGRADED]',
                'emergency': '[CRITICAL]'
            }
            
            deg_emoji = degradation_emoji.get(health_report.degradation_level.value, '[UNKNOWN]')
            print(f"{deg_emoji} Degradation Level: {health_report.degradation_level.value.upper()}")
            
            # Display uptime
            uptime_hours = health_report.uptime_seconds / 3600
            print(f"[TIME]  Uptime: {uptime_hours:.1f} hours")
            
            print("\n[HEALTH] Key Metrics:")
            for metric_name, metric in health_report.metrics.items():
                metric_emoji = status_emoji.get(metric.status.value, '[UNKNOWN]')
                unit = f" {metric.unit}" if metric.unit and metric.unit != 'boolean' else ""
                print(f"   {metric_emoji} {metric.name}: {metric.value:.1f}{unit} - {metric.message}")
            
            # Display recommendations
            if health_report.recommendations:
                print("\n[TIP] Recommendations:")
                for i, rec in enumerate(health_report.recommendations, 1):
                    print(f"   {i}. {rec}")
            else:
                print("\n[OK] No recommendations - system running well")
            
            return health_report.overall_status.value in ['healthy', 'warning']
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            print(f"[ERROR] Health check failed: {e}")
            return False
    
    async def analyze_grounded_theory(self, input_dir: str, output_dir: str = None) -> bool:
        """
        New GT-specific analyze command that processes all interviews together
        """
        try:
            print("[GT] Starting Grounded Theory analysis")
            print("=" * 60)
            
            # Set default output directory with timestamp
            if not output_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = f"reports/gt_{timestamp}"
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Load all interviews at once (GT requires full dataset)
            print(f"[DATA] Loading interviews from: {input_dir}")
            interviews = self.cli_ops.robust_load_interviews(input_dir)
            
            if not interviews:
                print(f"[ERROR] No interviews found in {input_dir}")
                return False
            
            print(f"[DATA] Loaded {len(interviews)} interviews")
            
            # Use the proven working configuration
            from qc_clean.config.methodology_config import MethodologyConfigManager
            config_manager = MethodologyConfigManager()
            config_path = Path("config/methodology_configs/grounded_theory_reliable.yaml")
            
            if not config_path.exists():
                print("[WARNING] Using default GT configuration")
                config = None
            else:
                config = config_manager.load_config_from_path(config_path)
                print(f"[CONFIG] Using configuration: {config_path}")
            
            # Initialize GT workflow with the correct operations context
            from ..workflow.grounded_theory import GroundedTheoryWorkflow
            gt_workflow = GroundedTheoryWorkflow(self.cli_ops, config=config)
            
            # Execute the complete GT workflow
            print("\n[PHASE 1/4] Open Coding...")
            print("[PHASE 2/4] Axial Coding...")
            print("[PHASE 3/4] Selective Coding...")
            print("[PHASE 4/4] Theory Integration...")
            
            results = await gt_workflow.execute_complete_workflow(interviews)
            
            if not results:
                print("[ERROR] GT analysis failed to produce results")
                return False
            
            # DETAILED DATA EXPORT - Add structured JSON/CSV export
            await self._export_detailed_data(results, interviews, output_path)
            
            # Generate reports
            print("\n[REPORTS] Generating reports...")
            from ..utils.autonomous_reporter import AutonomousReporter
            
            if config:
                reporter = AutonomousReporter(config)
            else:
                # Create minimal config for reporter
                from types import SimpleNamespace
                minimal_config = SimpleNamespace(
                    report_formats=['executive_summary', 'technical_report', 'raw_data'],
                    report_depth='comprehensive'
                )
                reporter = AutonomousReporter(minimal_config)
            
            # Generate configured reports
            reports = reporter.generate_all_configured_reports(results, gt_workflow.audit_trail)
            
            # Save reports
            for format_name, content in reports.items():
                if format_name == "raw_data":
                    output_file = output_path / f"gt_report_{format_name}.json"
                else:
                    output_file = output_path / f"gt_report_{format_name}.md"
                
                output_file.write_text(content, encoding='utf-8')
                print(f"   [OK] Generated: {output_file.name}")
            
            # Print summary
            print(f"\n[SUCCESS] Grounded Theory analysis complete!")
            print(f"   Open codes discovered: {len(results.open_codes) if results.open_codes else 0}")
            
            # Handle multiple core categories
            if hasattr(results, 'core_categories') and results.core_categories:
                print(f"   Core categories: {len(results.core_categories)}")
                for cat in results.core_categories[:3]:  # Show first 3
                    print(f"      - {cat.category_name}")
            elif results.core_category:
                print(f"   Core category: {results.core_category.category_name}")
            
            print(f"   Axial relationships: {len(results.axial_relationships) if results.axial_relationships else 0}")
            
            if results.theoretical_model:
                print(f"   Theoretical model: {results.theoretical_model.model_name}")
            
            # Show hierarchy information
            hierarchical_codes = [c for c in results.open_codes if c.parent_id or c.child_codes]
            if hierarchical_codes:
                print(f"   Hierarchical codes: {len(hierarchical_codes)}/{len(results.open_codes)}")
            
            print(f"\n   Reports saved to: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"GT analysis failed: {e}", exc_info=True)
            print(f"[ERROR] GT analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _export_detailed_data(self, results, interviews, output_path):
        """Export detailed structured data in JSON and CSV formats"""
        try:
            from ..export.data_exporter import DataExporter
            from datetime import datetime
            
            print("\n[DETAILED EXPORT] Generating structured data exports...")
            
            # Initialize exporter
            exporter = DataExporter(str(output_path))
            
            # Convert GroundedTheoryResults to DataExporter format
            export_data = self._convert_gt_results_to_export_format(results, interviews)
            
            # Export in multiple formats
            json_path = exporter.export_results(export_data, format='json', filename='detailed_analysis')
            csv_path = exporter.export_results(export_data, format='csv', filename='detailed_analysis')
            
            print(f"   [OK] Detailed JSON: {json_path}")
            print(f"   [OK] Detailed CSV: {csv_path}")
            
        except Exception as e:
            logger.error(f"Detailed export failed: {e}", exc_info=True)
            print(f"   [WARNING] Detailed export failed: {e}")
    
    def _convert_gt_results_to_export_format(self, results, interviews):
        """Convert GroundedTheoryResults to DataExporter expected format"""
        from datetime import datetime
        
        # Convert OpenCode objects to export format
        codes_data = []
        if hasattr(results, 'open_codes') and results.open_codes:
            for code in results.open_codes:
                codes_data.append({
                    'code_name': code.code_name,
                    'description': code.description,
                    'frequency': getattr(code, 'frequency', 1),
                    'properties': getattr(code, 'properties', []),
                    'dimensions': getattr(code, 'dimensions', []),
                    'supporting_quotes': getattr(code, 'supporting_quotes', []),
                    'confidence': getattr(code, 'confidence', 0.0),
                    # Hierarchy fields - previously missing
                    'parent_id': getattr(code, 'parent_id', None),
                    'level': getattr(code, 'level', 0),
                    'child_codes': getattr(code, 'child_codes', [])
                })
        
        # Convert interview data with code associations  
        quotes_data = []
        if interviews:
            for idx, interview in enumerate(interviews):
                interview_id = interview.get('interview_id', f'interview_{idx}')
                content = interview.get('content') or interview.get('text', '')
                
                # Find codes associated with this interview
                associated_codes = []
                if hasattr(results, 'open_codes') and results.open_codes:
                    for code in results.open_codes:
                        # If code has supporting quotes from this interview
                        if hasattr(code, 'supporting_quotes') and code.supporting_quotes:
                            for quote in code.supporting_quotes:
                                if quote and quote.strip() in content:
                                    associated_codes.append(code.code_name)
                                    break
                
                quotes_data.append({
                    'text': content[:500] + '...' if len(content) > 500 else content,  # Truncate for CSV
                    'full_text': content,
                    'speaker': interview_id,
                    'filename': interview.get('filename', 'unknown'),
                    'codes': list(set(associated_codes))  # Remove duplicates
                })
        
        # Convert relationships to simple dict format
        relationships_data = []
        if hasattr(results, 'axial_relationships') and results.axial_relationships:
            for rel in results.axial_relationships:
                relationships_data.append({
                    'central_category': rel.central_category,
                    'related_category': rel.related_category,
                    'relationship_type': rel.relationship_type,
                    'conditions': getattr(rel, 'conditions', []),
                    'consequences': getattr(rel, 'consequences', []),
                    'strength': getattr(rel, 'strength', 0.0)
                })
        
        # Convert core categories
        core_categories_data = []
        if hasattr(results, 'core_categories') and results.core_categories:
            for cat in results.core_categories:
                core_categories_data.append({
                    'category_name': cat.category_name,
                    'description': getattr(cat, 'description', ''),
                    'properties': getattr(cat, 'properties', []),
                    'related_codes': getattr(cat, 'related_codes', [])
                })
        
        return {
            'codes': codes_data,
            'quotes': quotes_data,
            'relationships': relationships_data,
            'core_categories': core_categories_data,
            'metadata': {
                'total_interviews': len(interviews) if interviews else 0,
                'total_codes': len(codes_data),
                'total_relationships': len(relationships_data),
                'total_core_categories': len(core_categories_data),
                'analysis_timestamp': datetime.now().isoformat(),
                'methodology': 'grounded_theory'
            }
        }
    
    async def run_methodology_analysis(self, 
                                      config_path: Path,
                                      input_path: Path, 
                                      output_path: Path,
                                      audit_trail_path: Optional[Path] = None) -> bool:
        """Execute autonomous methodology analysis"""
        try:
            print(f"[METHODOLOGY] Starting methodology analysis")
            print(f"   Configuration: {config_path}")
            print(f"   Input: {input_path}")
            print(f"   Output: {output_path}")
            
            # Load configuration
            from qc_clean.config.methodology_config import MethodologyConfigManager
            config_manager = MethodologyConfigManager()
            config = config_manager.load_config_from_path(config_path)
            
            print(f"   Methodology: {config.methodology}")
            print(f"   Coding depth: {config.coding_depth}")
            print(f"   Report formats: {', '.join(config.report_formats)}")
            
            # Load data  
            interviews = self.cli_ops.robust_load_interviews(input_path)
            
            if not interviews:
                print(f"[ERROR] No interviews found in {input_path}")
                return False
            
            print(f"[DATA] Loaded {len(interviews)} interviews")
            
            # Execute GT workflow with configuration
            from ..workflow.grounded_theory import GroundedTheoryWorkflow
            gt_workflow = GroundedTheoryWorkflow(self.cli_ops, config)
            
            print("[ANALYSIS] Executing grounded theory workflow...")
            results = await gt_workflow.execute_complete_workflow(interviews)
            
            # Generate reports based on configuration
            from ..utils.autonomous_reporter import AutonomousReporter
            reporter = AutonomousReporter(config)
            reports = reporter.generate_all_configured_reports(results, gt_workflow.audit_trail)
            
            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save reports
            print(f"[REPORTS] Generating {len(reports)} report formats...")
            for format_name, content in reports.items():
                if format_name == "raw_data":
                    output_file = output_path / f"gt_report_{format_name}.json"
                else:
                    output_file = output_path / f"gt_report_{format_name}.md"
                
                output_file.write_text(content, encoding='utf-8')
                print(f"   Generated: {output_file}")
            
            # Save audit trail if requested  
            if audit_trail_path and gt_workflow.audit_trail:
                audit_trail_path.parent.mkdir(parents=True, exist_ok=True)
                audit_trail_path.write_text(gt_workflow.audit_trail.to_json(), encoding='utf-8')
                print(f"   Audit trail: {audit_trail_path}")
                
                # Also generate human-readable audit report
                audit_report_path = audit_trail_path.parent / f"gt_audit_report.md"
                audit_report_path.write_text(gt_workflow.audit_trail.export_audit_report(), encoding='utf-8')
                print(f"   Audit report: {audit_report_path}")
                
                # Generate methodology compliance report
                compliance_report_path = audit_trail_path.parent / f"gt_compliance_report.md"
                compliance_report_path.write_text(gt_workflow.audit_trail.export_methodology_compliance_report(), encoding='utf-8')
                print(f"   Compliance report: {compliance_report_path}")
            
            # Print summary
            print(f"\n[SUCCESS] Methodology analysis complete!")
            if results.core_category:
                print(f"   Core category: {results.core_category.category_name}")
            if results.theoretical_model:
                print(f"   Theoretical model: {results.theoretical_model.model_name}")
            print(f"   Open codes: {len(results.open_codes) if results.open_codes else 0}")
            print(f"   Relationships: {len(results.axial_relationships) if results.axial_relationships else 0}")
            print(f"   Memos generated: {len(results.supporting_memos) if results.supporting_memos else 0}")
            print(f"   Reports saved to: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Methodology analysis failed: {e}")
            print(f"[ERROR] Methodology analysis failed: {e}")
            return False
    
    async def system_status_summary(self):
        """Display system status summary"""
        try:
            print("[HEALTH] System Status Summary")
            print("=" * 30)
            
            # Get fail-fast manager status
            status = fail_fast_manager.get_system_status()
            
            print(f"System Status: {status['system_status'].upper()}")
            print(f"Fail-Fast Mode: {status['fail_fast_mode']}")
            print(f"Capabilities Status:")
            
            for cap_name, cap_info in status['capabilities'].items():
                status_icon = "[OK]" if cap_info['available'] else "[ERROR]"
                error_info = ""
                
                if cap_info['error_count'] > 0:
                    error_info = f" ({cap_info['error_count']} errors)"
                
                required_info = " (REQUIRED)" if cap_info.get('required', False) else ""
                
                print(f"   {status_icon} {cap_name.replace('_', ' ').title()}{error_info}{required_info}")
            
            # Operation summary
            op_summary = self.cli_ops.get_operation_summary()
            print(f"\nSession ID: {op_summary['session_id']}")
            
            if op_summary['operation_log']:
                print(f"Recent Operations:")
                for log_entry in op_summary['operation_log'][-5:]:  # Last 5
                    print(f"   • {log_entry}")
            
        except Exception as e:
            logger.error(f"Status summary failed: {e}")
            print(f"[ERROR] Status summary failed: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            print("\n[CLEANUP] Cleaning up...")
            
            # Monitoring functions removed - no lazy implementations
            
            # Cleanup CLI operations
            await self.cli_ops.cleanup()
            
            # Final status
            duration = datetime.now() - self.start_time
            print(f"[OK] Session completed (duration: {duration})")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            print(f"[WARNING]  Cleanup had issues: {e}")


async def main():
    """Main CLI entry point with robust error handling"""
    parser = argparse.ArgumentParser(
        description="Robust Qualitative Coding Analysis CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', choices=['analyze', 'process', 'export', 'health', 'status', 'methodology'],
                       help='Command to execute')
    parser.add_argument('--input', '-i', help='Input directory path')
    parser.add_argument('--output', '-o', help='Output directory path')
    parser.add_argument('--format', '-f', choices=['csv', 'excel'], default='csv',
                       help='Export format')
    parser.add_argument('--components', '-c', nargs='+', 
                       choices=['quotes', 'codes', 'speakers', 'entities'],
                       default=['quotes', 'codes'],
                       help='Components to export')
    parser.add_argument('--validation-mode', '-v', choices=['academic', 'exploratory', 'production'],
                       default='balanced', help='Validation mode')
    parser.add_argument('--config', help='Configuration file path for methodology analysis')
    parser.add_argument('--audit-trail', help='Output path for audit trail JSON')
    
    args = parser.parse_args()
    
    # Initialize robust CLI
    robust_cli = RobustCLI()
    
    try:
        # Initialize system
        init_success = await robust_cli.initialize()
        if not init_success:
            print("[ERROR] System initialization failed")
            return 1
        
        # Execute command
        success = False
        
        if args.command == 'analyze':
            # New GT-specific analyze command
            if not args.input:
                print("[ERROR] Input directory required for GT analysis")
                print("Usage: python -m src.qc.cli_robust analyze --input data/interviews/folder --output reports/output")
                return 1
            
            success = await robust_cli.analyze_grounded_theory(
                args.input, args.output
            )
        
        elif args.command == 'process':
            if not args.input:
                print("[ERROR] Input directory required for processing")
                return 1
            
            success = await robust_cli.process_interviews_robust(
                args.input, args.output, args.validation_mode
            )
        
        elif args.command == 'export':
            success = await robust_cli.export_data_robust(
                args.input, args.output, args.format, args.components
            )
        
        elif args.command == 'health':
            success = await robust_cli.system_health_check()
        
        elif args.command == 'status':
            await robust_cli.system_status_summary()
            success = True
        
        elif args.command == 'methodology':
            if not args.config:
                print("[ERROR] Configuration file required for methodology analysis")
                return 1
            if not args.input:
                print("[ERROR] Input directory required for methodology analysis")
                return 1
                
            success = await robust_cli.run_methodology_analysis(
                Path(args.config), Path(args.input), 
                Path(args.output) if args.output else Path("reports/methodology"),
                Path(args.audit_trail) if args.audit_trail else None
            )
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n[STOPPED]  Operation interrupted by user")
        return 130
    
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"[ERROR] CRITICAL ERROR: {e}")
        print("   Check logs for detailed error information")
        return 1
    
    finally:
        # Always cleanup
        try:
            await robust_cli.cleanup()
        except:
            pass  # Don't fail on cleanup errors


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)