# 📱 Logseq + RAG Integration

## Overview

asurdev Sentinel integrates with **Logseq** - a privacy-first knowledge management system - to provide persistent memory and context-aware analysis.

## Features

- 📓 **Vault Scanning** - Automatic discovery of pages and blocks
- 🔍 **Full-Text Search** - Fast search across all notes
- 🧠 **RAG Pipeline** - Retrieval-Augmented Generation for context
- 📝 **Auto-Indexing** - Keep knowledge base up-to-date
- 🔗 **Bidirectional Linking** - Follow page connections

## Architecture

```
Logseq Vault (markdown/Org-mode)
         │
         ▼
┌──────────────────┐
│  Vault Scanner   │ ─── Extracts pages/blocks
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  RAG Pipeline    │ ─── Embeddings + Vector Store
│  (FAISS/Chroma)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Logseq Agent    │ ─── Query + Context injection
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  LLM (Ollama)    │ ─── Final analysis
└──────────────────┘
```

## Quick Setup

```bash
# 1. Set vault path
export LOGSEQ_VAULT_PATH=~/logseq

# 2. Index vault
cd asurdevSentinel
python3 -c "
from logseq import get_logseq_agent
agent = get_logseq_agent()
result = agent.index_vault()
print('Indexed:', result)
"

# 3. Query knowledge base
python3 -c "
from logseq import get_logseq_agent
agent = get_logseq_agent()
results = agent.query('Elliott Wave patterns')
for r in results:
    print(r)
"
```

## Directory Structure

```
logseq/
├── __init__.py          # Package exports
├── vault_scanner.py     # Logseq vault parser
├── rag_pipeline.py      # Embeddings + Vector store
├── agent.py             # Logseq Agent
└── setup_logseq.sh      # Setup script
```

## Logseq Agent Methods

| Method | Description |
|--------|-------------|
| `index_vault(force)` | Index all pages and blocks |
| `query(text, limit)` | Semantic search |
| `add_page(title, content)` | Create new page |
| `get_page(title)` | Get page content |
| `get_backlinks(title)` | Find linked pages |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGSEQ_VAULT_PATH` | `~/logseq` | Path to Logseq vault |
| `LOGSEQ_INDEX_DIR` | `./data/logseq_index` | Vector index storage |

## Integration with Agents

```python
from agents import get_logseq_agent

# In any agent
logseq = get_logseq_agent()
context = logseq.query("relevant topic")
# Add context to LLM prompt
```

## Sync with Logseq

Logseq uses plain markdown/Org-mode files:

```markdown
- Logseq stores notes as `.md` or `.org` files
- Each block has unique ID
- Supports backlinks via `[[page]]` syntax
- Fully local - no cloud required
```

## Troubleshooting

**Vault not found:**
```bash
export LOGSEQ_VAULT_PATH=/path/to/your/logseq
```

**Empty results:**
```python
agent.index_vault(force=True)  # Force re-index
```

**Slow indexing:**
```bash
# For large vaults, index in background
nohup python3 -c "from logseq import get_logseq_agent; get_logseq_agent().index_vault()" &
```
