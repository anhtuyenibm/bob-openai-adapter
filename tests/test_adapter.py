"""
Tests for Bob OpenAI Adapter — covers both v1 and v2 CLI shapes.

The tests use temporary fake Bob executables so they do not require a live Bob
installation. Run with:

    python -m pytest -q

Fake bob design
---------------
Every fake bob script starts by emitting a version string on ``--version``
so the adapter's _detect_bob_version() returns the correct major number.

v1 fake: reads prompt from stdin, prints plain text.
v2 fake: ignores stdin, expects prompt as last positional arg under
         ``bob run``, prints JSON with a ``last_message`` field.
"""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
from pathlib import Path

from bob_openai_adapter import BobOpenAI, BobAPIError, BobConnectionError


# ── Fake-bob factory helpers ──────────────────────────────────────────────────

def _make_fake_bob(script_body: str) -> str:
    """Write *script_body* to a temp executable and return its path."""
    tmpdir = tempfile.mkdtemp(prefix="bob_adapter_test_")
    script = Path(tmpdir) / "fake_bob.py"
    script.write_text(script_body)
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script)


def _v1_success_bob() -> str:
    """
    Fake Bob v1 (1.0.4 shape).

    --version  → prints "1.0.4"
    -o text    → reads stdin, prints plain text answer
    -o stream-json → reads stdin, prints two JSON content lines
    """
    return _make_fake_bob(
        f"""#!{sys.executable}
import json, sys

args = sys.argv[1:]

if "--version" in args:
    print("1.0.4")
    sys.exit(0)

prompt = sys.stdin.read()

if "stream-json" in args:
    print(json.dumps({{"content": "hello "}}))
    print(json.dumps({{"content": "world"}}))
else:
    print("fake bob response")
"""
    )


def _v1_failing_bob() -> str:
    """Fake Bob v1 that always exits non-zero."""
    return _make_fake_bob(
        f"""#!{sys.executable}
import sys
args = sys.argv[1:]
if "--version" in args:
    print("1.0.4")
    sys.exit(0)
print("fake failure", file=sys.stderr)
sys.exit(7)
"""
    )


def _v2_success_bob() -> str:
    """
    Fake Bob v2 shape.

    --version      → prints "2.0.0"
    run --format json <prompt>
                   → prints JSON {"last_message": "fake bob response"}
    run --format stream-json <prompt>
                   → prints two JSON content lines (stream shape unchanged)
    """
    return _make_fake_bob(
        f"""#!{sys.executable}
import json, sys

args = sys.argv[1:]

if "--version" in args:
    print("2.0.0")
    sys.exit(0)

# args[0] == "run"
fmt = "json"
for i, a in enumerate(args):
    if a == "--format" and i + 1 < len(args):
        fmt = args[i + 1]

if fmt == "stream-json":
    print(json.dumps({{"content": "hello "}}))
    print(json.dumps({{"content": "world"}}))
else:
    print(json.dumps({{"last_message": "fake bob response"}}))
"""
    )


def _v2_failing_bob() -> str:
    """Fake Bob v2 that always exits non-zero."""
    return _make_fake_bob(
        f"""#!{sys.executable}
import sys
args = sys.argv[1:]
if "--version" in args:
    print("2.0.0")
    sys.exit(0)
print("fake failure", file=sys.stderr)
sys.exit(7)
"""
    )


# ── Shared assertion helpers ──────────────────────────────────────────────────

def _assert_basic_completion(bob_path: str) -> None:
    client = BobOpenAI(bob_command=bob_path, max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Say hello"}],
    )
    assert response.choices[0].message.content == "fake bob response"
    assert response.choices[0].finish_reason == "stop"
    assert response.model == "bob"


def _assert_streaming(bob_path: str) -> None:
    client = BobOpenAI(bob_command=bob_path, max_retries=0)
    chunks = list(
        client.chat.completions.create(
            model="bob",
            messages=[{"role": "user", "content": "Stream"}],
            stream=True,
        )
    )
    assert chunks[0].choices[0].delta.get("content") == "hello "
    assert chunks[1].choices[0].delta.get("content") == "world"
    assert chunks[-1].choices[0].finish_reason == "stop"


# ── Initialisation ────────────────────────────────────────────────────────────

def test_initialization() -> None:
    client = BobOpenAI(api_key="test_key", bob_command=_v1_success_bob())
    assert client is not None
    assert hasattr(client, "chat")


# ── v1 tests ──────────────────────────────────────────────────────────────────

def test_v1_basic_completion() -> None:
    _assert_basic_completion(_v1_success_bob())


def test_v1_response_serialization() -> None:
    client = BobOpenAI(bob_command=_v1_success_bob(), max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hi"}],
    )
    data = response.to_dict()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"] == "fake bob response"
    assert response.model_dump() == data
    assert isinstance(response.to_json(), str)


def test_v1_streaming_shape() -> None:
    _assert_streaming(_v1_success_bob())


def test_v1_accepted_ignored_parameters() -> None:
    client = BobOpenAI(bob_command=_v1_success_bob(), max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7,
        max_tokens=100,
        top_p=0.9,
    )
    assert response.choices[0].message.content == "fake bob response"


def test_v1_extra_args_are_accepted() -> None:
    client = BobOpenAI(bob_command=_v1_success_bob(), max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hello"}],
        extra_args=["--hide-intermediary-output"],
    )
    assert response.choices[0].message.content == "fake bob response"


def test_v1_nonzero_exit() -> None:
    client = BobOpenAI(bob_command=_v1_failing_bob(), max_retries=0)
    try:
        client.chat.completions.create(
            model="bob",
            messages=[{"role": "user", "content": "test"}],
        )
        raise AssertionError("Expected BobAPIError")
    except BobAPIError as exc:
        assert exc.status_code == 7


# ── v2 tests ──────────────────────────────────────────────────────────────────

def test_v2_basic_completion() -> None:
    _assert_basic_completion(_v2_success_bob())


def test_v2_response_serialization() -> None:
    client = BobOpenAI(bob_command=_v2_success_bob(), max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hi"}],
    )
    data = response.to_dict()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"] == "fake bob response"
    assert response.model_dump() == data
    assert isinstance(response.to_json(), str)


def test_v2_streaming_shape() -> None:
    _assert_streaming(_v2_success_bob())


def test_v2_nonzero_exit() -> None:
    client = BobOpenAI(bob_command=_v2_failing_bob(), max_retries=0)
    try:
        client.chat.completions.create(
            model="bob",
            messages=[{"role": "user", "content": "test"}],
        )
        raise AssertionError("Expected BobAPIError")
    except BobAPIError as exc:
        assert exc.status_code == 7


def test_v2_extra_args_are_accepted() -> None:
    client = BobOpenAI(bob_command=_v2_success_bob(), max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hello"}],
        extra_args=["--hide-intermediary-output"],
    )
    assert response.choices[0].message.content == "fake bob response"


# ── Shared / cross-version tests ──────────────────────────────────────────────

def test_missing_command() -> None:
    client = BobOpenAI(bob_command="definitely_missing_bob_command", max_retries=0)
    try:
        client.chat.completions.create(
            model="bob",
            messages=[{"role": "user", "content": "test"}],
        )
        raise AssertionError("Expected BobConnectionError")
    except BobConnectionError:
        pass
