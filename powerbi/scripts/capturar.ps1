# Captura uma imagem de cada pagina do painel aberto e grava em docs\img\.
# Captura so a janela do Power BI deste projeto, nao a tela inteira.
# Com -Celular, captura a primeira tela de cada pagina no layout de celular.
param([int]$EsperaPorPaginaSegundos = 12, [switch]$Celular)

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
    # A faixa do cabecalho e a unica regiao da janela com a cor de identidade do tema. Ela
    # tem posicao e largura conhecidas dentro da pagina; dai saem a escala e o canto da pagina.
    param([System.Drawing.Bitmap]$Imagem, [double]$Largura, [double]$Altura, $Faixa)
    $tema = Join-Path $script:PastaPainel "inteligencia-de-compra.Report\StaticResources\RegisteredResources\InteligenciaDeCompra.json"
    $hex = ([IO.File]::ReadAllText($tema, [Text.Encoding]::UTF8) | ConvertFrom-Json).tableAccent
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
    if ($x1 -le $x0 -or $y1 -le $y0) { throw "Faixa do cabecalho nao encontrada na captura." }
    $escala = ($x1 - $x0 + 1) / $Faixa.width
    $esquerda = [math]::Max(0, [int]($x0 - $Faixa.x * $escala))
    $topo = [math]::Max(0, [int]($y0 - $Faixa.y * $escala))
    $larguraFinal = [math]::Min($Imagem.Width - $esquerda, [int]($Largura * $escala))
    $alturaFinal = [math]::Min($Imagem.Height - $topo, [int]($Altura * $escala))
    return New-Object System.Drawing.Rectangle $esquerda, $topo, $larguraFinal, $alturaFinal
}

function Invoke-Botao {
    # Aciona um botao da janela pelo nome, sem mover o mouse.
    param($Raiz, [string]$Nome)
    $condicao = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::NameProperty, $Nome)
    $botao = $Raiz.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condicao) |
        Where-Object { $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button } |
        Select-Object -First 1
    if (-not $botao) { throw "Botao nao encontrado: $Nome" }
    $botao.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    Start-Sleep -Seconds 8
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
# Tela de celular: 320 de largura; a primeira tela tem cerca de 500 de altura.
$larguraCelular = 320; $alturaCelular = 496
if ($Celular) { Invoke-Botao $elemento "Layout m$([char]0xF3)vel" }
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
    $prefixo = if ($Celular) { "celular" } else { "painel" }
    $saida = Join-Path $destino "$prefixo-$nome.png"
    $faixa = ([IO.File]::ReadAllText((Join-Path $paginas "$nome\visuals\${nome}_faixa\visual.json"), [Text.Encoding]::UTF8) | ConvertFrom-Json).position
    if ($Celular) {
        $faixa = ([IO.File]::ReadAllText((Join-Path $paginas "$nome\visuals\${nome}_faixa\mobile.json"), [Text.Encoding]::UTF8) | ConvertFrom-Json).position
        $recorte = Get-AreaDaPagina $imagem $larguraCelular $alturaCelular $faixa
    } else {
        # Os ultimos pontos da margem inferior ficam fora: a dica da aba selecionada
        # aparece por cima deles.
        $recorte = Get-AreaDaPagina $imagem $pagina.width ($pagina.height - 10) $faixa
    }
    $pagina_img = $imagem.Clone($recorte, $imagem.PixelFormat)
    $pagina_img.Save($saida, [System.Drawing.Imaging.ImageFormat]::Png)
    $pagina_img.Dispose(); $imagem.Dispose()
    "capturada: $($pagina.displayName) -> $saida"
}
if ($Celular) { Invoke-Botao $elemento "Layout da $([char]0xE1)rea de trabalho" }
