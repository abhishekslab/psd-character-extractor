# Contributing to PSD Character Extractor

Thank you for your interest in contributing to PSD Character Extractor! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to help maintain a welcoming and inclusive community.

## Getting Started

### Types of Contributions

We welcome many different types of contributions:

- **Bug Reports**: Found a bug? Let us know!
- **Feature Requests**: Have an idea for a new feature?
- **Code Contributions**: Bug fixes, new features, performance improvements
- **Documentation**: Improvements to docs, examples, or tutorials
- **Testing**: Additional test cases, performance testing
- **Community**: Help answer questions, participate in discussions

### Before You Start

1. **Check existing issues** to see if your bug/feature is already reported
2. **Search discussions** for related conversations
3. **Read the documentation** to understand current functionality
4. **Try the examples** to familiarize yourself with the codebase

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- A PSD file for testing (optional but recommended)

### Environment Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/psd-character-extractor.git
   cd psd-character-extractor
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Verify installation**:
   ```bash
   pytest tests/
   python -m psd_extractor.cli --help
   ```

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Run tests and linting**:
   ```bash
   # Run tests
   pytest tests/

   # Format code
   black src/ tests/
   isort src/ tests/

   # Lint code
   flake8 src/ tests/

   # Type checking
   mypy src/
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create a pull request**

## Contributing Guidelines

### Bug Reports

When reporting bugs, please include:

- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment information** (OS, Python version, package version)
- **Sample PSD file** (if relevant and shareable)
- **Error messages** or stack traces

Use our bug report template:

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. With PSD file '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Windows 10, Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Package version: [e.g., 0.1.0]

**Additional Context**
Any other relevant information.
```

### Feature Requests

For feature requests, please provide:

- **Clear description** of the proposed feature
- **Use case** and motivation
- **Possible implementation** approach (if you have ideas)
- **Examples** of how it would be used

### Code Contributions

#### Areas for Contribution

**Core Functionality**:
- PSD parsing improvements
- Expression detection algorithms
- Image optimization enhancements
- Performance optimizations

**CLI Enhancements**:
- New command options
- Better error messages
- Progress indicators
- Output formatting

**Integration Support**:
- New VTuber software integrations
- Game engine plugins
- Additional output formats

**Documentation**:
- Tutorial improvements
- API documentation
- Example scripts
- Use case guides

#### Code Style

We follow these standards:

- **PEP 8** for Python code style
- **Black** for code formatting (line length: 88)
- **isort** for import sorting
- **Type hints** for better code documentation
- **Docstrings** for all public functions and classes

#### Commit Messages

We use [Conventional Commits](https://conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(cli): add --quality option to extract command
fix(extractor): handle missing expression group gracefully
docs(examples): add VTube Studio integration example
test(analyzer): add test for layer detection edge cases
```

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] Code is properly formatted
- [ ] Documentation is updated (if needed)
- [ ] CHANGELOG.md is updated (for notable changes)
- [ ] Pre-commit hooks pass

### PR Description

Please include:

- **Summary** of changes
- **Motivation** for the changes
- **Type of change** (bug fix, feature, docs, etc.)
- **Testing** performed
- **Screenshots** (if UI changes)
- **Breaking changes** (if any)

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** by maintainers
3. **Manual testing** (if needed)
4. **Documentation review** (if applicable)
5. **Merge** when approved

### After Merge

- Delete your feature branch
- Pull the latest changes to your local main branch
- Consider contributing to related issues

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/psd_extractor

# Run specific test file
pytest tests/test_extractor.py

# Run tests matching pattern
pytest -k "test_extract"
```

### Writing Tests

- **Unit tests** for individual functions/methods
- **Integration tests** for component interactions
- **CLI tests** for command-line interface
- **Mock external dependencies** (PSD files, etc.)

Test file structure:
```python
"""Tests for module_name."""

import unittest
from unittest.mock import Mock, patch

from src.psd_extractor.module_name import ClassToTest


class TestClassToTest(unittest.TestCase):
    """Test cases for ClassToTest."""

    def setUp(self):
        """Set up test fixtures."""
        self.instance = ClassToTest()

    def test_method_name(self):
        """Test specific functionality."""
        # Arrange
        input_data = "test"

        # Act
        result = self.instance.method(input_data)

        # Assert
        self.assertEqual(result, expected_result)
```

## Documentation

### Types of Documentation

**User Documentation**:
- Installation guides
- Usage tutorials
- CLI reference
- API documentation

**Developer Documentation**:
- Architecture overview
- Contributing guidelines
- Code documentation
- Development setup

### Documentation Standards

- **Clear and concise** language
- **Code examples** for all features
- **Screenshots** for visual elements
- **Keep updated** with code changes

### Building Documentation

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build documentation locally
cd docs
make html

# View documentation
open _build/html/index.html
```

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Pull Requests**: Code review and collaboration

### Getting Help

1. **Search existing issues** and discussions
2. **Check documentation** and examples
3. **Ask in discussions** for usage questions
4. **Create an issue** for bugs or feature requests

### Helping Others

- **Answer questions** in discussions
- **Review pull requests** (even non-code reviews help!)
- **Improve documentation**
- **Share your use cases** and examples

## Recognition

We value all contributions and recognize contributors in:

- **Release notes** for significant contributions
- **Contributors file** for all contributors
- **Social media** for notable features or improvements

## License

By contributing to PSD Character Extractor, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

## Questions?

If you have questions about contributing, please:

1. Check this guide and existing documentation
2. Search past discussions and issues
3. Start a new discussion in our [GitHub Discussions](https://github.com/psd-extractor/psd-character-extractor/discussions)

Thank you for contributing to PSD Character Extractor! 🎨✨