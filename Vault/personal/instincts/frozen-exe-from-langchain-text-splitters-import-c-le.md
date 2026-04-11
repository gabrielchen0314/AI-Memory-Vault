---
id: "frozen-exe-from-langchain-text-splitters-import-c-le"
trigger: "frozen exe 在 from langchain_text_splitters import ... 時 C-level crash (0xC0000409)"
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-11"
sequence: 21
---

# 問題：frozen exe 在 from langchain_text_splitters import 

## 動作
importlib 預註冊空 package 繞過 __init__.py

## 證據
__init__.py 載入所有子模組（含 spacy/nltk/konlpy），某些 C extension 在 frozen 環境觸發 stack buffer overrun
