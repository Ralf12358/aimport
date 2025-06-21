# Publishing to PyPI

This guide explains how to publish the `aimport` package to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org/account/register/)
2. **API Token**: Generate an API token in your PyPI account settings
3. **twine**: Install twine for uploading packages

```bash
uv add --dev twine
# or globally: pipx install twine
```

## Publishing Steps

### 1. Verify Everything is Ready

```bash
# Run all tests
./test.sh

# Clean previous builds
rm -rf dist/ build/ aimport.egg-info/

# Build the package
uv build
```

### 2. Check Package Quality

```bash
# Verify the built package
twine check dist/*
```

### 3. Test Upload (Optional)

Test on PyPI's test instance first:

```bash
# Upload to test PyPI
twine upload --repository testpypi dist/*

# Test installation from test PyPI
pip install --index-url https://test.pypi.org/simple/ aimport
```

### 4. Upload to PyPI

```bash
# Upload to real PyPI
twine upload dist/*
```

You'll be prompted for your PyPI credentials or API token.

### 5. Verify Installation

```bash
# Test installation from PyPI
pip install aimport
```

## Package Details

- **Package Name**: `aimport`
- **Version**: `1.1.0`
- **License**: MIT
- **Python Requirement**: >=3.8

## What's Included

The published package includes:

- Main module: `aimport/__init__.py`
- Documentation: `README.md`
- License: `LICENSE`
- Tests: `tests/` directory

## Security Notes

- Never commit your PyPI API token to version control
- Use environment variables or `.pypirc` file for credentials
- Consider using GitHub Actions for automated publishing
