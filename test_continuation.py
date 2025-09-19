#!/usr/bin/env python3
"""Quick test of continuation functionality."""

import argparse
import os
import sys

from mcp_coder.cli.commands.prompt import execute_prompt

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))



def test_continuation():
    """Test continuation functionality with a real stored response."""
    
    print("Testing continuation functionality...")
    
    # Use the actual stored response file
    stored_file = ".mcp-coder/responses/response_2025-09-19T07-27-37.json"
    
    if not os.path.exists(stored_file):
        print(f"Error: Stored response file not found: {stored_file}")
        return False
    
    # Create test arguments for continuation
    args = argparse.Namespace(
        prompt="Can you also show me how to read that file back?",
        continue_from=stored_file,
        verbosity="verbose"
    )
    
    try:
        print(f"\nLoading from: {stored_file}")
        print(f"New prompt: {args.prompt}")
        print("\n" + "="*50)
        
        # Note: This would normally call Claude API, but we just want to test 
        # the continuation logic loads the file properly
        from mcp_coder.cli.commands.prompt import (
            _build_context_prompt,
            _load_previous_chat,
        )

        # Test loading the previous chat
        previous_context = _load_previous_chat(stored_file)
        print("✅ Successfully loaded previous context")
        print(f"Previous prompt: {previous_context['previous_prompt']}")
        print(f"Previous response: {previous_context['previous_response'][:100]}...")
        
        # Test building context prompt
        enhanced_prompt = _build_context_prompt(previous_context, args.prompt)
        print("\n✅ Successfully built enhanced prompt")
        print("Enhanced prompt:")
        print(enhanced_prompt)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing continuation: {e}")
        return False


if __name__ == "__main__":
    success = test_continuation()
    sys.exit(0 if success else 1)
