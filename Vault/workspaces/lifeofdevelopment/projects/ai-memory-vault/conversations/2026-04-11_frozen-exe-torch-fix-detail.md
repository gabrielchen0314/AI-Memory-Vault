---
type: conversation-detail
date: 2026-04-11
session: frozen-exe-torch-fix
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
tags: [conversation, detail]
---

# 2026-04-11 frozen-exe-torch-fix — 詳細對話紀錄

## 對話概要
- **主題**：Frozen exe torch 崩潰修復 + 全面驗證

## 關鍵問答紀錄

### Q1: 為什麼 frozen exe 中搜尋/同步功能會崩潰？
- **AI 分析**：import torch 在 PyInstaller 凍結環境中觸發 C runtime 崩潰，兩條匯入鏈分別來自嵌入模型和 EnsembleRetriever
- **決策**：torch stub + ONNX 直接推理雙層解法
- **替代方案**：嘗試過 backend='onnx' 但失敗（sentence_transformers 仍會 import torch）

## 修改的檔案清單

| 檔案 | 操作 | 摘要 |
|------|------|------|
| `AI_Engine/main.py` | 修改 | 新增 torch stub (~70 行)，修復 del _FakeDtype NameError |
| `AI_Engine/core/embeddings.py` | 修改 | 新增 _OnnxEmbeddings 類別（onnxruntime + tokenizers） |
| `AI_Engine/core/indexer.py` | 修改 | 移除假 langchain_text_splitters 套件 hack，改用正常 import |
| `AI_Engine/services/instinct.py` | 修改 | 修正 search() 方法的 dict unpacking（非 tuple） |
| `AI_Engine/test_exe_mcp.py` | 修改 | 擴充至 40 工具全覆蓋測試（45 步驟） |

## 遇到的問題與解決

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| _FakeDtype NameError | del _FakeDtype 刪除了 __getattr__ 運行時需要的類別 | 不 del _FakeDtype 和 _FakeTensor |
| search_vault TextSplitter 匯入失敗 | 舊的假 langchain_text_splitters 套件 hack 與 torch stub 衝突 | 移除 hack，改用正常 import |
| search_instincts too many values to unpack | VaultService.search() 回傳 dict，InstinctService 假設是 (doc, score) tuple | 改用 dict 存取 _Hit.get('source') |

## 學到的知識

- 不要 del 被 __getattr__ 閉包引用的 stub 類別
- 全域 torch stub 就位後，局部 import hack 變多餘且可能衝突
- 服務間 API 回傳型別要明確驗證
- ONNX vs torch 嵌入精度差異 < 5e-7，float32 可接受

## 決策記錄

| 決策 | 選項 | 最終選擇 | 理由 |
|------|------|---------|------|
| 採用 torch stub + ONNX 雙層方案 | A: backend='onnx' / B: torch stub + _OnnxEmbeddings | B | A 失敗（sentence_transformers 模組層級仍 import torch） |
