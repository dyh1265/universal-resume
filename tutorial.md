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

3) Container Apps (HTTPS, Paid)
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

4) CI/CD (Container Apps)
-------------------------

Example workflow: `.github/workflows/deploy-containerapp.yml`.
Secrets:
- `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_CLIENT_SECRET`
- `ACR_NAME`, `RESOURCE_GROUP`, `CONTAINERAPP_NAME`
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`

Notes
-----
- Container Apps provides HTTPS by default but is not fully free.
