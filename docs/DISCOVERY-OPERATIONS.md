# Six7 discovery operations — 2026-11-08

## Product decisions

Six7 is customer-owned business software, not a hosted SaaS subscription. Google Workspace is the initial validation environment, not the permanent company/product boundary. Support for additional platforms is a future direction, not an available feature claim.

Google Workspace Marketplace distribution and certification are CLOSED for this roadmap, at the founder's direction. No Marketplace application, certification task, app-store launch or SaaS relabelling is required for website visibility. Reopen only on explicit future instruction.

Keep the solo-business segment: personal Gmail testing for CRM and Kanban is planned, not validated. Retainer prices are unchanged. Six7 is a product incubated within Entangled Forge; do not conflate it with the consulting business or use Entangled Forge profiles as Six7 sameAs identities.

## What this repository controls

- Netlify build command `npm run build`, publish directory `dist` and production `SITE_URL=https://six7.work`.
- English and Spanish HTML titles, descriptions, visible introduction and JSON-LD use consistent customer-owned-software positioning.
- Canonical URLs, reciprocal en/es/x-default links and sitemap entries agree.
- Production robots.txt allows crawling. Preview robots and response headers remain non-indexable. This change preserves the existing training-crawler policy.
- Optional llms.txt describes actual scope and alpha limitations. It is not a Google ranking mechanism.
- `six7-build` HTML metadata records Netlify COMMIT_REF (or the GitHub test SHA), allowing actual deployment verification rather than assuming a merge means a deploy.
- Build-blocking discovery assertions run automatically in local, production, preview and branch-deploy context tests.
- GitHub CI records read-only DNS, TLS/HTTP, redirect, bot-user-agent and metadata observations in `discovery-audit.json`. It probes Google and Cloudflare public DNS resolvers and includes a control domain. User-agent simulation is not proof of real crawler-origin access. A successful diagnostic script is not a successful live-deployment certificate.

## Account-only checks, not completed by a code merge

### Netlify

Open the `six7-landing` project. Confirm its production branch is `main`, its published deploy corresponds to the merged commit, and production deployments are not locked or paused. Confirm `six7.work` is assigned to this project and is the primary domain; `www.six7.work` should be the alternate. Verify certificate coverage for both names and HTTPS redirection. Check password protection and bot/WAF controls without disabling protections indiscriminately.

The metadata origin is pinned in `netlify.toml`; this does NOT assign a custom domain, provision a certificate, change registrar records or verify Search Console ownership. Do not add a www-to-apex forced code redirect before verifying the account's primary-domain setting: conflicting automatic redirects can loop.

### GoDaddy / authoritative DNS provider

Determine the authoritative nameservers first. Buying the domain at GoDaddy does not imply the live DNS zone is hosted there. If it uses GoDaddy nameservers, edit the GoDaddy zone; if it uses Netlify or another provider's nameservers, manage records there.

Keep the existing DNS provider unless there is a demonstrated reason to migrate. Export the zone before any write. Preserve MX, SPF, DKIM, DMARC, verification TXT and unrelated subdomains. Change only proven incorrect website records; do not reset the zone or change nameservers as a blanket SEO fix.

For Netlify's standard network with external DNS, official documentation lists apex ALIAS/ANAME to `apex-loadbalancer.netlify.com`, or an A-record fallback of `75.2.60.5` when flattening is unavailable. A www CNAME should target the exact assigned project hostname, expected here to be `six7-landing.netlify.app`. Treat these as conditional reference values, not instructions to overwrite an already-working zone. The project's customized Pending DNS verification instructions take precedence, particularly for High-Performance Edge. Reconcile conflicting A/AAAA/CNAME records only after checking the live zone and project settings.

### Search ownership and measurement

Verify a Google Search Console domain property for `six7.work` using the exact owner-specific DNS record Google issues. Do not invent a verification token or publish placeholders. Verify/import the site in Bing Webmaster Tools. Submit `https://six7.work/sitemap.xml`, inspect `/` and `/es/`, and request indexing after the live tests pass. A sitemap submission, HTTP 200 or schema validation does not prove indexing or guarantee rankings.

## Release acceptance

1. Full repository build and all context/discovery tests pass.
2. The production homepage and Spanish page return HTTPS 200 with the merged release marker, correct canonical and no noindex directive.
3. robots.txt, sitemap.xml and llms.txt are retrievable with appropriate text/XML content, not HTML error pages.
4. The www and HTTP variants reach the intended primary HTTPS URL without loops; a missing route returns a real 404.
5. DNS observations agree with the actual hosting account; search ownership and sitemap submission are confirmed by the account owner.

Do not describe an item as complete merely because its code has merged. The existing README's initial-launch advice to avoid custom-domain/DNS setup is historical; this document governs the production discovery rollout.

## Official references checked 2026-11-08

- Netlify external DNS: https://docs.netlify.com/manage/domains/configure-domains/configure-external-dns/
- Netlify domain assignment: https://docs.netlify.com/manage/domains/manage-domains/assign-a-domain-to-your-site-app/
- GoDaddy DNS management: https://www.godaddy.com/help/manage-dns-records-680
- Google ownership verification: https://support.google.com/webmasters/answer/9008080
- Google AI search guidance: https://developers.google.com/search/docs/appearance/ai-features

Google explicitly says that its AI search features need no special AI text files or schema. Prioritize accessibility, indexability, useful visible content and accurate entity identity rather than unverified GEO claims.
