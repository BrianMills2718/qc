#!/usr/bin/env python3
"""
INTELLIGENT CONNECTION ANALYSIS - Examine if connections make conversational sense
"""

import json

def analyze_connection_intelligence():
    print("INTELLIGENT CONNECTION ANALYSIS")
    print("=" * 60)
    
    # Load the output data
    with open('output_production/interviews/Focus Group on AI and Methods 7_7.json') as f:
        output_data = json.load(f)
    
    quotes = output_data['quotes']
    
    print("EXAMINING SPECIFIC CONNECTIONS FOR INTELLIGENCE:")
    print("-" * 60)
    
    # Let's examine each connection type with the most detail possible
    connection_examples = {
        'responds_to': [],
        'clarifies': [],
        'supports': [],
        'builds_on': [],
        'challenges': []
    }
    
    # Group quotes by connection type
    for quote in quotes:
        conn_type = quote.get('thematic_connection')
        if conn_type in connection_examples:
            connection_examples[conn_type].append(quote)
    
    # Analyze each connection type for intelligence
    
    print("1. RESPONDS_TO CONNECTIONS:")
    print("-" * 40)
    
    responds_examples = connection_examples['responds_to'][:3]  # First 3
    
    for i, quote in enumerate(responds_examples, 1):
        speaker = quote.get('speaker', {}).get('name', 'Unknown')
        target = quote.get('connection_target', 'Unknown')
        confidence = quote.get('connection_confidence', 'N/A')
        text = quote['text']
        
        print(f"Example {i}: {speaker} -> {target} (confidence: {confidence})")
        print(f"Quote: \"{text[:200]}...\"")
        
        # Analyze intelligence
        if target in text or "I agree" in text or "Yes" in text or speaker != target:
            intelligence = "INTELLIGENT - Shows response pattern"
        else:
            intelligence = "QUESTIONABLE - Unclear response relationship"
        
        print(f"Analysis: {intelligence}")
        print()
    
    print("2. CLARIFIES CONNECTIONS:")
    print("-" * 40)
    
    clarifies_examples = connection_examples['clarifies'][:3]
    
    for i, quote in enumerate(clarifies_examples, 1):
        speaker = quote.get('speaker', {}).get('name', 'Unknown')
        target = quote.get('connection_target', 'Unknown')
        confidence = quote.get('connection_confidence', 'N/A')
        text = quote['text']
        
        print(f"Example {i}: {speaker} -> {target} (confidence: {confidence})")
        print(f"Quote: \"{text[:200]}...\"")
        
        # Look for clarification indicators
        clarification_words = ["no, no", "what I mean", "to clarify", "actually", "specifically", "I think"]
        has_clarification = any(word in text.lower() for word in clarification_words)
        
        if has_clarification or speaker != target:
            intelligence = "INTELLIGENT - Contains clarification language"
        else:
            intelligence = "QUESTIONABLE - No clear clarification pattern"
        
        print(f"Analysis: {intelligence}")
        print()
    
    print("3. SUPPORTS CONNECTIONS:")
    print("-" * 40)
    
    supports_examples = connection_examples['supports'][:3]
    
    for i, quote in enumerate(supports_examples, 1):
        speaker = quote.get('speaker', {}).get('name', 'Unknown')
        target = quote.get('connection_target', 'Unknown')
        confidence = quote.get('connection_confidence', 'N/A')
        text = quote['text']
        
        print(f"Example {i}: {speaker} -> {target} (confidence: {confidence})")
        print(f"Quote: \"{text[:200]}...\"")
        
        # Look for support indicators
        support_words = ["yeah", "yes", "agree", "exactly", "that seems", "no brainer", "good point"]
        has_support = any(word in text.lower() for word in support_words)
        
        if has_support:
            intelligence = "INTELLIGENT - Contains agreement/support language"
        else:
            intelligence = "QUESTIONABLE - No clear support pattern"
        
        print(f"Analysis: {intelligence}")
        print()
    
    print("4. PROBLEMATIC PATTERN ANALYSIS:")
    print("-" * 40)
    
    # Check for suspicious patterns
    target_speakers = [q.get('connection_target') for q in quotes if q.get('connection_target')]
    speaker_names = [q.get('speaker', {}).get('name') for q in quotes if q.get('speaker', {}).get('name')]
    
    print(f"Total quotes: {len(quotes)}")
    print(f"Connection targets mentioned: {len(set(target_speakers))}")
    print(f"Unique speakers: {len(set(speaker_names))}")
    print(f"Target distribution: {dict((t, target_speakers.count(t)) for t in set(target_speakers))}")
    print()
    
    # Check self-connections (suspicious)
    self_connections = 0
    for quote in quotes:
        speaker = quote.get('speaker', {}).get('name')
        target = quote.get('connection_target')
        if speaker == target:
            self_connections += 1
    
    print(f"Self-connections (speaker -> same speaker): {self_connections}")
    
    if self_connections > 0:
        print("WARNING: Self-connections are generally suspicious in conversation analysis")
    
    print()
    
    print("5. OVERALL INTELLIGENCE ASSESSMENT:")
    print("-" * 40)
    
    # Count intelligent vs questionable connections
    intelligent_patterns = 0
    total_analyzed = 0
    
    # Simplified intelligence check across all connections
    for quote in quotes:
        text = quote['text'].lower()
        speaker = quote.get('speaker', {}).get('name', '')
        target = quote.get('connection_target', '')
        
        # Intelligence indicators
        has_response_words = any(word in text for word in ['yes', 'yeah', 'i agree', 'that'])
        has_clarification_words = any(word in text for word in ['no,', 'actually', 'what i mean', 'specifically'])
        has_support_words = any(word in text for word in ['exactly', 'good point', 'seems like'])
        is_different_speakers = speaker != target
        
        if has_response_words or has_clarification_words or has_support_words or is_different_speakers:
            intelligent_patterns += 1
        
        total_analyzed += 1
    
    intelligence_rate = intelligent_patterns / total_analyzed * 100 if total_analyzed > 0 else 0
    
    print(f"Connections showing intelligent patterns: {intelligent_patterns}/{total_analyzed} ({intelligence_rate:.1f}%)")
    
    if intelligence_rate > 80:
        print("ASSESSMENT: HIGH INTELLIGENCE - Most connections show conversational logic")
    elif intelligence_rate > 60:
        print("ASSESSMENT: MODERATE INTELLIGENCE - Many connections make sense")
    elif intelligence_rate > 40:
        print("ASSESSMENT: LOW INTELLIGENCE - Some connections questionable")
    else:
        print("ASSESSMENT: POOR INTELLIGENCE - Many connections appear random")
    
    print()
    print("CONCLUSION:")
    print("-" * 40)
    print("Review the specific examples above to determine if the thematic connections")
    print("represent genuine conversational intelligence or systematic over-assignment.")

if __name__ == "__main__":
    analyze_connection_intelligence()