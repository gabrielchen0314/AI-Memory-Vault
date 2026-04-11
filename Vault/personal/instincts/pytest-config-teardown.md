---
id: "pytest-config-teardown"
trigger: 編寫涉及讀/寫設定檔（config.json）或正式資料的 pytest 測試時
confidence: 0.85
domain: python
source: "session-observation"
created: "2026-04-11"
sequence: 16
---

# pytest 測試必須用 tmp_path/monkeypatch 隔離 config.json

## 動作
必須使用 tmp_path / monkeypatch 隔離測試資料，絕不直接讀寫正式 config.json

## 證據
2026-04-11：pytest 執行後 config.json 被污染為 test_user/TEST_ORG 路徑，必須從 .bak 還原
