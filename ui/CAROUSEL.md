# Six7 real-app carousel — Option B

The existing `npm run build` now installs the real-app galleries before fingerprinting CSS and JavaScript. Netlify needs no additional dependencies or settings.

## Patch structure

- `scripts/carousel.py`: source-image validation, HTML rendering and image publishing.
- `ui/carousel.css`: scoped, responsive light/dark presentation.
- `ui/carousel.js`: app tabs, previous/next, thumbnail selection, scoped keyboard navigation, touch swipes and a full-size native dialog.
- `ui/gallery.json`: bilingual captions, app grouping and source-file checksums.
- `mockup-sources/apps/{crm,kb,sd,cp}/`: original screenshot PNGs, copied without alteration from the user's uploaded Git blobs.
- `scripts/finalize_build.py`: calls the gallery renderer before the existing hashed-asset and security-header steps.

All gallery images get content-hashed URLs under `/assets/apps/`. Missing or mismatched source images fail the build; there is no synthetic-screen or blank-panel fallback. All four galleries remain usable as image links without JavaScript. There is no autoplay. Screenshot pixels remain in their original English interface; labels, captions and controls are localized to EN/ES.

## Published source inventory

CRM: 5 screens. Kanban: 4 screens. Service Desk: 5 screens. Contracts & Providers: 5 screens. Total: 19 distinct PNGs in the 30 October GitHub upload.

The flat upload contained only one `05-reports.png` and one `03-new-request.png`, both belonging to Contracts & Providers. The Kanban report, Service Desk report and Service Desk new-request images from the original ZIPs were not included in the flat upload. They are not substituted with another app's image. Future additions belong in the relevant app folder and require a manifest entry with the source Git blob hash.

## QA

Chromium component tests cover EN/ES, light/dark, 320/375/768/1024/1440 px, all app tabs, previous/next wrapping, thumbnail navigation, modal zoom/close/focus return, scoped keyboard controls, a simulated touch swipe, and no-JavaScript fallback. Existing full-site link/form/metadata checks still run in GitHub Actions.

The form names, form actions, Story, biography, brand assets, PDFs and other sections are preserved.
