---
id: "verify-api-return-types-across-services"
trigger: 一個服務呼叫另一個服務的 API 並對回傳值做解包或索引存取時
confidence: 0.7
domain: python
source: "session-observation"
created: "2026-04-11"
sequence: 37
---

# 跨服務呼叫前驗證 API 回傳型別

## 動作
呼叫其他服務的 API 時，先確認回傳型別（dict / tuple / Document 等），不要假設。寫 `for item in results:` 搭配 dict 存取，或明確解包前加 assert 驗證型別。

## 證據
2026-04-11：InstinctService.search() 假設 VaultService.search() 回傳 (Doc, Score) tuple，實際回傳 dict 列表，導致 too many values to unpack。
