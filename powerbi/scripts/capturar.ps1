# Captura uma imagem de cada pagina do painel aberto e grava em docs\img\.
# Captura so a janela do Power BI deste projeto, nao a tela inteira.
param([int]$EsperaPorPaginaSegundos = 12)

. (Join-Path $PSScriptRoot "comum.ps1")
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class JanelaDoPainel {
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@

function Get-AreaDaPagina {
    # A pagina e a unica regiao da janela com a cor de fundo do tema; o retangulo que contem
    # todos os pontos dessa cor e a pagina, sem menus nem paineis laterais.
    param([System.Drawing.Bitmap]$Imagem)
    $tema = Join-Path $script:PastaPainel "inteligencia-de-compra.Report\StaticResources\RegisteredResources\InteligenciaDeCompra.json"
    $hex = ([IO.File]::ReadAllText($tema, [Text.Encoding]::UTF8) | ConvertFrom-Json).visualStyles.page.'*'.background[0].color.solid.color
    $alvo = [System.Drawing.ColorTranslator]::FromHtml($hex).ToArgb()
    $x0 = $Imagem.Width; $y0 = $Imagem.Height; $x1 = 0; $y1 = 0
    for ($y = 0; $y -lt $Imagem.Height; $y += 2) {
        for ($x = 0; $x -lt $Imagem.Width; $x += 2) {
            if ($Imagem.GetPixel($x, $y).ToArgb() -eq $alvo) {
                if ($x -lt $x0) { $x0 = $x }; if ($x -gt $x1) { $x1 = $x }
                if ($y -lt $y0) { $y0 = $y }; if ($y -gt $y1) { $y1 = $y }
            }
        }
    }
    if ($x1 -le $x0 -or $y1 -le $y0) { throw "Area da pagina nao encontrada na captura." }
    return New-Object System.Drawing.Rectangle $x0, $y0, ($x1 - $x0 + 1), ($y1 - $y0 + 1)
}

$painel = Get-ProcessoDoPainel
$janela = $painel.MainWindowHandle
[JanelaDoPainel]::ShowWindow($janela, 3) | Out-Null   # maximiza
Start-Sleep -Seconds 2

$raiz = (Split-Path $script:PastaPainel -Parent)
$destino = Join-Path $raiz "docs\img"
New-Item -ItemType Directory -Force $destino | Out-Null
$paginas = Join-Path $script:PastaPainel "inteligencia-de-compra.Report\definition\pages"
$ordem = ([IO.File]::ReadAllText((Join-Path $paginas "pages.json"), [Text.Encoding]::UTF8) | ConvertFrom-Json).pageOrder

$elemento = [System.Windows.Automation.AutomationElement]::FromHandle($janela)
foreach ($nome in $ordem) {
    $pagina = [IO.File]::ReadAllText((Join-Path $paginas "$nome\page.json"), [Text.Encoding]::UTF8) | ConvertFrom-Json
    $condicao = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::NameProperty, $pagina.displayName)
    # A arvore de acessibilidade do Power BI demora a aparecer na primeira consulta.
    $aba = $null
    for ($tentativa = 0; $tentativa -lt 10 -and -not $aba; $tentativa++) {
        $aba = $elemento.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condicao) |
            Where-Object { $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem } |
            Select-Object -First 1
        if (-not $aba) { Start-Sleep -Seconds 2 }
    }
    if (-not $aba) { throw "Aba da pagina nao encontrada: $($pagina.displayName)" }
    $aba.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
    Start-Sleep -Seconds $EsperaPorPaginaSegundos

    $r = New-Object JanelaDoPainel+RECT
    [JanelaDoPainel]::GetWindowRect($janela, [ref]$r) | Out-Null
    $imagem = New-Object System.Drawing.Bitmap ($r.R - $r.L), ($r.B - $r.T)
    $grafico = [System.Drawing.Graphics]::FromImage($imagem)
    $hdc = $grafico.GetHdc()
    [JanelaDoPainel]::PrintWindow($janela, $hdc, 2) | Out-Null
    $grafico.ReleaseHdc($hdc); $grafico.Dispose()
    $saida = Join-Path $destino "painel-$nome.png"
    $recorte = Get-AreaDaPagina $imagem
    # A cor de fundo continua abaixo da pagina; a altura sai da proporcao definida em page.json.
    $recorte.Height = [math]::Min($recorte.Height, [int]($recorte.Width * $pagina.height / $pagina.width))
    $pagina_img = $imagem.Clone($recorte, $imagem.PixelFormat)
    $pagina_img.Save($saida, [System.Drawing.Imaging.ImageFormat]::Png)
    $pagina_img.Dispose(); $imagem.Dispose()
    "capturada: $($pagina.displayName) -> $saida"
}
