# Installation Guide

## Requirements

- Python 3.7 or newer
- Bob Shell installed separately

Verify Bob Shell:

```bash
bob --version
```

## Install by Copying the Module

```bash
cp bob_openai_adapter.py /path/to/your/project/
```

Then import it:

```python
from bob_openai_adapter import BobOpenAI
```

## Optional Environment Variable

The client accepts `BOBSHELL_API_KEY` for compatibility with code that expects an API-key-style constructor argument:

```bash
export BOBSHELL_API_KEY="..."
```

The current adapter stores this value but does not pass it to Bob Shell. Bob Shell authentication remains the responsibility of the Bob Shell environment.

## Minimal Smoke Test

```python
from bob_openai_adapter import BobOpenAI

client = BobOpenAI()
response = client.chat.completions.create(
    model="bob",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

## Local Tests

```bash
python test_adapter.py
```

The tests use a fake Bob command created at runtime, so they can validate adapter behavior without calling a live Bob installation.
