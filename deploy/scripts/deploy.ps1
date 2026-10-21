# 一键把命令同步到本机 Claude 目录，并写入知识库路径
$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
$CmdDir = Join-Path $ClaudeDir "commands"
$ConfigTarget = Join-Path $ClaudeDir "distill.config.md"

$pythonCmd = "python"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        $pythonCmd = "python3"
    } else {
        Write-Warning "未找到 python/python3，请安装 Python 3.9+ 并加入 PATH。"
    }
}

New-Item -ItemType Directory -Force -Path $CmdDir | Out-Null

Get-ChildItem (Join-Path $RepoRoot "deploy\.claude\commands\*.md") | ForEach-Object {
    Copy-Item $_.FullName -Destination $CmdDir -Force
}

if (Test-Path $ConfigTarget) {
    Copy-Item $ConfigTarget "$ConfigTarget.bak" -Force
}

$repoPath = $RepoRoot -replace "\\", "/"
$configLines = @(
    "# 蒸馏配置",
    "",
    "## 知识库本地路径",
    "知识库路径：$repoPath",
    "",
    "## Python 命令",
    "Python命令：$pythonCmd",
    "",
    "## 说明",
    "- 主题清单由仓库内的 topics/INDEX.md 自动维护。",
    "- 新主题由 /distill 自动创建主题页。",
    "- 重新部署：运行 deploy/scripts/deploy.ps1。"
)
$config = ($configLines -join "`r`n") + "`r`n"
[System.IO.File]::WriteAllText($ConfigTarget, $config, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "已同步命令到: $CmdDir"
Write-Host "知识库路径: $repoPath"
Write-Host "Python 命令: $pythonCmd"
Write-Host "配置: $ConfigTarget"
Write-Host "请重启 / 重载 Claude Code，让 /distill、/consolidate、/recall 生效。"
