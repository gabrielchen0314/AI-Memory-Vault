# AI Memory Vault — Workspace Instructions

This repository is an **AI Memory Vault**: a personal knowledge base powered by a local RAG engine.
The vault root contains Markdown notes organized into `work/`, `life/`, `knowledge/`, `_system/`, and `templates/`.

## MCP Tools Available

When the MCP server is running, you have access to these tools:

| Tool | When to Use |
|------|-------------|
| `search_vault` | Find notes by topic, keyword, or semantic query |
| `read_note` | Read the full content of a specific note |
| `write_note` | Create or overwrite a note (auto-indexes to vector DB) |
| `sync_vault` | Rebuild the vector index after bulk file changes |

## Path Convention

All `file_path` arguments are **relative to the vault root** (this workspace folder).

```
✅  work/LIFEOFDEVELOPMENT/projects/MyProject/notes.md
✅  knowledge/python-tips.md
✅  life/journal/2026-03-30.md
❌  D:/AI-Memory-Vault/knowledge/python-tips.md   (absolute path)
```

## Vault Structure

```
_system/          → AI navigation layer (core-memory, AGENTS, handoff)
_AI_Engine/       → Python RAG engine (FastAPI + MCP + CLI)
work/             → Work domain (organized by company)
  _shared/        → Cross-company snippets, skills, tech notes
  CHINESEGAMER/   → Company A workspace
  LIFEOFDEVELOPMENT/ → Personal projects
life/             → Personal domain (journal, goals, learning, ideas)
knowledge/        → Permanent knowledge cards (distilled concepts)
templates/        → Vault structure templates (projects + sections)
```

## Write Path Rules

Before creating a new note, match the target path to the correct section:

| Content Type | Path |
|-------------|------|
| Company project notes | `work/{COMPANY}/projects/{ProjectName}/` |
| Meeting records | `work/{COMPANY}/meetings/` |
| Coding rules | `work/{COMPANY}/rules/` |
| Shared tech notes | `work/_shared/` |
| Permanent knowledge | `knowledge/` |
| Journal / weekly review | `life/journal/` |
| Learning notes | `life/learning/` |

## Setup (First Time)

1. Copy `.env.example` → `.env` and fill in your API keys
2. `cd _AI_Engine && pip install -r requirements.txt`
3. Run `python main.py --mode mcp` — VS Code will connect automatically via `.vscode/mcp.json`
