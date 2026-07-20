<!-- thinkx-system/citywalk/web-server/tests/golden/ui_legacy/ground_truth/keyframes/README.md -->

# Ground-truth keyframes

Source: `../createguideviewdemo.mov` (H.264, 1490×856, 60/1 nominal fps,
8,083 frames, 134.983333 seconds).

`manifest.tsv` is the extraction ledger. Frames are selected by zero-based source
frame number with FFmpeg's `select=eq(n\,FRAME)` filter. Output PNGs retain the
source 1490×856 resolution and use `-vsync 0`; no scaling, masking, or color
post-processing is applied. The nominal timestamp is `frame_number / 60` and is
recorded for review navigation; frame number is the deterministic selector.

The selected frames cover stable states and the start/middle/end of the observed
spot, panel, map, menu, form, and translation flows. Google Maps tile pixels are
ground-truth evidence but are not a pixel-exact comparison surface in C-0c/C-6.
