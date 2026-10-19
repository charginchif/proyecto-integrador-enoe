# Exporta cada diapositiva de una presentación como PNG con PowerPoint (revisión visual) y, opcionalmente, un PDF.
# Requiere Microsoft PowerPoint instalado (Windows).
#
#   powershell -File scripts\exportar_presentacion.ps1 -Pptx presentacion\Presentacion_Completa_Proyecto_ENOE.pptx -Salida C:\temp\diapositivas
#   powershell -File scripts\exportar_presentacion.ps1 -Pptx presentacion\Presentacion_Completa_Proyecto_ENOE.pptx -Pdf presentacion\Presentacion_Completa_Proyecto_ENOE.pdf
param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [string]$Salida = "",
    [string]$Pdf = "",
    [int]$Ancho = 1600,
    [int]$Alto = 900
)
$Pptx = (Resolve-Path $Pptx).Path
$app = New-Object -ComObject PowerPoint.Application
try {
    $pres = $app.Presentations.Open($Pptx, $true, $false, $false)   # solo lectura, sin título, sin ventana
    if ($Salida) {
        New-Item -ItemType Directory -Force $Salida | Out-Null
        $pres.Export((Resolve-Path $Salida).Path, "PNG", $Ancho, $Alto)
        Write-Output ("PNG exportados en {0} ({1} diapositivas)" -f $Salida, $pres.Slides.Count)
    }
    if ($Pdf) {
        $pres.SaveAs([IO.Path]::GetFullPath($Pdf), 32)               # 32 = ppSaveAsPDF
        Write-Output "PDF: $Pdf"
    }
    $pres.Close()
}
finally {
    $app.Quit()
}
