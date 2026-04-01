Universal Resume: Tutorial
=========================

This guide covers editing the CV, building locally, and deploying to Azure (static or Container Apps), plus CI/CD and **cost management** (Container Apps scale, ACR image cleanup).

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
  --set-env-vars AZURE_OPENAI_API_KEY=YOUR_KEY AZURE_OPENAI_ENDPOINT=YOUR_ENDPOINT AZURE_OPENAI_DEPLOYMENT=YOUR_DEPLOYMENT
```

Restart Container App (without changing the image):
```
& $az containerapp restart --name $appName --resource-group $rg
```

4) CI/CD (Container Apps)
-------------------------

Example workflow: `.github/workflows/deploy-containerapp.yml`.
Secrets:
- `AZURE_CREDENTIALS` (JSON from `az ad sp create-for-rbac --sdk-auth`)
- `ACR_NAME`, `RESOURCE_GROUP`, `CONTAINERAPP_NAME`
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`

5) Managing costs (Container Apps + ACR)
-----------------------------------------
Azure is **not fully free** while resources exist. Typical bill categories:

- **Azure Container Apps** — compute when replicas run; scales down when `minReplicas = 0` and traffic stops.
- **Container Registry (ACR)** — stores pushed images; old tags still use storage until deleted.
- **Azure Container Instances (ACI)** — a *different* product from Container Apps. If Cost Management shows large **Container Instances** charges (e.g. vCPU/memory duration in a region like **US West Central**), some **container group** is still running there. Tuning Container Apps or ACR will **not** remove that bill until you **delete or stop** those ACI resources.
- Other services (OpenAI, etc.) may also appear; use Cost Management → drill down by **Resource** to see exact names.

**Find and remove Azure Container Instances (ACI) waste**

Portal: search for **Container instances**, open each **container group**, delete what you do not need.

CLI — list every container group in the subscription (note resource group and location):

```
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"

& $az resource list --resource-type "Microsoft.ContainerInstance/containerGroups" -o table
```

Delete one container group (replace resource group and name):

```
& $az container delete --resource-group RESOURCE_GROUP --name CONTAINER_GROUP_NAME --yes
```

If the bill line mentions **US West Central**, focus on groups in that region; they may live in a different resource group than your résumé Container App (e.g. Germany West Central).

**Understanding Container Apps meters (idle vs active)**  
Cost analysis may show **Standard vCPU/Memory Idle Usage** vs **Active Usage**. High idle usually means replicas were **running** with little traffic for part of the period (e.g. `minReplicas` was 1, or something kept waking the app). Use `minReplicas = 0`, avoid uptime pings on the public URL, and confirm replicas are gone after idle with `replica list`.

**Scale to zero when idle (non-destructive)**  
Keeps the app; replicas can shut down after idle. `--max-replicas` must be at least **1** (Azure does not allow 0).

```
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$rg = "universal-resume-rg"
$appName = "resume-ca"

& $az containerapp update --name $appName --resource-group $rg --min-replicas 0 --max-replicas 1
```

**Optional: stop traffic immediately** (deactivate latest revision; URL may show 404 until you reactivate):

```
$rev = & $az containerapp show --name $appName --resource-group $rg --query "properties.latestRevisionName" -o tsv
& $az containerapp revision deactivate --name $appName --resource-group $rg --revision $rev
```

**Verify scale and replicas**

```
& $az containerapp show --name $appName --resource-group $rg --query "properties.template.scale" -o json
& $az containerapp replica list --name $appName --resource-group $rg -o table
```

**Resume (always-on minimum one replica)**

```
& $az containerapp update --name $appName --resource-group $rg --min-replicas 1 --max-replicas 1
```

**If you see: `404 - This Container App is stopped or does not exist`**  
The revision was deactivated. Reactivate it:

```
$rev = & $az containerapp show --name $appName --resource-group $rg --query "properties.latestRevisionName" -o tsv
& $az containerapp revision activate --name $appName --resource-group $rg --revision $rev
```

**Deep hibernation (max savings, deletes the Container App)**

```
& $az containerapp delete --name $appName --resource-group $rg --yes
```

You can recreate the app later with the deploy block in section 3).

**ACR: list repositories and tags**

Use the same registry name as in section 3 (`$acr = "resumereg74506"`). Image repository is typically `resume-web`.

```
& $az acr login --name $acr
& $az acr repository list --name $acr -o table
& $az acr repository show-tags --name $acr --repository "resume-web" -o table
```

**ACR: which tag is safe to keep?**  
Always match the tag your Container App runs (from CI/CD or manual deploy):

```
& $az containerapp show --name $appName --resource-group $rg --query "properties.template.containers[0].image" -o tsv
```

Example output: `resumereg74506.azurecr.io/resume-web:5fe64852fb43f448b64c0d95ef202fc62cdfe81f` → keep tag `5fe64852fb43f448b64c0d95ef202fc62cdfe81f`, delete other tags.

**ACR: delete one old tag** (repeat for each tag you no longer need; do not delete the tag in the image URL above).

```
& $az acr repository delete --name $acr --image "resume-web:OLD_TAG" --yes
```

**ACR: bulk delete** (PowerShell — copy tag names from `show-tags` into `$tags`, except the live tag):

```
$keep = "YOUR_LIVE_TAG_FROM_containerapp_show"
$tags = @("tag1", "tag2")  # all tags to remove; omit $keep

foreach ($t in $tags) {
  if ($t -eq $keep) { continue }
  & $az acr repository delete --name $acr --image "resume-web:$t" --yes
}
```

Re-check tags:

```
& $az acr repository show-tags --name $acr --repository "resume-web" -o table
```

Tips:

- Avoid uptime monitors hitting the public URL if you want the app to stay scaled to zero.
- Closing a browser tab does **not** stop Azure billing; idle scale-down happens after a cooldown.
- For more detail, see `README.md` section **Cost control (pause / resume)** and Azure Cost Management.

Notes
-----
- Container Apps provides HTTPS by default but is not fully free.
- See **5) Managing costs** for pause/resume, 404 recovery, and ACR cleanup.
