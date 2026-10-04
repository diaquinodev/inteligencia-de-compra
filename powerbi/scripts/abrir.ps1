# Abre o projeto no Power BI Desktop e carrega os dados do BigQuery, sem cliques.
# Uso: powershell -ExecutionPolicy Bypass -File powerbi\scripts\abrir.ps1
param([int]$EsperaMaximaSegundos = 420)

. (Join-Path $PSScriptRoot "comum.ps1")
Import-Tom
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

# Fecha so a janela deste projeto, se houver; outros arquivos abertos ficam como estao.
$nome = [IO.Path]::GetFileName($script:Projeto)
Get-CimInstance Win32_Process -Filter "Name = 'PBIDesktop.exe'" |
    Where-Object { $_.CommandLine -like "*$nome*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Start-Process $script:Projeto
"abrindo $nome ..."
$limite = (Get-Date).AddSeconds($EsperaMaximaSegundos)

# Espera a pagina do relatorio aparecer na tela. Carregar dados antes disso trava o Power BI:
# a carga segura o modelo enquanto a abertura do arquivo ainda precisa dele.
$paginas = Join-Path $script:PastaPainel "inteligencia-de-compra.Report\definition\pages"
$primeira = ([IO.File]::ReadAllText((Join-Path $paginas "pages.json"), [Text.Encoding]::UTF8) | ConvertFrom-Json).pageOrder[0]
$titulo = ([IO.File]::ReadAllText((Join-Path $paginas "$primeira\page.json"), [Text.Encoding]::UTF8) | ConvertFrom-Json).displayName
$condicao = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NameProperty, $titulo)
$pronto = $false
while (-not $pronto -and (Get-Date) -lt $limite) {
    Start-Sleep -Seconds 5
    try {
        $janela = (Get-ProcessoDoPainel).MainWindowHandle
        if ($janela -ne 0) {
            $raiz = [System.Windows.Automation.AutomationElement]::FromHandle($janela)
            $pronto = $raiz.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condicao).Count -gt 0
        }
    } catch { }
}
if (-not $pronto) { throw "O Power BI nao mostrou o relatorio em $EsperaMaximaSegundos segundos." }
Start-Sleep -Seconds 5
"relatorio aberto. Carregando os dados do BigQuery ..."

$servidor = New-Object Microsoft.AnalysisServices.Tabular.Server
$servidor.Connect("Data Source=localhost:$(Get-PortaDoPainel)")
$modelo = $servidor.Databases[0].Model

# Se o conector do BigQuery ainda nao estiver disponivel, a carga falha; tenta de novo.
$cronometro = [Diagnostics.Stopwatch]::StartNew()
$carregado = $false
$ultimoErro = ""
while (-not $carregado -and (Get-Date) -lt $limite) {
    try {
        $modelo.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
        $modelo.SaveChanges() | Out-Null
        $carregado = $true
    } catch {
        $ultimoErro = $_.Exception.Message
        $modelo.UndoLocalChanges()
        Start-Sleep -Seconds 10
    }
}
$servidor.Disconnect()
if (-not $carregado) { throw "A carga dos dados falhou: $ultimoErro" }
"dados carregados em {0:N0} s. O painel esta pronto." -f $cronometro.Elapsed.TotalSeconds
