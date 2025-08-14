# aimport

A minimal library for python: Adding support for smart imports with automatic path resolution.

## Usage

```python
import aimport
```

This automatically adds relevant directories to `sys.path` based on `__aimport__` anchor files found in the directory tree.

## Features

- **Smart path resolution**: Automatically discovers project roots using `__aimport__` anchor files
- **Anchor file content support**: `__aimport__` files can contain paths that will be used instead of the file location
- **Fallback support**: Falls back to `__init__.py` files when no `__aimport__` files are found
- **Priority ordering**: **BREAKING CHANGE v2.0.0**: New paths are now prepended to `sys.path` instead of appended, giving them higher import priority
- **Duplicate prevention**: Avoids adding duplicate paths to `sys.path`
- **Automatic execution**: Works immediately upon import

## Breaking Changes in v2.0.0

⚠️ **Import Priority Change**: Starting with v2.0.0, discovered paths are prepended to `sys.path` instead of appended. This means modules in aimport-discovered directories will take precedence over existing `sys.path` entries. This change ensures that project-local modules are found before system or virtual environment modules.

## How It Works

1. **Anchor File Discovery**: Searches upward from the starting directory for `__aimport__` files
2. **Content Processing**: If an `__aimport__` file contains a valid path, that path is used; otherwise the file's directory is used
3. **Fallback Mechanism**: If no `__aimport__` files are found, falls back to searching for `__init__.py` files
4. **Path Priority**: All discovered paths are added to the beginning of `sys.path` for higher import priority

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
