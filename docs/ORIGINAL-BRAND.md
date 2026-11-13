# Six7 approved origami master

The approved dark wordmark is `dist/assets/six7-logo.png`, 1200 x 487.
SHA-256: `37e48955832e2dde50cb1fa67bdebf2ecaeb249a6d9beeb3b5545edd6f8a66cb`.
It matches the original supplied by Gaston on November 13, 2026.

The old flattened light-logo file is retired from publication. Every build
runs `scripts/original_brand.py` to derive its replacement from the approved
master pixels. The old tracked dist PNG is not the light-theme source of truth.

The transformation removes the dark backing and remaps only neutral tones to
graphite for light backgrounds. It does not retype, redraw or resample the
letters. Source fold shading, texture, the mesh and the x-to-7 connection are
retained; opaque orange pixels are checked for exact RGB equality. Edge
matting is adapted to the light background. The dark master remains untouched.

Both EN/ES headers and footers reference the generated light PNG with a
content-derived query suffix. The legacy public light-PNG path is regenerated,
and a content-addressed copy is also provided. `assets/six7-brand-quality.json`
records the hashes and automatic checks. Fonts, layout, copy, carousel, forms,
collaborator logos and favicon are outside this change.
