[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$folder = $env:WEEKLY_REPORT_FOLDER ?? "C:\工作\周报"
$pptxPath = Get-ChildItem $folder -Filter "丁二烯顺丁橡胶周报*.pptx" | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
$mappingPath = Join-Path $folder "table_mapping.xlsx"
$excelBase = $env:EXCEL_DATA_FOLDER ?? "C:\工作"
$excelDirs = @("$excelBase\丁二烯合成\数据", "$excelBase\石脑油\数据")
$fileAlias = @{ "周度.xlsx" = "周度数据库.xlsx" }

function Find-ExcelFile($filename) {
    if ($fileAlias.ContainsKey($filename)) { $filename = $fileAlias[$filename] }
    foreach ($dir in $excelDirs) {
        $path = Join-Path $dir $filename
        if (Test-Path $path) { return $path }
    }
    return $null
}

function Parse-SingleRange($rangeStr) {
    if ($rangeStr -match '^([A-Z]+)(\d+):([A-Z]+)(\d+)$') {
        $cs = $Matches[1]; $ce = $Matches[3]
        $colS = 0; $colE = 0
        for ($i = 0; $i -lt $cs.Length; $i++) { $colS = $colS * 26 + ([int][char]$cs[$i] - 64) }
        for ($i = 0; $i -lt $ce.Length; $i++) { $colE = $colE * 26 + ([int][char]$ce[$i] - 64) }
        return @{ RS = [int]$Matches[2]; CS = $colS; RE = [int]$Matches[4]; CE = $colE }
    }
    return $null
}

# Read mapping
Write-Host "Reading mapping..." -ForegroundColor Cyan
$xlMap = New-Object -ComObject Excel.Application
$xlMap.Visible = $false; $xlMap.DisplayAlerts = $false
$wbMap = $xlMap.Workbooks.Open($mappingPath)
$wsMap = $wbMap.Sheets(1)
$mappings = @()
$row = 2
while ($wsMap.Cells($row, 1).Text) {
    $mappings += @{
        Slide = [int]$wsMap.Cells($row, 1).Text
        TableIdx = [int]$wsMap.Cells($row, 2).Text
        ExcelFile = $wsMap.Cells($row, 3).Text
        Sheet = $wsMap.Cells($row, 4).Text
        DataRange = $wsMap.Cells($row, 5).Text
        PptSR = [int]$wsMap.Cells($row, 6).Text
        PptSC = [int]$wsMap.Cells($row, 7).Text
        DateSheet = $wsMap.Cells($row, 8).Text
        DateRange = $wsMap.Cells($row, 9).Text
    }
    $row++
}
$wbMap.Close($false); $xlMap.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($xlMap) | Out-Null
Write-Host "Found $($mappings.Count) mappings" -ForegroundColor Green

# Connect to running Excel, or start new
Write-Host "Connecting to Excel..." -ForegroundColor Cyan
try {
    $xl = [System.Runtime.InteropServices.Marshal]::GetActiveObject("Excel.Application")
    Write-Host "  Connected to running Excel." -ForegroundColor Green
} catch {
    $xl = New-Object -ComObject Excel.Application
    $xl.Visible = $false; $xl.DisplayAlerts = $false
    Write-Host "  Started new Excel instance." -ForegroundColor Yellow
}

$excelCache = @{}

function Get-WB($filename) {
    if ($fileAlias.ContainsKey($filename)) { $filename = $fileAlias[$filename] }
    if (-not $excelCache.ContainsKey($filename)) {
        foreach ($wb in $xl.Workbooks) {
            $name = [System.IO.Path]::GetFileName($wb.FullName)
            if ($name -eq $filename) {
                Write-Host "  Found open: $filename" -ForegroundColor Gray
                $excelCache[$filename] = $wb
                return $wb
            }
        }
        $path = Find-ExcelFile $filename
        if ($path) {
            Write-Host "  Opening $filename ..." -ForegroundColor Gray
            $excelCache[$filename] = $xl.Workbooks.Open($path, $false, $true)
            Write-Host "  OK" -ForegroundColor Gray
        } else {
            Write-Host "  NOT FOUND: $filename" -ForegroundColor Red
        }
    }
    return $excelCache[$filename]
}

function Read-Range($wb, $sheetName, $rangeStr) {
    $ws = $wb.Sheets($sheetName)
    $data = @()
    $parts = $rangeStr -split ","
    foreach ($part in $parts) {
        $part = $part.Trim()
        $r = Parse-SingleRange $part
        if (-not $r) { continue }
        for ($row = $r.RS; $row -le $r.RE; $row++) {
            $rowData = @()
            for ($col = $r.CS; $col -le $r.CE; $col++) { $rowData += $ws.Cells($row, $col).Text }
            $data += ,$rowData
        }
    }
    return ,$data
}

# Open PPT
Write-Host "Opening PowerPoint..." -ForegroundColor Cyan
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue

try {
    $pres = $ppt.Presentations.Open($pptxPath, $false, $false, $false)
    foreach ($mp in $mappings) {
        $wb = Get-WB $mp.ExcelFile
        if (-not $wb) { Write-Host "  Slide $($mp.Slide): $($mp.ExcelFile) not found" -ForegroundColor Red; continue }
        $slide = $pres.Slides($mp.Slide)
        $tc = 0; $tt = $null
        foreach ($shape in $slide.Shapes) {
            if ($shape.HasTable) { $tc++; if ($tc -eq $mp.TableIdx) { $tt = $shape.Table; break } }
            if ($shape.Type -eq 6) {
                foreach ($item in $shape.GroupItems) {
                    if ($item.HasTable) { $tc++; if ($tc -eq $mp.TableIdx) { $tt = $item.Table; break } }
                }
                if ($tt) { break }
            }
        }
        if (-not $tt) { Write-Host "  Slide $($mp.Slide): table $($mp.TableIdx) not found" -ForegroundColor Red; continue }

        if ($mp.DateSheet -and $mp.DateRange) {
            try {
                $dd = Read-Range $wb $mp.DateSheet $mp.DateRange
                for ($i = 0; $i -lt $dd.Count; $i++) {
                    $r = $mp.PptSR + $i + 2
                    if ($r -le $tt.Rows.Count) { $tt.Cell($r, 1).Shape.TextFrame.TextRange.Text = "$($dd[$i][0])" }
                }
            } catch {
                Write-Host "    (date sheet not found, skipped)" -ForegroundColor Yellow
            }
        }
        $md = Read-Range $wb $mp.Sheet $mp.DataRange
        for ($i = 0; $i -lt $md.Count; $i++) {
            for ($j = 0; $j -lt $md[$i].Count; $j++) {
                $r = $mp.PptSR + $i + 2
                $c = $mp.PptSC + $j + 1
                if ($r -le $tt.Rows.Count -and $c -le $tt.Columns.Count -and $md[$i][$j]) {
                    $tt.Cell($r, $c).Shape.TextFrame.TextRange.Text = $md[$i][$j]
                }
            }
        }
        $rn = if ($md.Count -gt 0) { $md.Count } else { 0 }
        $cn = if ($md.Count -gt 0 -and $md[0].Count -gt 0) { $md[0].Count } else { 0 }
        Write-Host "  Slide $($mp.Slide): $rn x $cn" -ForegroundColor Green
    }
    Write-Host "`nSaving..." -ForegroundColor Cyan
    $pres.Save(); $pres.Close()
    Write-Host "Done!" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
} finally {
    $ppt.Quit(); [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
}

Write-Host "`nPress Enter to exit..."
Read-Host
