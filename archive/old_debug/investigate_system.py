#!/usr/bin/env python3
"""
Quick investigation script to check system readiness
Run this before attempting full analysis
"""

import os
import sys
import json
import yaml
from pathlib import Path

print("=" * 60)
print("QUALITATIVE CODING SYSTEM - READINESS CHECK")
print("=" * 60)

# 1. Check Python environment
print("\n1. PYTHON ENVIRONMENT:")
print(f"   Python Version: {sys.version}")
print(f"   Current Directory: {os.getcwd()}")

# 2. Check critical dependencies
print("\n2. DEPENDENCIES:")
try:
    import litellm
    print("   ✓ LiteLLM installed")
except ImportError:
    print("   ✗ LiteLLM NOT installed - run: pip install litellm")

try:
    import neo4j
    print("   ✓ Neo4j driver installed")
except ImportError:
    print("   ✗ Neo4j driver NOT installed - run: pip install neo4j")

try:
    from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
    print("   ✓ GT Workflow importable")
except ImportError as e:
    print(f"   ✗ GT Workflow import failed: {e}")

# 3. Check configuration files
print("\n3. CONFIGURATION FILES:")
config_dir = Path("config/methodology_configs")
if config_dir.exists():
    configs = list(config_dir.glob("*.yaml"))
    print(f"   Found {len(configs)} config files:")
    for cfg in configs[:3]:
        print(f"     - {cfg.name}")
        # Check for model configuration
        try:
            with open(cfg, 'r') as f:
                config_data = yaml.safe_load(f)
                model = config_data.get('model_preference', 'Not specified')
                print(f"       Model: {model}")
        except:
            pass
else:
    print("   ✗ Config directory not found!")

# 4. Check API keys
print("\n4. API KEYS:")
gemini_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
if gemini_key:
    print(f"   ✓ Gemini API key found (length: {len(gemini_key)})")
else:
    print("   ✗ Gemini API key NOT found in environment")
    print("     Set with: export GEMINI_API_KEY='your-key-here'")

openai_key = os.environ.get('OPENAI_API_KEY')
if openai_key:
    print(f"   ✓ OpenAI API key found (length: {len(openai_key)})")

# 5. Check Neo4j connection
print("\n5. NEO4J DATABASE:")
try:
    from neo4j import GraphDatabase
    # Try to connect (might fail if not running)
    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'password')
    
    print(f"   URI: {uri}")
    print(f"   User: {user}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()['count']
            print(f"   ✓ Connected! Nodes in database: {count}")
        driver.close()
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("     Is Neo4j running? Try: neo4j start")
except ImportError:
    print("   ✗ Neo4j driver not installed")

# 6. Check interview data
print("\n6. INTERVIEW DATA:")
interview_dir = Path("data/interviews")
if interview_dir.exists():
    interview_folders = [d for d in interview_dir.iterdir() if d.is_dir()]
    print(f"   Found {len(interview_folders)} interview folders:")
    for folder in interview_folders[:3]:
        files = list(folder.glob("*"))
        print(f"     - {folder.name}: {len(files)} files")
        # Check first file format
        if files:
            first_file = files[0]
            print(f"       Sample: {first_file.name}")
            with open(first_file, 'r', encoding='utf-8') as f:
                content = f.read(200)
                if content.startswith('{'):
                    print("       Format: JSON")
                elif content.startswith('Interview'):
                    print("       Format: Plain text transcript")
                else:
                    print("       Format: Unknown")
else:
    print("   ✗ Interview directory not found!")

# 7. Check output directories
print("\n7. OUTPUT DIRECTORIES:")
for dir_name in ['reports', 'data/memos', 'logs']:
    dir_path = Path(dir_name)
    if dir_path.exists():
        print(f"   ✓ {dir_name}/ exists")
        # Check for recent files
        if dir_name == 'data/memos':
            memos = list(dir_path.glob("theoretical_memo_*.json"))
            if memos:
                latest = max(memos, key=lambda p: p.stat().st_mtime)
                print(f"     Latest memo: {latest.name}")
    else:
        print(f"   ✗ {dir_name}/ not found - will be created on first run")

# 8. System readiness summary
print("\n" + "=" * 60)
print("READINESS SUMMARY:")
print("=" * 60)

issues = []
warnings = []

# Check critical issues
if not gemini_key and not openai_key:
    issues.append("No LLM API keys found")

if 'neo4j' not in sys.modules:
    issues.append("Neo4j driver not installed")

if not Path("config/methodology_configs").exists():
    issues.append("Configuration files missing")

# Report
if issues:
    print("❌ CRITICAL ISSUES FOUND:")
    for issue in issues:
        print(f"   - {issue}")
    print("\n⚠️  Fix these issues before running analysis!")
else:
    print("✅ SYSTEM APPEARS READY FOR TESTING")
    print("\nNext step: Run a test analysis:")
    print("  python -m src.qc.cli_robust analyze \\")
    print("    data/interviews/ai_interviews_3_for_test \\")
    print("    --output reports/test_run")

print("\n" + "=" * 60)