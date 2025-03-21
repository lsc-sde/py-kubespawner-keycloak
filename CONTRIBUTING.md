# Contributing to KubeSpawner Keycloak

Thank you for your interest in contributing to KubeSpawner Keycloak! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## Getting Started

### Prerequisites

- Python 3.8 or later
- pip
- Docker (for running tests with Kubernetes)
- Access to a Keycloak instance (for testing)

### Setting Up the Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```
   git clone https://github.com/YOUR-USERNAME/kubespawner-keycloak.git
   cd kubespawner-keycloak
   ```
3. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```
   pip install -e ".[dev]"
   ```

## Development Workflow

1. Create a new branch for your feature or bugfix:
   ```
   git checkout -b feature/your-feature-name
   ```
   or
   ```
   git checkout -b fix/issue-number
   ```

2. Make your changes, following our coding standards

3. Add tests for your changes

4. Run the tests to ensure they pass:
   ```
   pytest
   ```

5. Update documentation if necessary

6. Commit your changes:
   ```
   git commit -m "Description of your changes"
   ```

7. Push to your fork:
   ```
   git push origin feature/your-feature-name
   ```

8. Submit a pull request

## Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
2. Update the version number in setup.py following semantic versioning
3. The PR should work for Python 3.8 and later
4. Include a clear description of the changes in your PR description
5. Link any related issues in the PR description

## Coding Standards

- Follow PEP 8 style guidelines
- Write docstrings for all functions, classes, and methods
- Use type hints where appropriate
- Keep code modular and maintainable
- Add comments for complex logic

## Testing

- Write unit tests for all new functionality
- Ensure all tests pass before submitting a PR
- Integration tests should be included for features that interact with external systems

## Documentation

- Update documentation for all user-facing changes
- Document internal APIs and architecture decisions
- Use clear, concise language
- Include examples where helpful

## Issue Reporting

When reporting issues, please include:

- A clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Relevant logs or screenshots
- Version information (Python, Kubernetes, JupyterHub, KubeSpawner, etc.)

## Feature Requests

For feature requests, please include:

- A clear description of the feature
- Rationale for the feature
- Potential implementation approaches if you have ideas

## License

By contributing to KubeSpawner Keycloak, you agree that your contributions will be licensed under the project's MIT License.

Thank you for contributing to KubeSpawner Keycloak!
