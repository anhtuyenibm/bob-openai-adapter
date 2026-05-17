# Bob OpenAI Adapter

A lightweight Python adapter that exposes Bob Shell through an OpenAI-style chat-completions interface.

The adapter is intended for simple plain-text integrations that already use a pattern similar to:

```python
client.chat.completions.create(...)
```

It accepts selected OpenAI-style parameters for caller compatibility. Parameters that Bob Shell does not support, such as `temperature` and `max_tokens`, are accepted but logged and ignored.

## Scope

This project currently supports a practical subset of chat-completions behavior:

- plain text chat messages
- `client.chat.completions.create(...)`
- response access through `response.choices[0].message.content`
- configurable timeout and retry settings
- Bob-specific options such as `chat_mode` and `approval_mode`
- optional additional Bob CLI arguments through `extra_args`
- optional working directory through `cwd`

It is not a full implementation of the OpenAI Python SDK. Advanced features such as tools/function calling, multimodal content, async APIs, embeddings, and exact SDK object parity are outside the current scope.

## Prerequisites

- Python 3.7+
- Bob Shell installed and available on `PATH`

Check Bob availability:

```bash
bob --version
```

## Basic Usage

```python
import os
from bob_openai_adapter import BobOpenAI

client = BobOpenAI(api_key=os.getenv("BOBSHELL_API_KEY"))

response = client.chat.completions.create(
    model="bob",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
)

print(response.choices[0].message.content)
```

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

`api_key` is accepted for compatibility with callers that already expect an API-key field. Bob Shell authentication is handled by Bob Shell itself unless future Bob versions require otherwise.

## Chat Completion Parameters

Supported or accepted parameters include:

| Parameter | Behavior |
|---|---|
| `messages` | Converted into a text prompt and sent to Bob stdin |
| `model` | Passed to Bob as `-m` unless the value is `"bob"` |
| `stream` | Returns an iterator of chunk objects after Bob output is available |
| `chat_mode` | Passed to Bob as `--chat-mode` |
| `approval_mode` | Passed to Bob as `--approval-mode` |
| `extra_args` | Appended to the Bob CLI command |
| `temperature`, `max_tokens`, `top_p`, etc. | Accepted, logged, and ignored |

## Streaming Note

The current implementation invokes Bob with `subprocess.run(...)`, so output is collected after Bob exits. The `stream=True` path exposes an iterator of chunks for API-shape compatibility, but it is not true real-time streaming.

## Examples

### Bob chat mode

```python
response = client.chat.completions.create(
    model="bob",
    messages=[{"role": "user", "content": "Write a small Python function."}],
    chat_mode="code",
)
```

### Additional Bob arguments

```python
response = client.chat.completions.create(
    model="bob",
    messages=[{"role": "user", "content": "Review this workspace."}],
    chat_mode="advanced",
    extra_args=["--include-directories", "/path/to/project"],
)
```

### Streaming-shaped response

```python
stream = client.chat.completions.create(
    model="bob",
    messages=[{"role": "user", "content": "Explain the code."}],
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.get("content")
    if content:
        print(content, end="", flush=True)
```

## Error Handling

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

Run the unit tests with:

```bash
python test_adapter.py
```

These tests use temporary fake Bob executables and do not require a live Bob installation.

To run the optional real-Bob smoke test, use:

```bash
RUN_REAL_BOB_TESTS=1 python test_real_bob_version.py
```

That test only calls `bob -v`. It verifies that the Bob executable is available and returns version/help text; it does not send a prompt and does not require `BOBSHELL_API_KEY`. To use a non-default executable path, set `BOB_COMMAND`:

```bash
RUN_REAL_BOB_TESTS=1 BOB_COMMAND=/path/to/bob python test_real_bob_version.py
```

## Limitations

- The adapter targets simple chat-completion integrations, not complete SDK compatibility.
- OpenAI sampling parameters are accepted but not applied.
- Streaming is chunk-shaped output after process completion, not real-time process streaming.
- Retries should be configured carefully because Bob may perform tool or file-system actions depending on mode and configuration.
- Token usage is estimated from whitespace-separated words.

## Files

- `bob_openai_adapter.py` — core adapter implementation
- `examples.py` — usage examples
- `simple_example.py` — minimal runnable example
- `test_adapter.py` — tests using a temporary fake Bob command
- `QUICKSTART.md` — short usage guide
- `INSTALLATION.md` — installation notes
