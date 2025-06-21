# aimport

A minimal library for python: Adding support for smart imports

## Usage

```python
import aimport
```

This automatically adds relevant directories to `sys.path` based on `__aimport__` anchor files found in the directory tree.

## Features

- **Smart path resolution**: Automatically discovers project roots using `__aimport__` files
- **Fallback support**: Falls back to `__init__.py` files when no `__aimport__` files are found
- **Duplicate prevention**: Avoids adding duplicate paths to `sys.path`
- **Automatic execution**: Works immediately upon import

## Testing

The project includes comprehensive unit tests using pytest:

```bash
# Install development dependencies
uv sync --dev

# Run all tests
./test.sh

# Or run pytest directly
uv run pytest tests/ -v
```

### Test Coverage

- 23 comprehensive test cases
- Full coverage of all functions and edge cases
- Integration tests for complex directory structures
- Behavior-focused testing (not implementation details)

## Development

```bash
# Build distribution
python setup.py sdist

# Upload to PyPI
twine upload dist/*
```
