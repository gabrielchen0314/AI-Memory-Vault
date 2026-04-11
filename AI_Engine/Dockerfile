# ── AI Memory Vault — Docker 映像 ──────────────────────────
# 支援 MCP SSE 模式（HTTP 長連線）和排程器模式。
#
# 建構：
#   docker build -t ai-memory-vault -f AI_Engine/Dockerfile .
#
# 用法：
#   docker compose up          → 啟動 MCP SSE + Scheduler
#   docker compose up mcp-sse  → 僅啟動 MCP SSE 伺服器
# ────────────────────────────────────────────────────────────

FROM python:3.12-slim AS base

LABEL maintainer="gabrielchen"
LABEL description="AI Memory Vault — MCP SSE Server + Scheduler"

# 避免 Python 寫入 .pyc 和啟用即時輸出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── 安裝系統依賴 ──
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# ── 安裝 Python 依賴（利用 Docker 層快取）──
COPY AI_Engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 複製應用程式碼 ──
COPY AI_Engine/ .

# ── 資料目錄（volume 掛載點）──
RUN mkdir -p /data/backups /data/chroma_db
ENV VAULT_DATA_DIR=/data

# ── 預設 Vault 路徑（volume 掛載）──
VOLUME ["/vault", "/data"]

# ── 健康檢查（SSE 模式）──
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/sse')" || exit 1

# ── 預設：MCP SSE 模式 ──
EXPOSE 8765
CMD ["python", "main.py", "--mode", "api"]
