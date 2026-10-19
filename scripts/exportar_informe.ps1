# Actualiza el índice y los campos del informe en Word, exporta a PDF y (opcional) vuelca cada página como EMF.
# Requiere Microsoft Word instalado (Windows).
#
#   powershell -File scripts\exportar_informe.ps1
#   powershell -File scripts\exportar_informe.ps1 -PaginasDir C:\temp\paginas   # además guarda p001.emf, p002.emf...
param(
    [string]$Docx = (Join-Path $PSScriptRoot "..\documento\Informe_Final_Proyecto_ENOE.docx"),
    [string]$Pdf = (Join-Path $PSScriptRoot "..\documento\Informe_Final_Proyecto_ENOE.pdf"),
    [string]$PaginasDir = ""
)
$Docx = (Resolve-Path $Docx).Path
$Pdf = [IO.Path]::GetFullPath($Pdf)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Docx)
    $doc.Repaginate()
    foreach ($t in $doc.TablesOfContents) { $t.Update() }
    $null = $doc.Fields.Update()
    $doc.Repaginate()
    foreach ($t in $doc.TablesOfContents) { $t.UpdatePageNumbers() }
    $doc.Save()
    $doc.ExportAsFixedFormat($Pdf, 17)     # 17 = wdExportFormatPDF
    $paginas = $doc.ComputeStatistics(2)   # 2 = wdStatisticPages
    Write-Output "Paginas: $paginas"
    Write-Output "PDF: $Pdf"
    if ($PaginasDir) {
        New-Item -ItemType Directory -Force $PaginasDir | Out-Null
        $win = $word.ActiveWindow
        $win.View.Type = 3                 # vista de impresión
        $pane = $win.ActivePane
        for ($i = 1; $i -le $paginas; $i++) {
            $bytes = $pane.Pages.Item($i).EnhMetaFileBits
            [IO.File]::WriteAllBytes((Join-Path $PaginasDir ("p{0:000}.emf" -f $i)), $bytes)
        }
        Write-Output "EMF por pagina en: $PaginasDir"
    }
    $doc.Close(0)
}
finally {
    $word.Quit()
}
