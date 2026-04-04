# stop.ps1 — 停止 FastAPI (port 8000) 與 MCP Server (port 8001)
# 用法：.\stop.ps1

$_Ports = @(8000, 8001)

foreach( $_Port in $_Ports )
{
    $_Pid = (netstat -ano | Select-String ":$_Port\s" | ForEach-Object {
        ($_ -split "\s+")[-1]
    } | Select-Object -First 1)

    if( $_Pid -and $_Pid -match "^\d+$" )
    {
        Stop-Process -Id $_Pid -Force -ErrorAction SilentlyContinue
        Write-Host "✅ 已停止 port $_Port (PID $_Pid)"
    }
    else
    {
        Write-Host "⚪ port $_Port 沒有在跑"
    }
}
