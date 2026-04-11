---
id: "langchain-text-splitters-v1-1-1-init-py-import-all"
trigger: "langchain_text_splitters v1.1.1 的 __init__.py 會 import ALL 子模組（包括 spacy/nltk/konlpy），在 PyInstaller frozen 環境可能觸發 C-level crash"
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-11"
sequence: 23
---

# 學習：langchain_text_splitters v1.1.1 的 __init__.py 會 im

## 動作
langchain_text_splitters v1.1.1 的 __init__.py 會 import ALL 子模組（包括 spacy/nltk/konlpy），在 PyInstaller frozen 環境可能觸發 C-level crash
