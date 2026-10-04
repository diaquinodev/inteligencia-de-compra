# Funcoes compartilhadas pelos scripts do painel.
# Conversam com o motor local que o Power BI Desktop abre para cada arquivo (Analysis Services).

$ErrorActionPreference = "Stop"
$script:PastaPainel = Split-Path $PSScriptRoot -Parent
$script:Projeto = Join-Path $script:PastaPainel "inteligencia-de-compra.pbip"
$script:Bibliotecas = Join-Path $PSScriptRoot ".bibliotecas"

function Get-Biblioteca {
    # Baixa do NuGet (uma vez) as bibliotecas cliente da Microsoft e devolve a pasta das DLLs.
    param([Parameter(Mandatory)][string]$Pacote)
    $destino = Join-Path $script:Bibliotecas $Pacote
    $dlls = Join-Path $destino "lib\net45"
    if (-not (Test-Path $dlls)) {
        New-Item -ItemType Directory -Force $script:Bibliotecas | Out-Null
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $ProgressPreference = "SilentlyContinue"
        $zip = Join-Path $script:Bibliotecas "$Pacote.zip"
        Invoke-WebRequest "https://www.nuget.org/api/v2/package/$Pacote" -OutFile $zip -UseBasicParsing
        Expand-Archive $zip -DestinationPath $destino -Force
        Remove-Item $zip
    }
    return $dlls
}

function Import-Tom {
    $dlls = Get-Biblioteca "Microsoft.AnalysisServices.retail.amd64"
    Add-Type -Path (Join-Path $dlls "Microsoft.AnalysisServices.Core.dll")
    Add-Type -Path (Join-Path $dlls "Microsoft.AnalysisServices.Tabular.dll")
}

function Import-Adomd {
    $dlls = Get-Biblioteca "Microsoft.AnalysisServices.AdomdClient.retail.amd64"
    Add-Type -Path (Join-Path $dlls "Microsoft.AnalysisServices.AdomdClient.dll")
}

function Get-ProcessoDoPainel {
    # O Power BI Desktop aberto com o projeto deste repositorio (nao outros arquivos abertos).
    $nome = [IO.Path]::GetFileName($script:Projeto)
    $achado = Get-CimInstance Win32_Process -Filter "Name = 'PBIDesktop.exe'" |
        Where-Object { $_.CommandLine -like "*$nome*" } |
        Sort-Object CreationDate -Descending | Select-Object -First 1
    if (-not $achado) { throw "O projeto nao esta aberto no Power BI Desktop. Rode abrir.ps1." }
    return Get-Process -Id $achado.ProcessId
}

function Get-PortaDoPainel {
    # A porta fica num arquivo dentro da pasta de trabalho do motor, que e filho do Power BI.
    $painel = Get-ProcessoDoPainel
    $motor = Get-CimInstance Win32_Process -Filter "Name = 'msmdsrv.exe' AND ParentProcessId = $($painel.Id)" |
        Select-Object -First 1
    if (-not $motor) { throw "O motor local do Power BI ainda nao subiu." }
    if ($motor.CommandLine -notmatch '-s\s+"([^"]+)"') { throw "Pasta de trabalho do motor nao encontrada." }
    $arquivo = Join-Path $Matches[1] "msmdsrv.port.txt"
    return (Get-Content $arquivo -Encoding Unicode).Trim()
}

function Get-MedidasDax {
    # Bloco DEFINE e consultas de conferencia de medidas.dax.
    $texto = [IO.File]::ReadAllText((Join-Path $script:PastaPainel "medidas.dax"), [Text.Encoding]::UTF8)
    # A primeira linha que comeca com EVALUATE; a palavra tambem aparece em comentarios.
    $corte = [regex]::Match($texto, "(?m)^EVALUATE").Index
    if ($corte -le 0) { throw "medidas.dax nao tem consulta EVALUATE." }
    return @{
        Definicoes = $texto.Substring(0, $corte)
        Consultas  = @($texto.Substring($corte) -split "(?m)^(?=EVALUATE)" | Where-Object { $_.Trim() })
    }
}

function Invoke-Dax {
    # Executa uma consulta DAX e devolve as linhas como tabelas de nome -> valor.
    param([Parameter(Mandatory)]$Conexao, [Parameter(Mandatory)][string]$Consulta)
    $comando = $Conexao.CreateCommand()
    $comando.CommandText = $Consulta
    $leitor = $comando.ExecuteReader()
    $linhas = @()
    while ($leitor.Read()) {
        $linha = [ordered]@{}
        for ($i = 0; $i -lt $leitor.FieldCount; $i++) {
            # "[Gasto Total]" e "dim_item[categoria]" viram "Gasto Total" e "categoria".
            $nome = $leitor.GetName($i) -replace '^.*\[', '' -replace '\]$', ''
            $linha[$nome] = $leitor.GetValue($i)
        }
        $linhas += , $linha
    }
    $leitor.Close()
    return , $linhas
}
