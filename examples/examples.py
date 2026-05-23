"""
Examples showing how to use the Bob OpenAI Adapter.

Run this file to see different usage patterns.
"""

import os
from bob_openai_adapter import BobOpenAI, BobError, BobAPIError, BobTimeoutError


def example_basic_chat():
    """Basic chat completion."""
    print("=" * 60)
    print("Example 1: Basic Chat")
    print("=" * 60)
    
    # Initialize client
    client = BobOpenAI(api_key=os.getenv("BOBSHELL_API_KEY"))
    
    # Create a completion
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
    )
    
    # Access the response
    print(f"Response: {response.choices[0].message.content}")
    print(f"Model: {response.model}")
    print(f"Tokens used: {response.usage.total_tokens}")
    print()


def example_with_chat_mode():
    """Using Bob's chat modes."""
    print("=" * 60)
    print("Example 2: Bob Chat Modes")
    print("=" * 60)
    
    client = BobOpenAI()
    
    # Use code mode for coding tasks
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}
        ],
        chat_mode="code"
    )
    
    print(f"Code mode response:\n{response.choices[0].message.content}")
    print()


def example_streaming():
    """Streaming responses."""
    print("=" * 60)
    print("Example 3: Streaming")
    print("=" * 60)
    
    client = BobOpenAI()
    
    # Stream the response
    stream = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "Tell me a short story about a robot."}
        ],
        stream=True
    )
    
    print("Streaming response:")
    for chunk in stream:
        if chunk.choices[0].delta.get("content"):
            print(chunk.choices[0].delta["content"], end="", flush=True)
    print("\n")


def example_with_transport_config():
    """Custom transport configuration."""
    print("=" * 60)
    print("Example 4: Transport Configuration")
    print("=" * 60)
    
    # Configure retries and timeouts
    client = BobOpenAI(
        timeout=600.0,        # 10 minutes timeout
        max_retries=5,        # Retry up to 5 times
        retry_delay=2.0,      # Start with 2 second delay
        retry_backoff=2.0,    # Double delay each retry
        max_retry_delay=30.0  # Cap at 30 seconds
    )
    
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "Explain quantum computing in simple terms."}
        ]
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print()


def example_error_handling():
    """Error handling."""
    print("=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)
    
    client = BobOpenAI(timeout=1.0)  # Short timeout for demo
    
    try:
        response = client.chat.completions.create(
            model="bob",
            messages=[
                {"role": "user", "content": "Complex task that might timeout"}
            ]
        )
        print(f"Response: {response.choices[0].message.content}")
    except BobTimeoutError as e:
        print(f"Timeout error: {e}")
    except BobAPIError as e:
        print(f"API error: {e} (status code: {e.status_code})")
    except BobError as e:
        print(f"Bob error: {e}")
    print()


def example_openai_compatible_params():
    """OpenAI parameters (accepted but ignored)."""
    print("=" * 60)
    print("Example 6: OpenAI Parameters")
    print("=" * 60)
    
    client = BobOpenAI()
    
    # These parameters are accepted but Bob doesn't use them
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "Hello!"}
        ],
        temperature=0.7,
        max_tokens=100,
        top_p=0.9,
        frequency_penalty=0.5,
        presence_penalty=0.5,
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print("Note: These parameters are logged but Bob doesn't use them")
    print()


def example_multi_turn_conversation():
    """Multi-turn conversation."""
    print("=" * 60)
    print("Example 7: Multi-Turn Conversation")
    print("=" * 60)
    
    client = BobOpenAI()
    
    messages = [
        {"role": "system", "content": "You are a helpful math tutor."},
        {"role": "user", "content": "What is 15 + 27?"},
    ]
    
    # First turn
    response = client.chat.completions.create(
        model="bob",
        messages=messages
    )
    
    assistant_reply = response.choices[0].message.content
    print(f"User: {messages[-1]['content']}")
    print(f"Assistant: {assistant_reply}")
    
    # Continue the conversation
    messages.append({"role": "assistant", "content": assistant_reply})
    messages.append({"role": "user", "content": "Now multiply that by 3"})
    
    # Second turn
    response = client.chat.completions.create(
        model="bob",
        messages=messages
    )
    
    print(f"User: {messages[-1]['content']}")
    print(f"Assistant: {response.choices[0].message.content}")
    print()


def example_response_as_dict():
    """Response as dictionary."""
    print("=" * 60)
    print("Example 8: Response as Dictionary")
    print("=" * 60)
    
    client = BobOpenAI()
    
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "Say hello!"}
        ]
    )
    
    # Convert to dict for JSON serialization
    response_dict = response.to_dict()
    
    import json
    print("Response as JSON:")
    print(json.dumps(response_dict, indent=2))
    print()


def example_custom_bob_command():
    """Custom Bob command path."""
    print("=" * 60)
    print("Example 9: Custom Bob Path")
    print("=" * 60)
    
    # If Bob is in a custom location
    client = BobOpenAI(bob_command="/usr/local/bin/bob")
    
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "Hello from custom Bob path!"}
        ]
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print()


def example_approval_modes():
    """Different approval modes."""
    print("=" * 60)
    print("Example 10: Approval Modes")
    print("=" * 60)
    
    client = BobOpenAI()
    
    # Auto-approve edit tools only
    response = client.chat.completions.create(
        model="bob",
        messages=[
            {"role": "user", "content": "Create a simple Python script"}
        ],
        chat_mode="code",
        approval_mode="auto_edit"
    )
    
    print(f"Response with auto_edit mode:\n{response.choices[0].message.content}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Bob OpenAI Adapter - Examples")
    print("=" * 60 + "\n")
    
    # Run examples
    examples = [
        example_basic_chat,
        example_with_chat_mode,
        example_streaming,
        example_with_transport_config,
        example_error_handling,
        example_openai_compatible_params,
        example_multi_turn_conversation,
        example_response_as_dict,
        # example_custom_bob_command,  # Requires custom path
        example_approval_modes,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Error running {example.__name__}: {e}")
            print()
    
    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)
