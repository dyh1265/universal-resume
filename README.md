Universal Résumé Template
---------

Minimal and formal résumé (CV) website template for print, mobile, and desktop. The proportions are the same on the screen and paper. Built with amazing [Tailwind CSS](https://tailwindcss.com/).

[Letter Size Demo](https://universal-resume.netlify.app/) | [Multiple Pages Demo](https://universal-resume-pages.netlify.app/) | [A4 Size Demo](https://universal-resume-a4.netlify.app/) | [Mobile Demo](http://www.responsinator.com/?url=https%3A%2F%2Funiversal-resume-pages.netlify.app%2F)

**How to print or save as PDF?**  
In Chrome, Right-click → Print. In Firefox, File → Print. More info [here](#printing).

**Does it support A4 and Letter paper sizes?**  
Yes. Replace every `-letter` with `-a4`, and uncomment specified code blocks. More info [here](#a4-size-variant).

**Why it’s made?**  
I couldn’t find any formal or professional résumé (CV) website with good typography that is optimized for the Web, print, PDF, and mobile. Also, when researching what recruiters want, my priorities were fast scanning time and all content to fit on one page.

How to run it
---------

Navigate to the base directory:

```
cd universal-resume
```

Install the dependencies:

```
npm install
```

Start the development server:

```
npm run serve
```

Only generate CSS that is used on the page, which results in a much smaller file size:

```
npm run build
```

Tutorial: What Was Done
---------

This project was updated and deployed as a static résumé site. Below is a concise walkthrough of the changes and deployment flow so you can repeat it.

### 1) Update the content

- Edit `docs/index.html` and replace the template content with your CV details.
- Keep the overall structure (sections, headers, list items) so the layout stays consistent.

### 2) Tailwind v4 + PostCSS fixes

Tailwind v4 moved its PostCSS plugin to a separate package. The build pipeline was adjusted accordingly:

```
npm install @tailwindcss/postcss
```

In `postcss.config.js`, swap the Tailwind plugin for the new one and pass the config path:

```
require("@tailwindcss/postcss")({
  config: "./tailwind.config.js"
})
```

In `tailwind.css`, use the v4 import style:

```
@import "tailwindcss";
```

### 3) Two-column layout

To force two columns on all screen sizes, use `col-count-2` (without the `md:` prefix) on the column container in `docs/index.html`:

```
<div class="col-count-2 print:col-count-2 col-gap-md h-letter-col print:h-letter-col col-fill-auto">
```

### 4) Replace deprecated CSS

Autoprefixer warns about `color-adjust` being deprecated. Update this in `tailwind.css`:

```
print-color-adjust: exact !important;
```

### 5) Docker production container

A production Docker image builds the CSS and serves the site via Nginx.

```
docker build -t universal-resume .
docker run --rm -p 8080:80 universal-resume
```

### 6) Azure Static Website deployment

This setup uses Azure Storage Static Website hosting.

Install Azure CLI (Windows):

```
https://aka.ms/installazurecliwindows
```

Login (PowerShell needs the `&` call operator):

```
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" login --use-device-code
```

Then create resources and upload:

```
$rg = "universal-resume-rg"
$loc = "germanywestcentral"
$sa = "resumestatic" + (Get-Random -Maximum 99999)

& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" group create --name $rg --location $loc
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage account create --name $sa --resource-group $rg --location $loc --sku Standard_LRS --kind StorageV2 --allow-blob-public-access true
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage blob service-properties update --account-name $sa --static-website --index-document index.html --404-document index.html

$web = & "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage account show --name $sa --resource-group $rg --query "primaryEndpoints.web" -o tsv

$key = & "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage account keys list --account-name $sa --resource-group $rg --query "[0].value" -o tsv
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" storage blob upload-batch --account-name $sa --account-key $key --destination '$web' --source .\docs

$web
```

Starting Point
---------

`docs/index.html` is the main content file. By copying HTML: add pages, sections, subsections, and other parts.

`npm run build` will make the **docs** directory ready for drag-n-drop to, for example, https://app.netlify.com/drop (free registration required beforehand).

Also, with additionally running `git add docs/styles.css -f` and committing changes, it’s ready for push to GitHub and integration with GitHub Pages. GitHub Pages are free for  public repositories. Under your repository name, not profile, click “Settings” and enable GitHub Pages by navigating to: `Options → GitHub Pages → Source → /docs`.

Tailwind CSS
---------

Tailwind CSS is a highly customizable, low-level CSS framework that gives you all of the building blocks you need to build bespoke designs without any annoying opinionated styles you have to fight to override. It has great [documentation](https://tailwindcss.com/docs/installation).

Custom CSS
---------

Code from `tailwind.config.js` and `tailwind.css` transpiles to `docs/style.css`.

Here is the default tailwind config: [defaultConfig.stub.js](https://github.com/tailwindcss/tailwindcss/blob/master/stubs/defaultConfig.stub.js), and here’s the additional information from the Tailwind documentation: [theme](https://tailwindcss.com/docs/theme/#app).

If you want to change CSS in a classical way, add a class to the HTML element and write the CSS inside `tailwind.css`.

Balanced Columns
---------

Removing `col-fill-auto` class will make both columns equally tall. Moreover, removing `md:h-letter` and `md:h-letter-col` classes will eliminate fixed proportions of the letter or A4 page — thereby removing unnecessary vertical space when displaying short columns.

A4 Size Variant
---------

Change the default (letter) size to A4:

**1.** Inside `docs/index.html`, replace every `-letter` with `-a4`.

**2.** Inside `tailwind.config.js`, uncomment code block below `/* For A4 size */` and then comment code block below `/* For Letter size */`

**3.** Inside `tailwind.css`, comment code below `/* For Letter size */` and uncomment code below `/* For A4 size */`

**Important:** Too much content on one page will break the page in the form of additional columns.

Printing
---------

### Chrome

Right-click → Print.  
Also, choose the **Save as PDF** option if needed.

By expanding **More Settings**, change **Page Size** to A4 or Letter.

### Firefox

File → Print.

Choose A4 or Letter size by navigating to **Properties → Advanced → Paper Size**.

### Adobe Acrobat Reader

File → Print.

By clicking on the **Page Setup** button, you are taken to the window with A4 and Letter options.

Blocking Search Engines
---------

Disable search engine indexing by adding the following code to the `<head>`:

```html
<meta name="robots" content="noindex">
```

Language Support
---------

With [FiraGO](https://github.com/bBoxType/FiraGO) typeface, this résumé supports the following scrips: Latin, Cyrillic, Greek, Vietnamese, Arabic, Thai, Georgian, Devanagari, and Hebrew.

If you want to significantly speed up font loading time, find out what fonts you are using (under the developer tools network panel) and add them to the `head` like so:

```html
<link rel="preload" href="./fonts/FiraGO-Regular.latin.woff2" as="font" crossorigin="anonymous">
```

License
---------

NonCommercial-ShareAlike 1.0 Generic (CC NC-SA 1.0)  
https://creativecommons.org/licenses/nc-sa/1.0/

### You are free to:

Share — copy and redistribute the material in any medium or format  

Adapt — remix, transform, and build upon the material

### Under the following terms:

NonCommercial — You may not use the material for commercial purposes.

ShareAlike — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.
