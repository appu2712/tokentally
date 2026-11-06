# Contributing to TokenTally

Thank you for your interest in contributing to **TokenTally**! We welcome community contributions of all kinds: bug fixes, documentation improvements, new model pricing additions, and feature enhancements.

## Development Setup

1. **Fork and Clone the Repository**:
   ```bash
   git clone https://github.com/appu2712/tokentally.git
   cd tokentally
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install Editable Package with Development Dependencies**:
   ```bash
   pip install -e .
   ```

4. **Run the Test Suite**:
   ```bash
   python -m unittest discover -s tests
   # or with pytest
   pytest tests/
   ```

## Adding a New Model

To update or add new models and pricing:
1. Open `src/tokentally/models.py`.
2. Add your entry to `MODEL_REGISTRY` with canonical per-million-token USD pricing.
3. Add any relevant shorthand aliases to `MODEL_ALIASES`.
4. Run tests to confirm validation.

## Submitting a Pull Request

1. Create a feature branch: `git checkout -b feature/my-new-feature`
2. Commit with clean, descriptive messages.
3. Ensure all tests pass.
4. Push to your fork and submit a PR against `main`.

Thank you for helping make LLM engineering transparent and cost-effective!
