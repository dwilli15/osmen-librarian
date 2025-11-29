# Contributing to OsMEN Librarian

Thank you for your interest in contributing to OsMEN Librarian! This project is part of the [OsMEN ecosystem](https://github.com/dwilli15/OsMEN).

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/dwilli15/osmen-librarian/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, GPU)

### Suggesting Features

1. Check existing issues for similar suggestions
2. Create a new issue with the `enhancement` label
3. Describe the feature and its use case

### Pull Requests

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/osmen-librarian.git
   ```
3. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make changes** and add tests
5. **Run tests**:
   ```bash
   pytest -v
   ```
6. **Format code**:
   ```bash
   black src/
   ruff check src/ --fix
   ```
7. **Commit** with clear messages:
   ```bash
   git commit -m "feat: Add new retrieval mode"
   ```
8. **Push** and create a Pull Request

### Commit Message Format

We use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style (formatting, etc.)
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `test:` Adding missing tests
- `chore:` Maintenance tasks

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- (Optional) NVIDIA GPU with CUDA

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/osmen-librarian.git
cd osmen-librarian

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v
```

## Code Style

- **Black** for formatting (line length: 88)
- **Ruff** for linting
- **MyPy** for type checking
- Type hints required for all public functions

## Testing

- All new features need tests
- Maintain test coverage
- Tests should be in `src/tests/`
- Use `pytest` conventions

## Questions?

- Open an issue for questions
- Check the [OsMEN Documentation](https://github.com/dwilli15/OsMEN)

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
