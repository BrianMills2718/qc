"""
Query Command Handler - Natural language queries through CLI
"""

import logging
import sys
from typing import Dict, Any, Optional
from ..api_client import APIClient, APIClientError
from ..formatters.human_formatter import format_query_results
from ..formatters.json_formatter import format_json_output
from ..formatters.table_formatter import format_table_output

logger = logging.getLogger(__name__)

# Query history for interactive mode
QUERY_HISTORY = []


def handle_query_command(args) -> int:
    """Handle the query command"""
    
    try:
        # Initialize API client
        api_client = APIClient(base_url=args.api_url)
        
        # Check server connectivity
        if not api_client.health_check():
            print("❌ Cannot connect to API server.")
            print("Please start the server with: python start_server.py")
            return 1
        
        print("✅ Connected to API server")
        
        if args.interactive:
            return handle_interactive_mode(api_client, args.format)
        else:
            return handle_single_query(api_client, args.query_text, args.format)
            
    except Exception as e:
        logger.error(f"Unexpected error in query command: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
        return 1


def handle_single_query(api_client: APIClient, query_text: str, output_format: str) -> int:
    """Handle a single query execution"""
    
    if not query_text or not query_text.strip():
        print("❌ No query provided")
        return 1
    
    print(f"🔍 Executing query: {query_text}")
    print()
    
    try:
        result = api_client.natural_language_query(query_text)
        
        # Check if query was successful
        if not result.get('success', True):
            error_msg = result.get('error', 'Query failed without error message')
            print(f"❌ Query failed: {error_msg}")
            return 1
        
        # Format and display results
        if output_format == 'json':
            output = format_json_output(result)
        elif output_format == 'table':
            output = format_table_output(result)
        else:  # human format
            output = format_query_results(result)
        
        print(output)
        return 0
        
    except APIClientError as e:
        print(f"❌ Query failed: {e}")
        return 1


def handle_interactive_mode(api_client: APIClient, output_format: str) -> int:
    """Handle interactive query mode"""
    
    print("🔄 Interactive Query Mode")
    print("Enter your natural language queries below.")
    print("Type 'exit', 'quit', or press Ctrl+C to exit.")
    print("Type 'help' for available commands.")
    print("=" * 50)
    print()
    
    # Configure readline for better user experience
    try:
        import readline
        readline.parse_and_bind("tab: complete")
        
        # Load history if available
        for query in QUERY_HISTORY:
            readline.add_history(query)
    except ImportError:
        pass  # readline not available on all systems
    
    query_count = 0
    
    while True:
        try:
            # Get user input
            try:
                query = input("qc> ").strip()
            except EOFError:
                print("\nExiting...")
                break
            
            # Handle empty input
            if not query:
                continue
            
            # Handle special commands
            if query.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            elif query.lower() == 'help':
                print_interactive_help()
                continue
            elif query.lower() == 'history':
                print_query_history()
                continue
            elif query.lower() == 'clear':
                clear_screen()
                continue
            elif query.lower().startswith('format '):
                new_format = query.lower().split(' ', 1)[1]
                if new_format in ['json', 'table', 'human']:
                    output_format = new_format
                    print(f"Output format changed to: {output_format}")
                else:
                    print("Invalid format. Available: json, table, human")
                continue
            
            # Execute query
            query_count += 1
            print(f"\n[Query {query_count}] {query}")
            print("-" * 40)
            
            try:
                result = api_client.natural_language_query(query)
                
                # Add to history
                if query not in QUERY_HISTORY:
                    QUERY_HISTORY.append(query)
                    if len(QUERY_HISTORY) > 50:  # Keep last 50 queries
                        QUERY_HISTORY.pop(0)
                
                # Check if query was successful
                if not result.get('success', True):
                    error_msg = result.get('error', 'Query failed without error message')
                    print(f"❌ Query failed: {error_msg}")
                    print()
                    continue
                
                # Format and display results
                if output_format == 'json':
                    output = format_json_output(result)
                elif output_format == 'table':
                    output = format_table_output(result)
                else:  # human format
                    output = format_query_results(result)
                
                print(output)
                print()
                
            except APIClientError as e:
                print(f"❌ Query failed: {e}")
                print()
            
        except KeyboardInterrupt:
            print("\n\nExiting interactive mode...")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print()
    
    return 0


def print_interactive_help() -> None:
    """Print help for interactive mode"""
    print()
    print("INTERACTIVE MODE COMMANDS:")
    print("-" * 30)
    print("  help        - Show this help message")
    print("  history     - Show query history")
    print("  clear       - Clear screen")
    print("  format <fmt> - Change output format (json, table, human)")
    print("  exit/quit   - Exit interactive mode")
    print("  Ctrl+C      - Exit interactive mode")
    print()
    print("EXAMPLE QUERIES:")
    print("-" * 15)
    print("  Find codes related to communication")
    print("  Show me themes about user experience")
    print("  What recommendations do we have for improving the process?")
    print("  List all codes with high frequency")
    print()


def print_query_history() -> None:
    """Print query history"""
    if not QUERY_HISTORY:
        print("No query history available")
        return
    
    print()
    print("QUERY HISTORY:")
    print("-" * 15)
    for i, query in enumerate(QUERY_HISTORY[-10:], 1):  # Show last 10
        print(f"{i:2d}. {query}")
    print()


def clear_screen() -> None:
    """Clear the screen"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')