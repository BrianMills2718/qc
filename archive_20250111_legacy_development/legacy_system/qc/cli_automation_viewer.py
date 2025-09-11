#!/usr/bin/env python3
"""
CLI Automation Viewer for Qualitative Coding Analysis Tool

Displays automated qualitative coding results including quotes, entities, 
codes, and their relationships with confidence scores and reasoning.
"""

import asyncio
import click
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .core.neo4j_manager import EnhancedNeo4jManager
from .core.schema_config import create_research_schema

logger = logging.getLogger(__name__)


class AutomationResultsViewer:
    """Viewer for automated qualitative coding results"""
    
    def __init__(self):
        self.neo4j = None
        self.schema = create_research_schema()
    
    async def setup(self):
        """Initialize database connections"""
        self.neo4j = EnhancedNeo4jManager()
        await self.neo4j.connect()
    
    async def cleanup(self):
        """Clean up database connections"""
        if self.neo4j:
            await self.neo4j.close()
    
    def format_quote_display(self, quote: Dict[str, Any], show_entities: bool = True, 
                           show_codes: bool = True, context_lines: int = 2) -> str:
        """Format a quote for display with optional entity/code information"""
        lines = []
        
        # Quote header
        lines.append(f"📝 Quote {quote['id']} (Lines {quote['line_start']}-{quote['line_end']})")
        lines.append(f"   Interview: {quote['interview_id']}")
        if quote.get('speaker'):
            lines.append(f"   Speaker: {quote['speaker']}")
        if quote.get('confidence'):
            confidence = float(quote['confidence'])
            conf_icon = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🔴"
            lines.append(f"   Confidence: {conf_icon} {confidence:.2f}")
        
        # Quote text
        lines.append("")
        lines.append(f"   \"{quote['text']}\"")
        
        # Context if available
        if context_lines > 0 and quote.get('context'):
            lines.append("")
            lines.append(f"   Context: {quote['context']}")
        
        # Entity relationships
        if show_entities and quote.get('entities'):
            lines.append("")
            lines.append("   🔗 Entities:")
            for entity in quote['entities']:
                conf_str = f" ({entity.get('confidence', 0.0):.2f})" if entity.get('confidence') else ""
                lines.append(f"      • {entity['name']} ({entity['entity_type']}){conf_str}")
        
        # Code relationships
        if show_codes and quote.get('codes'):
            lines.append("")
            lines.append("   📋 Codes:")
            for code in quote['codes']:
                conf_str = f" ({code.get('confidence', 0.0):.2f})" if code.get('confidence') else ""
                lines.append(f"      • {code['name']} ({code.get('code_type', 'code')}){conf_str}")
        
        return "\n".join(lines)
    
    def format_automation_summary(self, summary: Dict[str, Any]) -> str:
        """Format automation summary for display"""
        lines = []
        lines.append("🤖 AUTOMATED QUALITATIVE CODING RESULTS")
        lines.append("=" * 50)
        lines.append("")
        
        # Overall statistics
        stats = summary.get('statistics', {})
        lines.append("📊 Overall Statistics:")
        lines.append(f"   Interviews Processed: {stats.get('interviews_processed', 0)}")
        lines.append(f"   Quotes Extracted: {stats.get('quotes_extracted', 0)}")
        lines.append(f"   Quote Nodes Created: {stats.get('quote_nodes', 0)}")
        lines.append(f"   Entities Detected: {stats.get('entities_detected', 0)}")
        lines.append(f"   Entity Relationships: {stats.get('entity_relationships', 0)}")
        lines.append(f"   Code Assignments: {stats.get('code_assignments', 0)}")
        lines.append("")
        
        # Confidence distribution
        conf_dist = summary.get('confidence_distribution', {})
        if conf_dist:
            lines.append("🎯 Confidence Distribution:")
            lines.append(f"   High (≥0.8): {conf_dist.get('high', 0)} items")
            lines.append(f"   Medium (0.6-0.8): {conf_dist.get('medium', 0)} items")
            lines.append(f"   Low (<0.6): {conf_dist.get('low', 0)} items")
            lines.append("")
        
        # Processing timeline
        timeline = summary.get('timeline', {})
        if timeline:
            lines.append("⏱️ Processing Timeline:")
            for interview_id, info in timeline.items():
                lines.append(f"   {interview_id}: {info.get('quotes', 0)} quotes, "
                           f"{info.get('entities', 0)} entities")
        
        return "\n".join(lines)
    
    def format_pattern_display(self, patterns: List[Dict[str, Any]]) -> str:
        """Format automatically detected patterns for display"""
        lines = []
        lines.append("🔍 AUTOMATICALLY DETECTED PATTERNS")
        lines.append("=" * 50)
        lines.append("")
        
        for i, pattern in enumerate(patterns, 1):
            lines.append(f"Pattern {i}: {pattern.get('name', 'Unnamed Pattern')}")
            lines.append(f"   Type: {pattern.get('pattern_type', 'unknown')}")
            lines.append(f"   Confidence: {pattern.get('confidence', 0.0):.2f}")
            lines.append(f"   Frequency: {pattern.get('frequency', 0)} occurrences")
            
            if pattern.get('description'):
                lines.append(f"   Description: {pattern['description']}")
            
            # Supporting quotes
            if pattern.get('supporting_quotes'):
                lines.append("   📝 Supporting Evidence:")
                for quote in pattern['supporting_quotes'][:3]:  # Show first 3
                    lines.append(f"      • \"{quote['text'][:100]}...\" "
                               f"({quote['interview_id']}:{quote['line_start']})")
                if len(pattern['supporting_quotes']) > 3:
                    remaining = len(pattern['supporting_quotes']) - 3
                    lines.append(f"      ... and {remaining} more quotes")
            
            lines.append("")
        
        return "\n".join(lines)


