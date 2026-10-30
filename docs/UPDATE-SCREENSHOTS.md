# Publish the new 25-screen release

Upload the original `Six7-alpha-screens.zip` to the repository root, on `main`.
Do not extract it. Do not place the enclosing download folder in the repository.
The build also accepts the ZIP directly inside `mockup-sources/`.

The importer validates the exact supplied release and all 25 PNG checksums before replacing any active source. It publishes CRM 5, Kanban 6, Service Desk 9 and Contracts & Providers 5. The source images are never redrawn, resized or recompressed. The compact carousel CSS is unchanged.

Without the ZIP, the previous working carousel is kept and the build prints `SCREENSHOT UPDATE PENDING`. This must not be described as a completed screenshot deployment.

`/carousel-version.json` reports the screenshot release included in a build. `latest_screens_active` must be true, and the counts must be 5 / 6 / 9 / 5, before calling the update published. The separate GitHub Actions workflow checks public HTML and the C&P Home image; a source build passing is not proof of Netlify publication.

The registered C&P Home image is byte-for-byte the supplied `01-home(2).png`, including the purple document icon and Six7 wordmark. Its Git blob SHA is `d75e462d933700e86e639e84303b7071ce165b94`.

For a later release, validate its screenshot inventory and update `ui/gallery-latest.json` with its SHA-256 and image hashes before replacing the ZIP. Never place duplicate screenshot basenames at the top level of `mockup-sources/`.
