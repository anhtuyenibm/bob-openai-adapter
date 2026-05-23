# Installation

This project is packaged as a normal Python package. The import name remains:

```python
from bob_openai_adapter import BobOpenAI
```

## Local editable install

From the repository root:

```bash
python3 -m pip install -e .
```

For development tools:

```bash
python3 -m pip install -e ".[dev]"
```

## Install from a Git repository

After the project is committed to GitHub/GitHub Enterprise:

```bash
python3 -m pip install "git+ssh://git@github.ibm.com/<org>/bob-openai-adapter.git"
```

or, for a specific branch:

```bash
python3 -m pip install "git+ssh://git@github.ibm.com/<org>/bob-openai-adapter.git@main"
```

## Build a distributable wheel

```bash
python3 -m pip install build
python3 -m build
```

This creates files under `dist/`, for example:

```text
dist/bob_openai_adapter-0.1.0-py3-none-any.whl
```

Users can install that wheel directly:

```bash
python3 -m pip install dist/bob_openai_adapter-0.1.0-py3-none-any.whl
```

## Runtime requirement

Bob Shell must be installed separately and available through `bob` on `PATH`, unless callers pass a custom `bob_command`.

```bash
bob --version
```
