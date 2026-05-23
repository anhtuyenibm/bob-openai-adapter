# Technical Overview: Bob OpenAI Adapter

## Overview

The Bob OpenAI Adapter is a small Python module that exposes Bob Shell through a chat-completions-style interface.

It is designed for applications that already use simple chat-completion calls and want to route those calls to Bob Shell with minimal application-level changes.

## How It Works

Bob Shell is a command-line tool. The adapter translates a list of chat messages into a text prompt, invokes Bob as a subprocess, sends the prompt through stdin, and wraps Bob's stdout in a response object with a familiar structure.

```text
Application → BobOpenAI adapter → Bob subprocess → response object
```

## Main Components

- `BobOpenAI`: main client object
- `Chat` and `Completions`: chat-completion facade
- `BobExecutor`: subprocess execution and error handling
- `TransportConfig`: timeout and retry settings
- `ChatCompletion` and `ChatCompletionChunk`: response objects

## Message Translation

Input messages are converted into a plain text transcript:

```python
[
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello."},
]
```

becomes:

```text
System: You are helpful.

User: Hello.
```

## Parameter Handling

Some parameters map to Bob options. Others are accepted for compatibility but are not applied.

- `model` maps to Bob's model flag when the value is not `"bob"`
- `chat_mode` maps to `--chat-mode`
- `approval_mode` maps to `--approval-mode`
- `extra_args` appends caller-supplied Bob CLI flags
- `temperature`, `max_tokens`, `top_p`, and similar parameters are logged and ignored

## Reliability

The adapter supports configurable timeouts and retries. Because Bob may be configured to use tools or modify files, retry settings should be selected carefully for non-idempotent workflows.

## Streaming Behavior

The current implementation does not stream Bob output in real time. It collects Bob output after process completion and, when `stream=True`, returns chunk-shaped objects for compatibility with simple streaming-style consumers.

## Limitations

The adapter focuses on plain text chat-completion calls. It does not currently implement advanced OpenAI SDK features such as tools/function calling, multimodal content, async calls, embeddings, fine-tuning APIs, or exact object-model parity.

## Intended Use

This package is best treated as a lightweight compatibility layer for internal Bob Shell integrations. It provides a clear starting point and can be expanded as consuming applications require more compatibility.
