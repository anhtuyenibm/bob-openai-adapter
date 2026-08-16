# Bob OpenAI Adapter

A small Python adapter that lets plain-text Bob Shell calls use an OpenAI-style chat-completions call pattern.

The adapter is intended for code that already uses a simple pattern like:

```python
client.chat.completions.create(...)
```

It is not a full OpenAI SDK implementation. It supports a practical subset of chat-completion behavior and keeps Bob-specific limitations explicit.

## Repository

<https://github.com/anhtuyenibm/bob-openai-adapter>

## What it supports

- `BobOpenAI` client object
- `client.chat.completions.create(...)`
- plain-text `system`, `user`, and `assistant` messages
- response access through `response.choices[0].message.content`
- `to_dict()`, `model_dump()`, and `to_json()` response helpers
- configurable timeout and retry settings
- Bob options such as `chat_mode`, `approval_mode`, and `extra_args`
- optional working directory through `cwd`
- optional streaming-shaped response objects

## What it does not support

The adapter currently does not implement:

- full OpenAI SDK object parity
- tools or function calling
- multimodal message content
- async APIs
- embeddings, fine-tuning, or other non-chat APIs
- true real-time streaming from the Bob process

OpenAI-style parameters such as `temperature`, `max_tokens`, and `top_p` are accepted for caller compatibility, but Bob Shell does not use them through this adapter.

## Prerequisites

- Python 3.8+
- Bob Shell installed separately and available on `PATH`, unless `bob_command` points to a specific executable

Check Bob availability:

```bash
bob --version
```

## Installation

Install from the repository using SSH (no credential prompt):

```bash
python3 -m pip install "git+ssh://git@github.com/anhtuyenibm/bob-openai-adapter.git"
```

This uses your machine's SSH key — the same one used for `git clone`. Ensure
your key is added to your GitHub account before running this command.

For development from a local checkout:

```bash
git clone git@github.com:anhtuyenibm/bob-openai-adapter.git
cd bob-openai-adapter
python3 -m pip install -e ".[dev]"
```

## Basic usage

```python
import os
from bob_openai_adapter import BobOpenAI

client = BobOpenAI(api_key=os.getenv("BOBSHELL_API_KEY"))

response = client.chat.completions.create(
    model="bob",
    messages=[
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "Explain what a Python list is."},
    ],
)

print(response.choices[0].message.content)
```

`api_key` is accepted for compatibility with callers that expect an API-key field. Bob Shell authentication is handled by the local Bob Shell setup.

## Configuration

```python
client = BobOpenAI(
    api_key=os.getenv("BOBSHELL_API_KEY"),
    bob_command="bob",
    timeout=300.0,
    max_retries=1,
    retry_delay=1.0,
    retry_backoff=2.0,
    max_retry_delay=60.0,
    cwd="/path/to/workspace",
)
```

## Common parameters

| Parameter | Behavior |
|---|---|
| `messages` | Converted into a plain-text prompt and sent to Bob stdin |
| `model` | Passed to Bob with `-m` when the value is not `"bob"` |
| `chat_mode` | Passed to Bob with `--chat-mode` |
| `approval_mode` | Passed to Bob with `--approval-mode` |
| `extra_args` | Appended to the Bob CLI command |
| `stream` | Returns chunk-shaped response objects after Bob output is available |
| `temperature`, `max_tokens`, `top_p`, etc. | Accepted for compatibility and ignored |

Example with Bob-specific options:

```python
response = client.chat.completions.create(
    model="bob",
    messages=[{"role": "user", "content": "Review this workspace."}],
    chat_mode="advanced",
    approval_mode="yolo",
    extra_args=["--include-directories", "/path/to/project"],
)
```

## Streaming-shaped responses

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

The current implementation invokes Bob with `subprocess.run(...)`. Output is collected after Bob exits. The streaming path provides chunk-shaped objects for simple compatibility, not true live streaming.

## Error handling

```python
from bob_openai_adapter import BobAPIError, BobConnectionError, BobError, BobTimeoutError

try:
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hello"}],
    )
except BobConnectionError:
    print("Bob executable was not found or could not be started.")
except BobTimeoutError:
    print("Bob call timed out.")
except BobAPIError as exc:
    print(f"Bob returned an error: {exc}")
except BobError as exc:
    print(f"Adapter error: {exc}")
```

## Tests

Run the unit tests:

```bash
python3 -m pytest -q
```

The unit tests use temporary fake Bob executables and do not require a live Bob installation.

Optional real-Bob smoke test:

```bash
RUN_REAL_BOB_TESTS=1 python3 examples/test_real_bob_version.py
```

That smoke test only calls `bob -v`. It does not send a prompt and does not require `BOBSHELL_API_KEY`.