# CLI Command Group
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def automation(ctx, verbose):
    """Commands for viewing automated qualitative coding results"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    if verbose:
        logging.basicConfig(level=logging.DEBUG)


@automation.command()
@click.option('--interview-ids', '-i', multiple=True, 
              help='Specific interview IDs to analyze (default: all)')
@click.option('--confidence-threshold', '-c', type=float, default=0.0,
              help='Minimum confidence threshold (default: 0.0)')
@click.option('--show-reasoning', '-r', is_flag=True,
              help='Show LLM reasoning for decisions')
@click.pass_context
async def show_results(ctx, interview_ids, confidence_threshold, show_reasoning):
    """Display complete automated qualitative coding results"""
    viewer = AutomationResultsViewer()
    await viewer.setup()
    
    try:
        # Get automation summary
        summary = await viewer.neo4j.get_automation_summary(list(interview_ids) if interview_ids else None)
        
        # Display summary
        click.echo(viewer.format_automation_summary(summary))
        
        # Show detailed results if verbose
        if ctx.obj.get('verbose'):
            click.echo("\n" + "="*50)
            click.echo("DETAILED RESULTS")
            click.echo("="*50)
            
            # Get quotes with assignments
            for interview_id in (interview_ids or summary.get('interview_ids', [])):
                quotes = await viewer.neo4j.get_quotes_with_assignments(
                    interview_id, include_confidence=True
                )
                
                filtered_quotes = [q for q in quotes if q.get('confidence', 0) >= confidence_threshold]
                
                if filtered_quotes:
                    click.echo(f"\n📋 Interview: {interview_id}")
                    click.echo("-" * 30)
                    
                    for quote in filtered_quotes:
                        click.echo(viewer.format_quote_display(quote, show_entities=True, show_codes=True))
                        click.echo("")
    
    except Exception as e:
        click.echo(f"❌ Error displaying automation results: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            click.echo(traceback.format_exc(), err=True)
    
    finally:
        await viewer.cleanup()


@automation.command()
@click.argument('interview_id')
@click.option('--line-range', '-l', type=str, help='Line range (e.g., "10-50")')
@click.option('--context-lines', '-c', type=int, default=2, 
              help='Number of context lines to show (default: 2)')
@click.option('--show-entities', '-e', is_flag=True, default=True,
              help='Show entity relationships')
@click.option('--show-codes', '-k', is_flag=True, default=True,
              help='Show code assignments')
@click.pass_context
async def browse_quotes(ctx, interview_id, line_range, context_lines, show_entities, show_codes):
    """Interactive quote browser with automated assignments"""
    viewer = AutomationResultsViewer()
    await viewer.setup()
    
    try:
        # Parse line range if provided
        start_line, end_line = None, None
        if line_range:
            try:
                parts = line_range.split('-')
                start_line = int(parts[0])
                end_line = int(parts[1]) if len(parts) > 1 else start_line
            except ValueError:
                click.echo(f"❌ Invalid line range format: {line_range}", err=True)
                return
        
        # Get quotes with assignments
        quotes = await viewer.neo4j.get_quotes_with_assignments(interview_id, include_confidence=True)
        
        # Filter by line range if specified
        if start_line is not None:
            quotes = [q for q in quotes if 
                     start_line <= q.get('line_start', 0) <= (end_line or start_line)]
        
        if not quotes:
            click.echo(f"📭 No quotes found for interview {interview_id}" + 
                      (f" in lines {line_range}" if line_range else ""))
            return
        
        click.echo(f"📋 Found {len(quotes)} quotes in interview {interview_id}")
        if line_range:
            click.echo(f"   Lines {line_range}")
        click.echo("")
        
        # Display quotes
        for quote in quotes:
            click.echo(viewer.format_quote_display(
                quote, 
                show_entities=show_entities, 
                show_codes=show_codes,
                context_lines=context_lines
            ))
            click.echo("")
    
    except Exception as e:
        click.echo(f"❌ Error browsing quotes: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            click.echo(traceback.format_exc(), err=True)
    
    finally:
        await viewer.cleanup()


@automation.command()
@click.option('--cross-interview', '-x', is_flag=True,
              help='Analyze patterns across interviews')
@click.option('--auto-themes', '-t', is_flag=True,
              help='Show automatically detected themes')
@click.option('--confidence-threshold', '-c', type=float, default=0.7,
              help='Minimum confidence threshold for patterns (default: 0.7)')
@click.pass_context
async def explore_patterns(ctx, cross_interview, auto_themes, confidence_threshold):
    """Show automatically detected patterns and themes"""
    viewer = AutomationResultsViewer()
    await viewer.setup()
    
    try:
        # Get automated patterns
        patterns = await viewer.neo4j.get_automated_patterns(
            interview_ids=None,  # All interviews for cross-interview analysis
            min_confidence=confidence_threshold
        )
        
        if not patterns:
            click.echo(f"🔍 No patterns found with confidence ≥ {confidence_threshold}")
            return
        
        # Filter patterns based on options
        if cross_interview:
            patterns = [p for p in patterns if p.get('cross_interview', False)]
        
        if auto_themes:
            patterns = [p for p in patterns if p.get('pattern_type') == 'theme']
        
        # Display patterns
        click.echo(viewer.format_pattern_display(patterns))
        
        # Show pattern statistics
        if ctx.obj.get('verbose'):
            click.echo("\n" + "="*50)
            click.echo("PATTERN STATISTICS")
            click.echo("="*50)
            
            by_type = {}
            for pattern in patterns:
                ptype = pattern.get('pattern_type', 'unknown')
                by_type[ptype] = by_type.get(ptype, 0) + 1
            
            for ptype, count in by_type.items():
                click.echo(f"   {ptype.title()}: {count} patterns")
    
    except Exception as e:
        click.echo(f"❌ Error exploring patterns: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            click.echo(traceback.format_exc(), err=True)
    
    finally:
        await viewer.cleanup()


# Make commands available for async execution
def run_show_results(interview_ids, confidence_threshold, show_reasoning, verbose=False):
    """Wrapper for async execution"""
    async def _run():
        ctx = click.Context(show_results)
        ctx.obj = {'verbose': verbose}
        await show_results.callback(ctx, interview_ids, confidence_threshold, show_reasoning)
    
    asyncio.run(_run())


def run_browse_quotes(interview_id, line_range=None, context_lines=2, 
                     show_entities=True, show_codes=True, verbose=False):
    """Wrapper for async execution"""
    async def _run():
        ctx = click.Context(browse_quotes)
        ctx.obj = {'verbose': verbose}
        await browse_quotes.callback(ctx, interview_id, line_range, context_lines, 
                                   show_entities, show_codes)
    
    asyncio.run(_run())


def run_explore_patterns(cross_interview=False, auto_themes=False, 
                        confidence_threshold=0.7, verbose=False):
    """Wrapper for async execution"""
    async def _run():
        ctx = click.Context(explore_patterns)
        ctx.obj = {'verbose': verbose}
        await explore_patterns.callback(ctx, cross_interview, auto_themes, confidence_threshold)
    
    asyncio.run(_run())


if __name__ == '__main__':
    automation()