# 開発用リンクを作成する。
# リポジトリの script フォルダを、AviUtl2 の Script フォルダの下に
# ジャンクション（フォルダの別名）として見せる。
# これで、リポジトリ内のファイルを編集するだけで AviUtl2 に反映される。
# ジャンクションは管理者権限なしで作成できる。

param(
	[string]$LinkName = "renban-matome-dev"
)

$ErrorActionPreference = "Stop"

$sourceFolder = Join-Path $PSScriptRoot "..\script" | Resolve-Path
$aviutlScriptFolder = Join-Path $env:ProgramData "aviutl2\Script"
$linkPath = Join-Path $aviutlScriptFolder $LinkName

if (-not (Test-Path $aviutlScriptFolder)) {
	throw "AviUtl2 の Script フォルダが見つかりません: $aviutlScriptFolder"
}

if (Test-Path $linkPath) {
	$existing = Get-Item $linkPath -Force
	if ($existing.LinkType -eq "Junction") {
		Write-Host "既にリンクがあります: $linkPath -> $($existing.Target)"
		exit 0
	}
	throw "同名のフォルダが既にあります（リンクではありません）: $linkPath"
}

New-Item -ItemType Junction -Path $linkPath -Target $sourceFolder | Out-Null
Write-Host "リンクを作成しました: $linkPath -> $sourceFolder"
