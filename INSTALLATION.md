# Installation

The package import name is:

```python
from bob_openai_adapter import BobOpenAI
```

## Install from GitHub

Using HTTPS:

```bash
python3 -m pip install "git+https://github.com/anhtuyenibm/bob-openai-adapter.git"
```

Using SSH:

```bash
python3 -m pip install "git+ssh://git@github.com/anhtuyenibm/bob-openai-adapter.git"
```

For a specific branch or tag, append `@<name>`:

```bash
python3 -m pip install "git+https://github.com/anhtuyenibm/bob-openai-adapter.git@main"
```

## Local development install

From a local checkout:

```bash
git clone https://github.com/anhtuyenibm/bob-openai-adapter.git
cd bob-openai-adapter
python3 -m pip install -e ".[dev]"
```

The editable install keeps Python pointed at the local source tree, which is convenient while changing the adapter.

## Build a wheel

```bash
python3 -m pip install build
python3 -m build
```

The built artifacts are written under `dist/`.

Install the wheel directly:

```bash
python3 -m pip install dist/bob_openai_adapter-0.1.0-py3-none-any.whl
```

## Runtime requirement

Bob Shell must be installed separately and available as `bob` on `PATH`, unless the caller passes a custom `bob_command`.

```bash
bob --version
```

The adapter accepts `api_key` and reads `BOBSHELL_API_KEY` for compatibility with OpenAI-style caller code. Bob Shell authentication itself is handled by the local Bob Shell setup.

## Verify the install

```bash
python3 - <<'PY'
from bob_openai_adapter import BobOpenAI
print(BobOpenAI)
PY
```

Run the unit tests from the repository root:

```bash
python3 -m pytest -q
```
