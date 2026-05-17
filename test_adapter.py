"""
Tests for Bob OpenAI Adapter.

The tests use temporary fake Bob executables so they do not require a live Bob
installation. Run with:

    python test_adapter.py
"""

from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path

from bob_openai_adapter import BobOpenAI, BobAPIError, BobConnectionError


def _make_fake_bob(script_body: str) -> str:
    tmpdir = tempfile.mkdtemp(prefix="bob_adapter_test_")
    script = Path(tmpdir) / "fake_bob.py"
    script.write_text(script_body)
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script)


def _success_bob() -> str:
    return _make_fake_bob(
        f"""#!{sys.executable}
import json
import sys

args = sys.argv[1:]
prompt = sys.stdin.read()
if "stream-json" in args:
    print(json.dumps({{"content": "hello "}}))
    print(json.dumps({{"content": "world"}}))
else:
    print("fake bob response")
"""
    )


def _failing_bob() -> str:
    return _make_fake_bob(
        f"""#!{sys.executable}
import sys
print("fake failure", file=sys.stderr)
sys.exit(7)
"""
    )


def test_initialization() -> None:
    client = BobOpenAI(api_key="test_key", bob_command=_success_bob())
    assert client is not None
    assert hasattr(client, "chat")


def test_basic_completion() -> None:
    client = BobOpenAI(bob_command=_success_bob(), max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Say hello"}],
    )
    assert response.choices[0].message.content == "fake bob response"
    assert response.choices[0].finish_reason == "stop"
    assert response.model == "bob"


def test_response_serialization() -> None:
    client = BobOpenAI(bob_command=_success_bob(), max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hi"}],
    )
    data = response.to_dict()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"] == "fake bob response"
    assert response.model_dump() == data
    assert isinstance(response.to_json(), str)


def test_streaming_shape() -> None:
    client = BobOpenAI(bob_command=_success_bob(), max_retries=0)
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


def test_accepted_ignored_parameters() -> None:
    client = BobOpenAI(bob_command=_success_bob(), max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7,
        max_tokens=100,
        top_p=0.9,
    )
    assert response.choices[0].message.content == "fake bob response"


def test_extra_args_are_accepted() -> None:
    client = BobOpenAI(bob_command=_success_bob(), max_retries=0)
    response = client.chat.completions.create(
        model="bob",
        messages=[{"role": "user", "content": "Hello"}],
        extra_args=["--hide-intermediary-output"],
    )
    assert response.choices[0].message.content == "fake bob response"


def test_nonzero_exit() -> None:
    client = BobOpenAI(bob_command=_failing_bob(), max_retries=0)
    try:
        client.chat.completions.create(
            model="bob",
            messages=[{"role": "user", "content": "test"}],
        )
        raise AssertionError("Expected BobAPIError")
    except BobAPIError as exc:
        assert exc.status_code == 7


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


def main() -> int:
    tests = [
        test_initialization,
        test_basic_completion,
        test_response_serialization,
        test_streaming_shape,
        test_accepted_ignored_parameters,
        test_extra_args_are_accepted,
        test_nonzero_exit,
        test_missing_command,
    ]

    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"PASS {test.__name__}")
        except Exception as exc:
            print(f"FAIL {test.__name__}: {exc}")

    print(f"\nTest Results: {passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
