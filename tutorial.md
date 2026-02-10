Universal Resume: Full Tutorial
==============================

This guide documents the exact steps used to customize, build, containerize, and deploy the resume site.

Prerequisites
-------------

- Node.js + npm
- Docker Desktop (for container deployment)
- Azure account (for Azure deployment)
- Azure CLI for Windows

Project Structure
-----------------

- `docs/index.html`: main content file
- `tailwind.css`: Tailwind entry + custom CSS
- `tailwind.config.js`: Tailwind theme and utilities
- `postcss.config.js`: PostCSS pipeline
- `docs/`: build output and static assets

1) Customize the Resume Content
-------------------------------

Edit `docs/index.html` and replace the template content with your CV. Keep the same section layout so styling continues to work.

2) Fix Tailwind v4 + PostCSS Integration
----------------------------------------

Tailwind v4 moved the PostCSS plugin to a separate package:

```
npm install @tailwindcss/postcss
```

Update `postcss.config.js` to use the new plugin and point it at the Tailwind config:

```
module.exports = {
  plugins: [
    require("postcss-import"),
    require("@tailwindcss/postcss")({
      config: "./tailwind.config.js"
    }),
    require("autoprefixer"),
    ...process.env.NODE_ENV === "build" ?
      [purgecss, require("cssnano")] : []
  ]
};
```

Update `tailwind.css` to use Tailwind v4 import style:

```
@import "docs/fira-go.css";
@import "tailwindcss";
```

3) Always Two Columns
---------------------

Force two columns at all sizes by using `col-count-2` on the column container.

```
<div class="col-count-2 print:col-count-2 col-gap-md h-letter-col print:h-letter-col col-fill-auto">
```

4) Fix Deprecated Print Color Property
---------------------------------------

Autoprefixer warns about `color-adjust`. Replace it in `tailwind.css`:

```
print-color-adjust: exact !important;
```

5) Build and Serve Locally
--------------------------

Install dependencies:

```
npm install
```

Run the dev server:

```
npm run serve
```

Build optimized CSS for production:

```
npm run build
```

6) Containerize (Production Image)
----------------------------------

The provided `Dockerfile` builds the CSS and serves `docs/` via Nginx.

Build:

```
docker build -t universal-resume .
```

Run:

```
docker run --rm -p 8080:80 universal-resume
```

Open:

```
http://localhost:8080
```

7) Deploy to Azure Storage Static Website
-----------------------------------------

Install Azure CLI:

```
https://aka.ms/installazurecliwindows
```

Login (PowerShell needs `&` for quoted paths):

```
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" login --use-device-code
```

Create a resource group and storage account, enable static website hosting, then upload:

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

8) Deploy to Azure Container Instances (ACI)
---------------------------------------------

This method runs the Docker image in Azure.

Create an Azure Container Registry (ACR), build/push the image, then create the ACI:

```
$rg = "universal-resume-rg"
$loc = "germanywestcentral"
$rand = Get-Random -Maximum 99999
$acr = "resumereg$rand"
$img = "resume-web:1"
$dns = "resume-aci-$rand"

& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" group create --name $rg --location $loc
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" acr create --name $acr --resource-group $rg --location $loc --sku Basic
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" acr login --name $acr

$fullImage = "$acr.azurecr.io/$img"
docker build -t $fullImage .
docker push $fullImage

& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" acr update --name $acr --admin-enabled true
$acrUser = & "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" acr credential show --name $acr --query "username" -o tsv
$acrPass = & "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" acr credential show --name $acr --query "passwords[0].value" -o tsv

& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" container create `
  --resource-group $rg `
  --name $dns `
  --image $fullImage `
  --os-type Linux `
  --cpu 1 `
  --memory 1.5 `
  --registry-login-server "$acr.azurecr.io" `
  --registry-username $acrUser `
  --registry-password $acrPass `
  --ports 80 `
  --dns-name-label $dns `
  --location $loc

$fqdn = & "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" container show --resource-group $rg --name $dns --query "ipAddress.fqdn" -o tsv
"http://$fqdn"
```

Updating Your CV (Free Static Hosting)
--------------------------------------

Edit `docs/index.html`, rebuild, then upload with overwrite:

```
npm run build

$rg = "universal-resume-rg"
$sa = "resumestatic15247"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"

$key = & $az storage account keys list --account-name $sa --resource-group $rg --query "[0].value" -o tsv
& $az storage blob upload-batch --account-name $sa --account-key $key --destination '$web' --source .\docs --overwrite true
```

Your site updates at:

```
https://resumestatic15247.z1.web.core.windows.net/
```

CI/CD (GitHub Actions Auto-Deploy)
----------------------------------

You can deploy automatically on every push to `main` using GitHub Actions.

1) Add the workflow file (already included in this repo):

```
.github/workflows/deploy-azure-static.yml
```

2) Add repository secrets in GitHub:

- `AZURE_STORAGE_ACCOUNT` = `resumestatic15247`
- `AZURE_STORAGE_KEY` = storage account key

3) Push to `main`. The workflow will:

- Install dependencies
- Run `npm run build`
- Upload `docs/` to the `$web` container

If your default branch is not `main`, update the workflow trigger.

Notes
-----

- `docs/build.css` is generated during `npm run build`.
- Azure Static Website is the cheapest for pure static hosting.
- ACI is useful if you want a containerized deployment without Kubernetes.

9) HTTPS for ACI (Recommended: Azure Front Door)
------------------------------------------------

ACI does not provide HTTPS certificates. The recommended approach is to place Azure Front Door in front of the ACI endpoint.

### Create Front Door and enable HTTPS

Replace `$fqdn` with your ACI FQDN (e.g. `resume-aci-xxxxx.germanywestcentral.azurecontainer.io`).

```
$rg = "universal-resume-rg"
$fd = "resume-frontdoor"
$endpoint = "resume-fd-endpoint"
$originGroup = "resume-fd-origins"
$origin = "resume-aci-origin"
$route = "resume-route"
$fqdn = "resume-aci-74506.germanywestcentral.azurecontainer.io"

& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" network front-door create --resource-group $rg --name $fd --backend-address $fqdn
```

This command creates a Front Door profile and exposes a `*.azurefd.net` endpoint with HTTPS enabled by default.
Use the `*.azurefd.net` URL to access your site securely.

### (Optional) Add a custom domain with managed HTTPS

```
$domain = "www.example.com"

& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" network front-door frontend-endpoint create `
  --resource-group $rg `
  --front-door-name $fd `
  --name "custom-domain" `
  --host-name $domain

& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" network front-door frontend-endpoint enable-https `
  --resource-group $rg `
  --front-door-name $fd `
  --name "custom-domain"
```

Then add the DNS CNAME record from your domain to the Front Door endpoint shown in Azure.

Important: Front Door Availability
----------------------------------

Azure Front Door is blocked on Free Trial and Student subscriptions. If you see an error about this, the HTTPS alternative is **Azure Container Apps** (HTTPS by default), but it is not fully free.
