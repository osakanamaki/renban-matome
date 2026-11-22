# 動作確認用のダミー連番画像を作成する。
# 公開リポジトリには利用者の素材を含めないため、テストにはこの画像だけを使う。
#
#   samples/number/number_000.png ～ number_010.png : 数字 0～10
#   samples/bar/bar_000.png       ～ bar_010.png    : 0～10 割合のバー

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$samplesFolder = Join-Path $PSScriptRoot "..\samples"
$lastNumber = 10

function New-NumberImage([int]$number, [string]$path) {
	$bitmap = New-Object System.Drawing.Bitmap 160, 120
	$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
	$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
	$graphics.Clear([System.Drawing.Color]::Transparent)

	$font = New-Object System.Drawing.Font "Arial", 64, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
	$format = New-Object System.Drawing.StringFormat
	$format.Alignment = [System.Drawing.StringAlignment]::Center
	$format.LineAlignment = [System.Drawing.StringAlignment]::Center
	$area = New-Object System.Drawing.RectangleF 0, 0, 160, 120
	$graphics.DrawString([string]$number, $font, [System.Drawing.Brushes]::White, $area, $format)

	$bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
	$font.Dispose(); $graphics.Dispose(); $bitmap.Dispose()
}

function New-BarImage([int]$number, [string]$path) {
	$width = 400
	$height = 40
	$bitmap = New-Object System.Drawing.Bitmap $width, $height
	$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
	$graphics.Clear([System.Drawing.Color]::Transparent)

	$filledWidth = [int]($width * $number / $lastNumber)
	if ($filledWidth -gt 0) {
		$graphics.FillRectangle([System.Drawing.Brushes]::LimeGreen, 0, 0, $filledWidth, $height)
	}
	$graphics.DrawRectangle([System.Drawing.Pens]::White, 0, 0, $width - 1, $height - 1)

	$bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
	$graphics.Dispose(); $bitmap.Dispose()
}

foreach ($kind in "number", "bar") {
	$folder = Join-Path $samplesFolder $kind
	New-Item -ItemType Directory -Force -Path $folder | Out-Null
	for ($number = 0; $number -le $lastNumber; $number++) {
		$fileName = "{0}_{1:D3}.png" -f $kind, $number
		$path = Join-Path $folder $fileName
		if ($kind -eq "number") { New-NumberImage $number $path } else { New-BarImage $number $path }
	}
	Write-Host "作成しました: $folder"
}
