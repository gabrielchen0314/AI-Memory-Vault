---
id: "monkeypatch-instinctservice-lazy-import"
trigger: monkeypatch 目標錯誤：InstinctService lazy import
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-10"
sequence: 1
---

# 問題：monkeypatch 目標錯誤：InstinctService lazy import

## 動作
改 monkeypatch 目標為 services.instinct.InstinctService

## 證據
_auto_learn_instincts 內部用 from services.instinct import InstinctService，monkeypatch services.scheduler.InstinctService 無效
