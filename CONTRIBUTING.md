# Contributing to Rename Media

Thank you for considering contributing to Rename Media! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Bugs

Before submitting a bug report:
1. Check if the issue already exists in [GitHub Issues](https://github.com/maimik/rename-media/issues)
2. Try the latest version of the project
3. Collect information about the bug (Python version, OS, error messages)

When submitting a bug report, include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version (`python --version`)
- Operating system
- Sample files that cause the issue (if possible)

### Suggesting Features

Feature suggestions are welcome! Please:
1. Check existing issues and discussions first
2. Describe the feature and its use case
3. Explain why it would be useful to most users

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python -m pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

#### Pull Request Guidelines

- Follow existing code style
- Add tests for new functionality
- Update documentation as needed
- Keep changes focused and atomic
- Write clear commit messages

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/maimik/rename-media.git
cd rename-media

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test file
python -m pytest test_renamed_check.py -v
```

### Code Style

- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions focused and not too long
- Use type hints where appropriate
- Follow PEP 8 guidelines

## Project Structure

```
rename-media/
├── rename_media_cli.py    # CLI implementation
├── rename_media_gui.py    # GUI implementation (tkinter)
├── convert_icon.py        # Icon conversion utility
├── test_*.py              # Test files
├── requirements.txt       # Runtime dependencies
├── pyproject.toml         # Project configuration
├── README.md              # Main documentation
├── CONTRIBUTING.md        # This file
├── CHANGELOG.md           # Version history
└── LICENSE                # MIT License
```

## Areas for Contribution

Here are some areas where contributions are especially welcome:

### High Priority
- [ ] Custom filename templates
- [ ] Group files by date into folders
- [ ] Undo/restore original names
- [ ] Parallel file processing

### Medium Priority
- [ ] Export report to CSV/HTML
- [ ] Thumbnail preview in GUI
- [ ] Drag-and-drop support in GUI
- [ ] More metadata extraction options

### Documentation
- [ ] Video tutorials
- [ ] More usage examples
- [ ] Translation to other languages

## Questions?

If you have questions, feel free to:
1. Open a GitHub Issue
2. Start a GitHub Discussion

Thank you for contributing!
