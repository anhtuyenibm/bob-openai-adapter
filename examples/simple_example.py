#!/usr/bin/env python3
"""
Simple example demonstrating Bob OpenAI Adapter usage.

Run this file to see the adapter in action:
    python examples/simple_example.py
"""

import os
from bob_openai_adapter import BobOpenAI

def main():
    print("Bob OpenAI Adapter - Simple Example")
    print("=" * 60)
    
    # Initialize the client
    print("\n1. Initializing Bob client...")
    client = BobOpenAI(
        api_key=os.getenv("BOBSHELL_API_KEY"),  # Optional, for compatibility
        timeout=300.0,
        max_retries=3
    )
    print("✓ Client initialized")
    
    # Simple question
    print("\n2. Asking a simple question...")
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "What is 2+2? Answer with just the number."}
        ]
    )
    print(f"Question: What is 2+2?")
    print(f"Answer: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens}")
    
    # With system message
    print("\n3. Using system message...")
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": "What is Python?"}
        ]
    )
    print(f"Question: What is Python?")
    print(f"Answer: {response.choices[0].message.content[:100]}...")
    
    # Using Bob's code mode
    print("\n4. Using Bob's code mode...")
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "Write a one-line Python function to add two numbers"}
        ],
        chat_mode="code"
    )
    print(f"Request: Write a one-line Python function to add two numbers")
    print(f"Response: {response.choices[0].message.content[:150]}...")
    
    # OpenAI-compatible parameters (accepted but ignored)
    print("\n5. Using OpenAI parameters (accepted but ignored by Bob)...")
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "Say hello"}
        ],
        temperature=0.7,      # Ignored
        max_tokens=50,        # Ignored
        top_p=0.9            # Ignored
    )
    print(f"Response: {response.choices[0].message.content}")
    print("Note: temperature, max_tokens, top_p were logged but not used")
    
    print("\n" + "=" * 60)
    print("✓ All examples completed successfully!")
    print("\nNext steps:")
    print("- Check examples.py for more advanced usage")
    print("- Read README.md for full documentation")
    print("- Run python -m pytest -q to test the adapter")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nMake sure Bob Shell is installed and available in PATH")
        print("Check with: bob --version")
