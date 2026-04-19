$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$folder = "C:\Users\12902\Nutstore\1\我的坚果云\工作\周报"
$pptxPath = Get-ChildItem $folder -Filter "丁二烯顺丁橡胶周报*.pptx" | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
Write-Host "Target: $pptxPath" -ForegroundColor Cyan

Write-Host "Opening PowerPoint..." -ForegroundColor Cyan
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue
$ppt.DisplayAlerts = [Microsoft.Office.Core.MsoTriState]::msoFalse

function Refresh-ChartsInShape($shape) {
    $count = 0
    if ($shape.HasChart) {
        try {
            $shape.Chart.ChartData.Activate()
            $count = 1
        } catch {
        }
    }
    if ($shape.Type -eq 6) {
        foreach ($item in $shape.GroupItems) {
            $count += Refresh-ChartsInShape $item
        }
    }
    return $count
}

try {
    Write-Host "Opening: $pptxPath" -ForegroundColor Cyan
    $pres = $ppt.Presentations.Open($pptxPath, $false, $false, $false)

    $refreshed = 0
    $total = $pres.Slides.Count

    for ($i = 1; $i -le $total; $i++) {
        Write-Host "  Slide $i / $total ..." -ForegroundColor Yellow -NoNewline
        $slide = $pres.Slides($i)
        foreach ($shape in $slide.Shapes) {
            $refreshed += Refresh-ChartsInShape $shape
        }
        Write-Host " OK (total: $refreshed)" -ForegroundColor Green
    }

    Write-Host "`nSaving..." -ForegroundColor Cyan
    $pres.Save()
    $pres.Close()
    Write-Host "Done! Refreshed $refreshed charts." -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
} finally {
    Write-Host "Closing PowerPoint..." -ForegroundColor Cyan
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
}

Write-Host "`nPress Enter to exit..."
Read-Host
