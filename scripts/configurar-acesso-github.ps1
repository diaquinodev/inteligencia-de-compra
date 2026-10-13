# Da ao GitHub Actions deste repositorio acesso ao BigQuery, sem arquivo de chave.
# Roda uma vez, por quem e dono do projeto no Google Cloud. Rodar de novo nao estraga nada:
# o que ja existe da erro de "already exists" e o script segue.
#
#   powershell -File scripts\configurar-acesso-github.ps1
#
# O que cria:
#   1. uma conta de servico (a identidade do robo), sem chave;
#   2. permissao para ela criar consultas no projeto e escrever SO no conjunto "compras";
#   3. um provedor de identidade que aceita SO este repositorio, na branch main;
#   4. duas variaveis no repositorio do GitHub (nao sao segredos: sao so enderecos).
param(
    [string]$Projeto = "inteligencia-de-compra",
    [string]$Repositorio = "diaquinodev/inteligencia-de-compra",
    [string]$Conjunto = "compras"
)

$conta = "github-dados"
$email = "$conta@$Projeto.iam.gserviceaccount.com"
$numero = gcloud projects describe $Projeto --format="value(projectNumber)"

gcloud services enable iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com --project $Projeto

gcloud iam service-accounts create $conta --project $Projeto --display-name "GitHub Actions: pipeline de dados"

# Criar consultas: no projeto. Escrever tabelas: so no conjunto.
gcloud projects add-iam-policy-binding $Projeto --member "serviceAccount:$email" --role "roles/bigquery.jobUser" --condition None
$concessao = "GRANT ``roles/bigquery.dataEditor`` ON SCHEMA ``$Projeto.$Conjunto`` TO 'serviceAccount:$email'"
cmd /c "bq query --project_id=$Projeto --use_legacy_sql=false `"$concessao`""

gcloud iam workload-identity-pools create github --project $Projeto --location global --display-name "GitHub Actions"
gcloud iam workload-identity-pools providers create-oidc github --project $Projeto --location global `
    --workload-identity-pool github `
    --issuer-uri "https://token.actions.githubusercontent.com" `
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" `
    --attribute-condition "assertion.repository == '$Repositorio' && assertion.ref == 'refs/heads/main'"

gcloud iam service-accounts add-iam-policy-binding $email --project $Projeto `
    --role "roles/iam.workloadIdentityUser" `
    --member "principalSet://iam.googleapis.com/projects/$numero/locations/global/workloadIdentityPools/github/attribute.repository/$Repositorio"

gh variable set GCP_PROVEDOR --repo $Repositorio --body "projects/$numero/locations/global/workloadIdentityPools/github/providers/github"
gh variable set GCP_CONTA_DE_SERVICO --repo $Repositorio --body $email

"Pronto. Dispare o workflow: gh workflow run dados.yml --repo $Repositorio"
