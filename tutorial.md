Universal Resume: Tutorial
=========================

This guide covers editing the CV, building locally, and deploying to Azure (static or Container Apps), plus CI/CD.

Prerequisites
-------------
- Node.js + npm
- Docker Desktop (only for container deployment)
- Azure account
- Azure CLI for Windows

Project Structure
-----------------
- `docs/index.html`: main content
- `tailwind.css`, `tailwind.config.js`, `postcss.config.js`: styling pipeline
- `docs/`: build output
- `Dockerfile.chat`: combined CV + chat container (HTTPS via Container Apps)
- `cv_chat/`: chat backend + context

1) Edit the CV
--------------
Update `docs/index.html` with your content.

2) Local Build
--------------
```
npm install
npm run build
```

Run dev server:
```
npm run serve
```

3) Free Hosting (Azure Static Website)
-------------------------------------
Install Azure CLI:
```
https://aka.ms/installazurecliwindows
```
Login:
```
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" login --use-device-code
```
Create storage + upload:
```
$rg = "universal-resume-rg"
$loc = "germanywestcentral"
$sa = "resumestatic" + (Get-Random -Maximum 99999)

& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" group create --name $rg --location $loc
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage account create --name $sa --resource-group $rg --location $loc --sku Standard_LRS --kind StorageV2 --allow-blob-public-access true
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage blob service-properties update --account-name $sa --static-website --index-document index.html --404-document index.html

$web = & "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage account show --name $sa --resource-group $rg --query "primaryEndpoints.web" -o tsv
$key = & "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage account keys list --account-name $sa --resource-group $rg --query "[0].value" -o tsv
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage blob upload-batch --account-name $sa --account-key $key --destination '$web' --source .\docs --overwrite true

$web
```

Update static site later:
```
npm run build
$key = & $az storage account keys list --account-name resumestatic15247 --resource-group universal-resume-rg --query "[0].value" -o tsv
& $az storage blob upload-batch --account-name resumestatic15247 --account-key $key --destination '$web' --source .\docs --overwrite true
```

4) Container Apps (HTTPS, Paid)
-------------------------------
Build and deploy the combined CV + chat container:
```
$rg = "universal-resume-rg"
$loc = "germanywestcentral"
$acr = "resumereg74506"
$appEnv = "resume-ca-env"
$appName = "resume-ca"
$imgTag = "resume-web:2"
$fullImage = "$acr.azurecr.io/$imgTag"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"

& $az acr login --name $acr

docker build -f Dockerfile.chat -t $fullImage .
docker push $fullImage

$envExists = & $az containerapp env show --name $appEnv --resource-group $rg --query "name" -o tsv 2>$null
if (-not $envExists) { & $az containerapp env create --name $appEnv --resource-group $rg --location $loc }

$appExists = & $az containerapp show --name $appName --resource-group $rg --query "name" -o tsv 2>$null
if ($appExists) {
  & $az containerapp update --name $appName --resource-group $rg --image $fullImage
} else {
  $acrUser = & $az acr credential show --name $acr --query "username" -o tsv
  $acrPass = & $az acr credential show --name $acr --query "passwords[0].value" -o tsv
  & $az containerapp create --name $appName --resource-group $rg --environment $appEnv --image $fullImage `
    --registry-server "$acr.azurecr.io" --registry-username $acrUser --registry-password $acrPass `
    --target-port 8080 --ingress external --min-replicas 1 --max-replicas 1
}

$fqdn = & $az containerapp show --name $appName --resource-group $rg --query "properties.configuration.ingress.fqdn" -o tsv
"https://$fqdn"
```

Chat env vars:
```
& $az containerapp update --name $appName --resource-group $rg `
  --set-env-vars AZURE_OPENAI_API_KEY=YOUR_KEY AZURE_OPENAI_ENDPOINT=YOUR_ENDPOINT
```

5) CI/CD
--------

Static Website auto-deploy workflow: `.github/workflows/deploy-azure-static.yml`.+
Secrets:
- `AZURE_STORAGE_ACCOUNT`
- `AZURE_STORAGE_KEY`

Container Apps CI/CD (example workflow is in this document, add `.github/workflows/deploy-containerapp.yml`):
Secrets:
- `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- `ACR_NAME`, `RESOURCE_GROUP`, `CONTAINERAPP_NAME`
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`

Notes
-----
- Azure Front Door is blocked on Free Trial/Student subscriptions.
- Container Apps provides HTTPS by default but is not fully free.
