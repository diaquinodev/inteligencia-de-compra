# Compara os numeros do painel aberto (medidas DAX) com os valores calculados no BigQuery.
# Antes: python -m compras esperado   (grava powerbi\esperado.json)
#        powerbi\scripts\abrir.ps1    (abre o painel e carrega os dados)
# Sai com codigo 1 se algum numero divergir.
param([double]$Tolerancia = 1e-6)

. (Join-Path $PSScriptRoot "comum.ps1")
Import-Adomd

$arquivo = Join-Path $script:PastaPainel "esperado.json"
if (-not (Test-Path $arquivo)) { throw "Falta $arquivo. Rode: python -m compras esperado" }
$esperado = [IO.File]::ReadAllText($arquivo, [Text.Encoding]::UTF8) | ConvertFrom-Json

$dax = Get-MedidasDax
$conexao = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$(Get-PortaDoPainel)")
$conexao.Open()
$total = (Invoke-Dax $conexao ($dax.Definicoes + $dax.Consultas[0]))[0]
$porCategoria = Invoke-Dax $conexao ($dax.Definicoes + $dax.Consultas[1])
$conexao.Close()

$script:falhas = 0
$script:conferidos = 0
function Compare-Valor {
    param([string]$Rotulo, $Painel, $BigQuery)
    $script:conferidos++
    $diferenca = [math]::Abs([double]$Painel - [double]$BigQuery)
    $limite = $Tolerancia * [math]::Max(1.0, [math]::Abs([double]$BigQuery))
    if ($diferenca -le $limite) {
        "ok      {0,-44} {1,22:N4}" -f $Rotulo, [double]$Painel
    } else {
        $script:falhas++
        "FALHOU  {0,-44} painel={1:N4}  bigquery={2:N4}" -f $Rotulo, [double]$Painel, [double]$BigQuery
    }
}

foreach ($propriedade in $esperado.total.PSObject.Properties) {
    if (-not $total.Contains($propriedade.Name)) {
        $script:conferidos++; $script:falhas++
        "FALHOU  $($propriedade.Name): a consulta de conferencia nao devolve essa medida"
        continue
    }
    Compare-Valor $propriedade.Name $total[$propriedade.Name] $propriedade.Value
}
foreach ($categoria in $esperado.categoria.PSObject.Properties) {
    $linha = $porCategoria | Where-Object { $_["categoria"] -eq $categoria.Name }
    if (-not $linha) {
        $script:conferidos++; $script:falhas++
        "FALHOU  categoria ausente no painel: $($categoria.Name)"
        continue
    }
    foreach ($propriedade in $categoria.Value.PSObject.Properties) {
        Compare-Valor "$($categoria.Name) / $($propriedade.Name)" $linha[$propriedade.Name] $propriedade.Value
    }
}

"{0} de {1} valores conferem com o BigQuery." -f ($script:conferidos - $script:falhas), $script:conferidos
if ($script:falhas -gt 0) { exit 1 }
