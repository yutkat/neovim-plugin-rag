# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Setup
- Python 3.13+ required
- Install dependencies: `pip install -e .` or `pip install -r requirements.txt`
- Run scripts using: `python scripts/script_name.py [arguments]`

## Scripts
- Neovim plugin search: `python scripts/search.py <GitHub_URL>`
- Embed plugins: `python scripts/embedding.py`
- Predict categories: `python scripts/predict_category.py <GitHub_URL>`
- Convert to CSV: `python scripts/convert_to_csv.py`

## Code Style Guidelines
- Follow PEP 8 conventions
- Use descriptive variable names (snake_case)
- Imports: stdlib first, then third-party, then local modules
- Include docstrings for functions with descriptions and param types
- Error handling: Use try/except with specific error types and informative messages
- Type hints encouraged for function parameters and returns

## Environment Variables
- OPENAI_API_KEY must be set for embedding and categorization
- GITHUB_TOKEN required for fetching repo information