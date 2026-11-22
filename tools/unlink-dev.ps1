# 開発用リンクを削除する。
# リンク（ジャンクション）だけを削除し、リポジトリ内のファイルは消さない。

param(
	[string]$LinkName = "renban-matome-dev"
)

$ErrorActionPreference = "Stop"

$linkPath = Join-Path $env:ProgramData "aviutl2\Script\$LinkName"

if (-not (Test-Path $linkPath)) {
	Write-Host "リンクはありません: $linkPath"
	exit 0
}

$existing = Get-Item $linkPath -Force
if ($existing.LinkType -ne "Junction") {
	throw "リンクではないため削除しません: $linkPath"
}

# Directory.Delete を非再帰で呼ぶと、ジャンクション自体だけが消える。
[System.IO.Directory]::Delete($linkPath, $false)
Write-Host "リンクを削除しました: $linkPath"
