#!/usr/bin/env python3
"""
Offline prompt testing script - test prompts without API calls.

Usage:
    python scripts/test_prompts_offline.py

This script allows you to:
1. View generated prompts for different queries
2. Compare prompt structures
3. Validate prompt quality
4. Test prompt variations
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.chat.prompting import build_prompt
from app.core.kb import load_kb, set_kb
from rag.retrieval import retrieve


def print_prompt_analysis(system_prompt: str, user_prompt: str, query: str):
    """Print detailed analysis of a prompt."""
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)
    
    print("\n📋 SYSTEM PROMPT:")
    print("-" * 80)
    print(system_prompt)
    print(f"\nLength: {len(system_prompt)} characters")
    
    print("\n📝 USER PROMPT:")
    print("-" * 80)
    print(user_prompt[:2000])  # First 2000 chars
    if len(user_prompt) > 2000:
        print(f"\n... (truncated, total length: {len(user_prompt)} characters)")
    print(f"\nLength: {len(user_prompt)} characters")
    
    # Analyze prompt quality
    print("\n🔍 PROMPT QUALITY METRICS:")
    print("-" * 80)
    
    metrics = {
        "Has synthesis instruction": (
            "synthesize" in system_prompt.lower() or 
            "synthesize" in user_prompt.lower() or
            "conversational" in system_prompt.lower()
        ),
        "Has entity grouping": (
            "entity" in system_prompt.lower() and 
            "entity" in user_prompt.lower()
        ),
        "Has citation instruction": (
            "citation" in system_prompt.lower() or 
            "citation" in user_prompt.lower()
        ),
        "Has don't copy instruction": (
            "don't copy" in system_prompt.lower() or 
            "don't copy" in user_prompt.lower() or
            "verbatim" in system_prompt.lower()
        ),
        "System prompt length OK": 200 < len(system_prompt) < 2000,
        "User prompt length OK": 100 < len(user_prompt) < 5000,
    }
    
    for metric, value in metrics.items():
        status = "✅" if value else "❌"
        print(f"{status} {metric}")
    
    print()


def test_query(kb, query: str, top_k: int = 5):
    """Test a query and show the generated prompt."""
    print(f"\n🔍 Testing query: '{query}'")
    print("-" * 80)
    
    # Retrieve chunks
    results = retrieve(
        query,
        inv=kb.inverted_index,
        chunk_by_id=kb.chunk_by_id,
        top_k=top_k,
    )
    
    retrieved_chunks = [r.chunk for r in results]
    print(f"Retrieved {len(retrieved_chunks)} chunks")
    
    # Build prompt
    system_prompt, user_prompt = build_prompt(query, retrieved_chunks)
    
    # Analyze
    print_prompt_analysis(system_prompt, user_prompt, query)
    
    # Show retrieved chunks summary
    print("📦 RETRIEVED CHUNKS:")
    print("-" * 80)
    for i, chunk in enumerate(retrieved_chunks[:5], 1):
        chunk_id = chunk.get("id", "unknown")
        entity = chunk.get("metadata", {}).get("entity", "Unknown")
        text_preview = chunk.get("text", "")[:80]
        print(f"{i}. [{chunk_id}] {entity}: {text_preview}...")
    
    return system_prompt, user_prompt


def main():
    """Main function."""
    print("=" * 80)
    print("OFFLINE PROMPT TESTING TOOL")
    print("Test prompts without using API tokens")
    print("=" * 80)
    
    # Load knowledge base
    print("\nLoading knowledge base...")
    kb = load_kb(
        chunks_path="index/chunks.json",
        inverted_index_path="index/inverted_index.json",
    )
    set_kb(kb)
    print("✅ Knowledge base loaded")
    
    # Test queries
    test_queries = [
        "What's Tae's work experience like?",
        "What AI experience does Tae have?",
        "Tell me about Tae's backend projects",
        "What frameworks has Tae used?",
    ]
    
    prompts = {}
    for query in test_queries:
        system_prompt, user_prompt = test_query(kb, query)
        prompts[query] = (system_prompt, user_prompt)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Tested {len(test_queries)} queries")
    print(f"All prompts generated successfully")
    print("\n💡 Tips:")
    print("- Check that all prompts encourage synthesis (not verbatim copying)")
    print("- Verify entity grouping is present")
    print("- Ensure citation instructions are clear")
    print("- Compare prompt lengths - they should be reasonable")
    print("\nTo test with actual LLM (uses tokens), use the API or test scripts")


if __name__ == "__main__":
    main()


