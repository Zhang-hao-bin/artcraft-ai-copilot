# Project instructions

This repository publishes the reusable integration, not a full fork or an official ArtCraft release.

- CADCraft v0.7.0 at the pinned commit is the reference implementation. Do not claim other apps or platforms are integrated without tests.
- Never add credentials, account exports, chat transcripts, user drawings, machine configurations, build trees or binaries. Keep runtime outputs in ignored/private locations.
- Edit Rust changes in an isolated checkout of the pinned upstream. Follow that checkout's AGENTS.md, preserve unrelated work, and re-export the patch with new modules included. Never reset the user's original source.
- Keep stable document ownership, independent conversations and drafts, non-destructive new-chat behavior, cancellation guards and bounded persistence.
- Use public software APIs. Do not copy/link external GPL CAD kernels into the Rust application; FreeCAD stays a separate optional process.
- Run Python tests and actual patch/build checks when behavior changes. Keep docs/VALIDATION.md and validation-summary.json honest about what was run.
- Installation and publishing are separate from verification. Existing prefixes must not be overwritten without the intended update path. Never auto-install as part of a scheduled version check.
