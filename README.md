# Neovim Plugin RAG

Automated system for discovering, categorizing, and updating Neovim plugins using RAG (Retrieval-Augmented Generation) technology.

## What it does

This system automatically monitors new Neovim plugins and creates pull requests to [yutkat/my-neovim-pluginlist](https://github.com/yutkat/my-neovim-pluginlist) with proper categorization using AI.

## CI Workflows

### 1. Daily Plugin Discovery (`create-pr.yml`)

Runs daily at 0:30 UTC to discover new plugins:

- Fetches latest plugins from RSS feeds
- Uses RAG to find similar existing plugins in the vector database
- Predicts categories using OpenAI GPT-4
- Creates pull request to `yutkat/my-neovim-pluginlist` with new plugins
- Triggers Codex verification workflow

### 2. Vector Database Update (`update-vector-db.yml`)

Runs daily at 10:00 UTC to maintain the plugin database:

- Monitors recent commits in `yutkat/my-neovim-pluginlist`
- Extracts newly added plugin URLs
- Fetches README content from GitHub repositories
- Creates embeddings using OpenAI API
- Updates ChromaDB vector database

### 3. Codex Verification (`verify-categories.yml`)

Automatically verifies plugin categorizations:

- Uses OpenAI Codex (GPT-5) to verify AI-generated categorizations
- Reviews plugin categories for accuracy
- Updates markdown files with corrections
- Creates refined pull request with improved categorization

## Technology Stack

- **Vector Database**: ChromaDB for storing plugin embeddings
- **AI Models**: OpenAI text-embedding-3-small for similarity search, GPT-4 for categorization
- **Verification**: OpenAI Codex (GPT-5) for category validation
- **Data Source**: RSS feeds and GitHub API for plugin discovery
