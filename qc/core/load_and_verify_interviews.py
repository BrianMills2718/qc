"""
Script to load all 103 interviews and verify they fit within the 1M token context window.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from qc.parsing.docx_parser import DOCXParser
from qc.utils.token_counter import TokenCounter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_all_interview_files(base_dir: Path) -> List[Path]:
    """Find all DOCX interview files in the data directory."""
    interview_files = []
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.docx') and not file.startswith('~$'):  # Skip temp files
                file_path = Path(root) / file
                interview_files.append(file_path)
    
    return sorted(interview_files)


def load_all_interviews_with_metadata(interview_files: List[Path]) -> Tuple[str, int, List[Dict]]:
    """
    Load all interviews with metadata markers for traceability.
    
    Returns:
        - Combined text with metadata markers
        - Total token count
        - List of interview metadata
    """
    parser = DOCXParser()
    token_counter = TokenCounter()
    
    all_content = []
    interview_metadata = []
    total_words = 0
    
    for i, file_path in enumerate(interview_files, 1):
        try:
            # Parse the interview
            interview_data = parser.parse_interview_file(file_path)
            
            # Create content with metadata markers
            content_with_metadata = f"""
=== INTERVIEW {i:03d}: {interview_data['metadata']['file_name']} ===
WORD_COUNT: {interview_data['metadata']['word_count']}
SOURCE: {file_path}

{interview_data['content']}

=== END INTERVIEW {i:03d} ===
"""
            all_content.append(content_with_metadata)
            
            # Collect metadata
            metadata = {
                'interview_id': f'INT_{i:03d}',
                'file_name': interview_data['metadata']['file_name'],
                'file_path': str(file_path),
                'word_count': interview_data['metadata']['word_count'],
                'estimated_tokens': interview_data['estimated_tokens']
            }
            interview_metadata.append(metadata)
            total_words += interview_data['metadata']['word_count']
            
            logger.info(f"Loaded Interview {i:03d}: {interview_data['metadata']['file_name']} "
                       f"({interview_data['metadata']['word_count']} words)")
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            # Continue with other files
    
    # Combine all content
    full_text = "\n\n".join(all_content)
    
    # Count total tokens
    total_tokens = token_counter.count_tokens(full_text)
    
    return full_text, total_tokens, interview_metadata


def generate_summary_report(total_tokens: int, interview_metadata: List[Dict]) -> str:
    """Generate a summary report of the loaded interviews."""
    report = f"""
=== INTERVIEW LOADING SUMMARY ===

Total Interviews Loaded: {len(interview_metadata)}
Total Token Count: {total_tokens:,}
Token Limit: 1,048,576 (Gemini 2.5 Flash)
Available Tokens: {1_048_576 - total_tokens:,}

Can fit in single context? {'YES [SUCCESS]' if total_tokens < 900_000 else 'NO [FAILURE]'}
(Using 900K as safe limit to leave room for prompt and output)

Token Distribution:
- Average tokens per interview: {total_tokens // len(interview_metadata):,}
- Min tokens: {min(m['estimated_tokens'] for m in interview_metadata):,}
- Max tokens: {max(m['estimated_tokens'] for m in interview_metadata):,}

Interview Categories:
- AI Methods interviews: {sum(1 for m in interview_metadata if 'AI' in m['file_name'])}
- Africa interviews: {sum(1 for m in interview_metadata if 'africa' in m['file_path'].lower())}

Top 5 Largest Interviews:
"""
    
    # Sort by token count and show top 5
    sorted_metadata = sorted(interview_metadata, 
                           key=lambda x: x['estimated_tokens'], 
                           reverse=True)
    
    for i, meta in enumerate(sorted_metadata[:5], 1):
        report += f"{i}. {meta['file_name']}: {meta['estimated_tokens']:,} tokens\n"
    
    return report


def save_combined_interviews(full_text: str, output_path: Path):
    """Save the combined interview text for inspection."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
    logger.info(f"Saved combined interviews to: {output_path}")


def main():
    """Main function to load and verify all interviews."""
    # Find interview directory
    data_dir = project_root / "data" / "interviews"
    
    if not data_dir.exists():
        logger.error(f"Interview directory not found: {data_dir}")
        return
    
    # Find all interview files
    logger.info("Finding all interview files...")
    interview_files = find_all_interview_files(data_dir)
    logger.info(f"Found {len(interview_files)} interview files")
    
    # Load all interviews
    logger.info("Loading all interviews with metadata...")
    full_text, total_tokens, interview_metadata = load_all_interviews_with_metadata(interview_files)
    
    # Generate and print summary report
    report = generate_summary_report(total_tokens, interview_metadata)
    print(report)
    
    # Save combined text for inspection (optional)
    output_dir = project_root / "output" / "combined"
    save_combined_interviews(full_text, output_dir / "all_interviews_combined.txt")
    
    # Save metadata as JSON
    import json
    with open(output_dir / "interview_metadata.json", 'w') as f:
        json.dump({
            'total_interviews': len(interview_metadata),
            'total_tokens': total_tokens,
            'interviews': interview_metadata
        }, f, indent=2)
    
    logger.info(f"Metadata saved to: {output_dir / 'interview_metadata.json'}")
    
    # Return status
    if total_tokens < 900_000:
        logger.info("SUCCESS: All interviews can fit in a single LLM context!")
        return True
    else:
        logger.warning("WARNING: Interviews exceed safe token limit. Consider batching.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)