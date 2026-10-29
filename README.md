# Six7 landing page

English and Spanish site for Six7. Prepared for Netlify continuous deployment from this repository. No DNS setup is needed to launch on a Netlify-generated address.

## What is included

- English at `/` and Spanish at `/es/`.
- Accessible light/dark selection, following the device preference initially and remembering manual selection across languages.
- CRM, Kanban, Service Desk and C&P app sections with space for future mockups.
- Bilingual footnotes: CRM and Kanban will be tested with personal Gmail accounts for solo businesses. Compatibility is not yet validated.
- Separate English and Spanish A4 PDFs rendered from the supplied HTML, editable HTML packages and five original brand/story artworks.
- Founder story and a single collaborator/build credit in the footer.

## Netlify deployment

1. In Netlify, import this GitHub repository.
2. Set the production branch to `main`.
3. Netlify reads `netlify.toml`: build command `npm run build`, publish directory `dist`, Node 24 and Python 3.12.
4. Deploy and keep Netlify's generated `netlify.app` URL. Do not add a custom domain or change DNS yet.

The app has no npm or Python package dependencies. Netlify's build environment supplies Node and Python. `npm run build` generates the site and stops the deployment if validation fails.

After the Git connection is enabled, Netlify can build Deploy Previews for pull requests. Enable branch deploys in Netlify only for branches you want to preview. The code handles production, Deploy Preview and branch-deploy contexts. The Netlify UI owns whether those deploy types are enabled.

### Deployment details

- Production canonical URLs, Open Graph links, alternate-language links and sitemap use Netlify's `URL` automatically.
- Preview metadata uses `DEPLOY_PRIME_URL`; preview pages, robots.txt and headers request no indexing.
- If/when the custom domain is ready, `SITE_URL=https://six7.work` can override production metadata. This variable only sets metadata; it never configures DNS.
- CSS and JavaScript use content hashes with immutable browser caching. HTML revalidates; original downloadable assets use shorter caching.
- `_headers` adds CSP, MIME-sniffing, referrer and permission policies. Preview CSP allows Netlify's documented Drawer frame origin.
- `_redirects` normalizes English language aliases. No SPA catch-all: unknown routes serve the bilingual `404.html` with a real 404 status on Netlify.
- GitHub Actions runs the build and deployment-context checks on main pushes and pull requests.
- No functions, database, analytics or credentials are needed for this landing page.

The generated files are committed in `dist/`. For manual deployment to an already known address, build with `SITE_URL=https://your-project.netlify.app npm run build` and upload the contents of `dist/`, including `_headers` and `_redirects`.

## Local development

Use Node 24 and Python 3.12.

```sh
npm ci --ignore-scripts
npm run build
npm run dev
```

Open `http://localhost:8000`.

```sh
npm run check
python3 scripts/check_contexts.py
```

## Editing

- `build.py`: bilingual content and page structure.
- `theme.css`: theme styling.
- `theme-controls.js`: theme selection.
- `theme-init.js`: early theme loading, before first render.
- `scripts/finalize_build.py`: hashed assets, 404 and Netlify headers/redirects.
- `scripts/check_site.py`: deploy-blocking content/link/JavaScript/config checks.
- `scripts/check_contexts.py`: production and preview metadata checks.
- `dist/assets/`: original artwork and downloadable materials.

C&P currently follows the contract-register description in the supplied one-pager. The site uses a compact alpha-interest form prepared for Netlify Forms. Enable form detection in Netlify before deployment. Requests appear in the Netlify Forms dashboard; email notifications require separate configuration. The new PDFs use Six7 alpha-programme text instead of the source contact placeholder and include the personal-Gmail testing footnote. Original HTML ZIP packages and the original bilingual PDF remain available as source/archive materials. The light-theme logo uses black Six lettering and a papaya 7 on transparency; the original artwork remains in the resource archive.

All brand assets remain the property of their respective owner. Google Workspace is a trademark of Google LLC; Six7 is not affiliated with Google.

## Regenerating the one-page PDFs

Normal Netlify builds serve the checked-in PDFs and need no extra packages. For editorial PDF regeneration only, install `weasyprint==70.0` and a Helvetica-compatible sans-serif font (Nimbus Sans / Nimbus Sans Narrow were used for the verified export), then run:

```sh
python3 scripts/render_one_pagers.py
```

The source is `one-pagers/en.html` and `one-pagers/es.html`, adapted from the supplied HTML exports. `one-pagers/print.css` makes the exports fit one A4 page in each language. Review the rendered PDFs after edits.

## Build credit

Built in collaboration with Entangled Forge using Anthropic Claude and Omarchy on a repurposed seven-year-old notebook.

## App mockups

The received `(2).zip` files are English/Spanish one-pager exports, identical in content to the earlier exports. They do not contain the four app mockups. App preview panels remain labelled forthcoming until the app assets are supplied.
