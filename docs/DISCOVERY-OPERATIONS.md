# Six7 discovery operations — 2026-11-08

## Product decisions

Six7 is customer-owned business software, not a hosted SaaS subscription. Google Workspace is the initial validation environment, not the permanent company/product boundary. Support for additional platforms is a future direction, not an available feature claim.

Google Workspace Marketplace distribution and certification are CLOSED for this roadmap, at the founder's direction. No Marketplace application, certification task, app-store launch or SaaS relabelling is required for website visibility. Reopen only on explicit future instruction.

Keep the solo-business segment: personal Gmail testing for CRM and Kanban is planned, not validated. Retainer prices are unchanged. Six7 is a product incubated within Entangled Forge; do not conflate it with the consulting business or use Entangled Forge profiles as Six7 sameAs identities.

## Verified baseline — 2026-11-08 14:11 UTC

Evidence: GitHub Actions run 42488547045, job 128755654855, artifact 13620945526 (six7-discovery-audit). https://github.com/dreamsgarage/Six7-landing/actions/runs/42488547045

Independent network checks from the GitHub runner returned:

| Check | Observed result |
| --- | --- |
| English and Spanish homepages | HTTPS 200; correct six7.work canonical; no noindex |
| robots.txt | 200 text/plain; Allow: /; correct sitemap |
| sitemap.xml | 200 application/xml; / and /es/ |
| llms.txt from preceding release | 200 text/plain |
| www.six7.work | 301 to https://six7.work/ |
| http://six7.work/ | 301 to HTTPS |
| Missing route | Real HTTP 404 with noindex |
| Five simulated search-agent user agents | 200; simulation does not verify actual provider-origin access |
| Default six7-landing.netlify.app hostname | 200 duplicate page, not redirected — addressed by this patch |

Google and Cloudflare public DNS both reported `dns1.p03.nsone.net`, `dns2.p03.nsone.net`, `dns3.p03.nsone.net`, and `dns4.p03.nsone.net`. DNS SOA identifies `domains+netlify.netlify.com`. The live zone is delegated to Netlify's DNS infrastructure, not GoDaddy's nameservers. No DNS outage was found in this baseline. These are observations from a runner and two resolvers, not a worldwide uptime claim.

Do not overwrite this functioning managed-DNS setup with generic GoDaddy A/CNAME instructions. No registrar, nameserver, DNS or email-record changes were performed.

## Repository-managed changes

- Netlify production SITE_URL is pinned to https://six7.work. This sets metadata, not account-level domain ownership.
- English and Spanish titles, descriptions, visible introductions and JSON-LD agree on customer-owned software and broader-than-Google scope.
- Reciprocal en/es/x-default links and sitemap entries agree with canonical URLs.
- Production robots.txt allows crawling; previews remain noindex/Disallow. The existing training-crawler policy is preserved.
- Exact production Netlify hostnames redirect permanently to six7.work, preserving paths. Preview hostnames are unaffected. Existing www and HTTP redirects were already working.
- Optional llms.txt states alpha status, planned solo/Gmail tests and scope boundaries. It is not a Google ranking mechanism.
- The six7-build HTML marker records Netlify COMMIT_REF or the GitHub test SHA.
- Build-blocking discovery assertions run with production/preview/context tests.
- Public CI diagnostics preserve DNS/HTTP/redirect/metadata evidence in discovery-audit.json. On main pushes, a bounded readiness check requires the exact published commit, valid EN/ES pages, canonical redirects, discovery files and a true 404. A failure indicates the release was not verified, not necessarily that the site is globally down.

## Account-only work still required

### Netlify

The public website and managed DNS are working. Keep six7.work as the primary domain and www as its alternate. Check domain/certificate/project settings only if fresh evidence shows a problem. Preserve protections while ensuring legitimate crawlers are not challenged. Deployment acceptance comes from the live release marker, not from assuming a merge published.

### GoDaddy

Retain it as registrar. No record or nameserver change is indicated by this audit. The authoritative zone is on Netlify's DNS infrastructure; adding a TXT record to a non-authoritative GoDaddy zone would not verify this live domain. Never reset the zone or disturb mail/verification/unrelated records as an SEO fix.

### Search Console and Bing — next operational milestone

The account owner must verify a Google Search Console domain property for six7.work with the exact owner-specific DNS record Google issues, placed in the authoritative Netlify DNS zone. Do not invent a token. Then verify/import the site in Bing Webmaster Tools, submit https://six7.work/sitemap.xml, inspect / and /es/, and request indexing. A sitemap submission, HTTP 200 or schema validation does not prove indexing or guarantee rankings.

No Google Search Console or Bing account was accessed; no ownership verification, sitemap submission or indexing request has been performed by this change.

The existing README's initial-launch advice to avoid custom-domain/DNS setup is historical; this document governs the current rollout.

## Official references checked 2026-11-08

- Netlify domain assignment: https://docs.netlify.com/manage/domains/manage-domains/assign-a-domain-to-your-site-app/
- Netlify DNS: https://docs.netlify.com/manage/domains/set-up-netlify-dns/
- GoDaddy DNS management: https://www.godaddy.com/help/manage-dns-records-680
- Google ownership verification: https://support.google.com/webmasters/answer/9008080
- Google AI search guidance: https://developers.google.com/search/docs/appearance/ai-features

Google says its AI search features need no special AI text files or schema. Prioritize accessibility, indexability, useful visible content and accurate entity identity over unverified GEO claims.
