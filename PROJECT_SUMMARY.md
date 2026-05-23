# Bob OpenAI Adapter - Project Summary

## Purpose

This project provides a small Python adapter that lets simple chat-completion-style callers invoke Bob Shell through a familiar interface.

The main goal is to reduce application-level changes for code that already uses a pattern such as:

```python
client.chat.completions.create(...)
```

Internally, the adapter still invokes Bob Shell through the command line, passes the prompt through standard input, and reads the response from standard output.

## Current Capabilities

- OpenAI-style client object: `BobOpenAI`
- Chat endpoint: `client.chat.completions.create(...)`
- Plain text message formatting for `system`, `user`, and `assistant` roles
- Response object with `choices[0].message.content`
- Basic `to_dict()`, `model_dump()`, and `to_json()` helpers
- Timeout and retry configuration
- Bob options for `chat_mode`, `approval_mode`, and `model`
- Optional `extra_args` for additional Bob CLI flags
- Optional `cwd` for running Bob from a selected workspace
- Standard-library-only implementation

## Current Boundaries

This package is an adapter for a practical subset of chat-completion usage. It is not a full OpenAI SDK replacement.

Current limitations include:

- no tools/function-calling API
- no multimodal message content
- no async client
- no embeddings or fine-tuning APIs
- no exact SDK object parity
- simulated streaming shape rather than true real-time streaming
- estimated usage counts rather than tokenizer-based counts

## Architecture

```text
Application code
    ↓
BobOpenAI client
    ↓
Chat completions facade
    ↓
Prompt formatter
    ↓
BobExecutor
    ↓
Bob Shell subprocess
```

## Design Notes

### OpenAI-style surface

The adapter keeps the public call shape close to common chat-completions usage, while being explicit that unsupported OpenAI parameters are ignored.

### Bob subprocess execution

Bob is invoked through `subprocess.run(...)`. The adapter passes prompts through stdin and reads stdout/stderr after process completion.

### Transport settings

The client exposes timeout and retry settings. Retry behavior should be used carefully for agentic Bob modes because repeated invocations may repeat external actions.

### Bob-specific extension point

The `extra_args` parameter allows callers to pass Bob CLI options that are not explicitly modeled by the adapter yet.

## Testing

`test_adapter.py` uses a temporary fake Bob executable so the adapter behavior can be tested without requiring a live Bob installation.

Run:

```bash
python test_adapter.py
```

## Recommended Next Improvements

- Add validation for Bob enum values such as `chat_mode`, `approval_mode`, and `output_format`
- Add a safer retry policy that distinguishes timeout, nonzero exit, and empty output
- Implement true streaming with `subprocess.Popen(...)` if Bob output format supports it reliably
- Expand response-object compatibility where needed by consuming applications
- Split the single-file module into a package layout if the adapter grows
- Add CI tests with fake Bob fixtures

## Summary

The current package is a compact wrapper for simple Bob Shell chat calls. It is suitable as a starting point for internal integrations that need plain-text chat-completion behavior, with clear boundaries around features that are not implemented yet.


## Optional Real-Bob Smoke Test

`test_real_bob_version.py` provides an opt-in integration smoke test for environments where Bob is installed. It runs only when `RUN_REAL_BOB_TESTS=1` is set and calls `bob -v`, so it does not require `BOBSHELL_API_KEY` or a live chat request.
