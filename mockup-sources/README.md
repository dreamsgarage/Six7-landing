# Six7 image sources

## Active carousel screenshots

Keep screenshots in their application folders, not loose in this folder:

- `apps/crm/` — CRM
- `apps/kb/` — Kanban
- `apps/sd/` — Service Desk
- `apps/cp/` — Contracts & Providers

The carousel reads these files through `ui/gallery.json`. That file records the image order, English/Spanish captions, expected counts and source checksums. When replacing screenshots, commit the matching gallery manifest and images together. Identical filenames in different apps must remain in separate folders.

The old numbered PNGs directly under `mockup-sources/` were unused duplicates of the files in `apps/` and have been removed. Their removal does not replace or change the active screenshot set.

## Brand assets

The Claude and Omarchy SVGs and the Entangled Forge/Claude `.webp.b64` files in this folder are brand sources used by the build. Keep them. Do not delete the whole `mockup-sources/` folder.

Generated public image URLs live under `dist/assets/` and are produced by the build; edit the source files above instead.
