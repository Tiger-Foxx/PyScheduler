# Contributing to PyScheduler

Thank you for your interest in contributing to PyScheduler! 🚀

## Quick Start

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a virtual environment
4. **Install** development dependencies
5. **Make** your changes
6. **Test** your changes
7. **Submit** a pull request

```bash
git clone https://github.com/YOUR_USERNAME/PyScheduler.git
cd PyScheduler
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows
pip install -e .[dev]
```

## Development Setup

### Install Development Dependencies
```bash
pip install -e .[dev]  # Installs: pytest, black, flake8, mypy
```

### Run Tests
```bash
pytest                 # Run all tests
pytest -v             # Verbose output
pytest --cov          # With coverage
```

### Code Formatting
```bash
black .               # Format code
flake8 .             # Check style
mypy pyscheduler/    # Type checking
```

## Contributing Guidelines

### Code Style
- **Black** for code formatting (line length: 100)
- **flake8** for style checking
- **Type hints** for all public functions
- **Docstrings** for all public classes and methods

### Testing
- **Write tests** for all new features
- **Maintain** >90% test coverage
- **Test** on multiple Python versions (3.7+)
- **Include** both unit and integration tests

### Documentation
- **Update** relevant documentation
- **Add** examples for new features
- **Follow** existing documentation style
- **Include** docstrings with examples

## Types of Contributions

### 🐛 Bug Reports
- Use the **bug report template**
- Include **minimal reproduction code**
- Provide **system information**
- Describe **expected vs actual behavior**

### ✨ Feature Requests
- Use the **feature request template**
- Explain the **use case**
- Provide **implementation ideas** if possible
- Consider **backward compatibility**

### 📝 Documentation
- Fix **typos** and **unclear explanations**
- Add **missing examples**
- Improve **API documentation**
- Translate to **other languages**

### 🔧 Code Contributions
- Follow the **development setup**
- Write **comprehensive tests**
- Update **documentation**
- Follow **code style guidelines**

## Pull Request Process

1. **Create** feature branch: `git checkout -b feature/my-feature`
2. **Make** your changes with tests
3. **Run** full test suite: `pytest`
4. **Update** documentation if needed
5. **Commit** with clear messages
6. **Push** and create pull request
7. **Address** review feedback

### Commit Messages
Use clear, descriptive commit messages:
```
feat: add async task timeout handling
fix: resolve CRON timezone calculation bug
docs: update installation guide with conda
test: add integration tests for YAML config
```

## Development Guidelines

### Project Structure
```
PyScheduler/
├── pyscheduler/           # Main package
│   ├── core/             # Core functionality
│   ├── config/           # Configuration classes
│   ├── exceptions/       # Custom exceptions
│   └── examples/         # Usage examples
├── tests/                # Test suite
├── docs/                 # Documentation
├── examples/             # Standalone examples
└── scripts/              # Development scripts
```

### Adding New Features

1. **Design** the API carefully
2. **Write** tests first (TDD approach)
3. **Implement** the feature
4. **Add** documentation and examples
5. **Update** changelog

### Testing Strategy

- **Unit tests**: Test individual components
- **Integration tests**: Test component interactions
- **Example tests**: Ensure examples work
- **Performance tests**: For critical paths

## Release Process

1. **Update** version in `pyscheduler/__init__.py`
2. **Update** `CHANGELOG.md`
3. **Run** full test suite
4. **Create** release PR
5. **Tag** release after merge
6. **Publish** to PyPI

## Getting Help

- 💬 **Discussions**: https://github.com/Tiger-Foxx/PyScheduler/discussions
- 📧 **Email**: donfackarthur750@gmail.com
- 🐛 **Issues**: https://github.com/Tiger-Foxx/PyScheduler/issues

## Code of Conduct

Be respectful, inclusive, and constructive. We want PyScheduler to be welcoming to contributors of all backgrounds and experience levels.

## Recognition

Contributors will be:
- **Listed** in CONTRIBUTORS.md
- **Mentioned** in release notes
- **Thanked** publicly for significant contributions

Thank you for making PyScheduler better! 🙏
