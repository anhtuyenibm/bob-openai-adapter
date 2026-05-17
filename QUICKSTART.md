# Quick Start Guide

## Prerequisites

- Python 3.7+
- Bob Shell installed and available on `PATH`

Check Bob:

```bash
bob --version
```

## Install

Copy the adapter into your project:

```bash
cp bob_openai_adapter.py /path/to/your/project/
```

The adapter uses only the Python standard library.

## Basic Usage

```python
from bob_openai_adapter import BobOpenAI

client = BobOpenAI()

response = client.chat.completions.create(
    model="bob",
    messages=[{"role": "user", "content": "What is Python?"}],
)

print(response.choices[0].message.content)
```

## With a System Message

```python
response = client.chat.completions.create(
    model="bob",
    messages=[
        {"role": "system", "content": "You are a concise coding assistant."},
        {"role": "user", "content": "Write hello world in Python."},
    ],
)
```

## Bob Code Mode

```python
response = client.chat.completions.create(
    model="bob",
    messages=[{"role": "user", "content": "Create a Python function to sort a list."}],
    chat_mode="code",
)
```

## Working Directory

```python
client = BobOpenAI(cwd="/path/to/workspace")
```

## Additional Bob Arguments

```python
response = client.chat.completions.create(
    model="bob",
    messages=[{"role": "user", "content": "Review this project."}],
    chat_mode="advanced",
    extra_args=["--include-directories", "/path/to/project"],
)
```

## Streaming-Shaped Response

```python
stream = client.chat.completions.create(
    model="bob",
    messages=[{"role": "user", "content": "Explain this code."}],
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.get("content")
    if content:
        print(content, end="", flush=True)
```

Note: this adapter currently returns chunk-shaped output after Bob completes. It does not provide true real-time streaming.

## Error Handling

```python
from bob_openai_adapter import BobAPIError, BobConnectionError, BobError, BobTimeoutError

try:
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hello"}],
    )
except BobConnectionError:
    print("Bob executable was not found.")
except BobTimeoutError:
    print("Bob timed out.")
except BobAPIError as exc:
    print(f"Bob returned an error: {exc}")
except BobError as exc:
    print(f"Adapter error: {exc}")
```

## Run Tests

```bash
python test_adapter.py
```

The tests use a temporary fake Bob command and do not require a live Bob installation.
