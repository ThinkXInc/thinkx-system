<!-- thinkx-system/citywalk/web-server/tests/golden/ui_legacy/ground_truth/REVIEW.md -->

# C-0c ground-truth review

Human-review inputs currently available:

- `createguideviewdemo.mov`: owner-provided 134.983333-second production demo
  (Git LFS).
- `keyframes/frame-0001.png` through `keyframes/frame-0039.png`: deterministic
  full-resolution review sequence.
- `keyframes/manifest.tsv`: source frame numbers, nominal timestamps, and the
  observation represented by each PNG.

Review sequence:

1. Confirm initial create-guide layout and the content-list/map split.
2. Confirm spot selection and placement responses on the map.
3. Confirm left edit-panel open/close motion and content edit-state changes.
4. Confirm map pan, zoom, and re-centering flow; tile pixels themselves may vary.
5. Confirm form select-menu open/close and text-entry responses.
6. Confirm translation panel slide-in, scrolling, selection, slide-out, and form
   update order.

The original business blueprint now runs in a real browser, and the layer-1
screenshot oracle is available under the parent `ui_legacy/` directory. The
required layer-2 local-reproduction sequence and layer-3 side-by-side output are
not yet available. C-0c remains unapprovable until those outputs are produced,
compared with this ground truth, and reviewed by the owner.

## Animation segments

The machine-readable source is `animation_segments.tsv`. Detection samples the
left UI at 20 fps and excludes the Google Maps tile region (`x=600..1489`). The
listed source frames use the video's nominal 60 fps timeline.

- 00:00.55–00:00.90 — initial create-guide transition (60 fps recommended)
- 00:01.20–00:02.20 — content-list/edit-state transition (30 fps)
- 00:03.05–00:05.35 — content selection and spot-placement response (60 fps)
- 00:05.60–00:07.20 — left edit-panel open/close (60 fps)
- 00:07.75–00:10.70 — repeated content/spot selection (30 fps)
- 00:12.05–00:13.45 — selected-content replacement (30 fps)
- 00:14.55–00:18.90 — edit-panel/content-state sequence (30 fps)
- 00:20.30–00:25.30 — spot/edit-panel sequence (30 fps)
- 00:27.05–00:31.70 — content replacement and panel transition (30 fps)
- 00:32.55–00:34.75 — map pan/zoom, tile pixels masked (20 fps)
- 00:36.90–00:40.05 — select-menu open/close (60 fps)
- 00:59.55–01:01.60 — content-to-map navigation (30 fps)
- 01:02.45–01:04.05 — edit-state replacement (60 fps)
- 01:05.40–01:07.45 — map pan/zoom/recenter, tile pixels masked (20 fps)
- 01:09.30–01:09.65 — dropdown opening (60 fps)
- 01:11.65–01:12.35 — dropdown closing/selection (60 fps)
- 01:17.45–01:21.95 — text-entry discrete events (20 fps; verify each
  character appearance as layer-1-like states, not continuous motion flow)
- 01:25.15–01:30.25 — text-entry/validation discrete events (20 fps; verify
  character appearance as layer-1-like states, not continuous motion flow)
- 01:32.80–01:39.70 — translation panel expansion/population (60 fps)
- 01:42.15–01:50.60 — translation list scroll/selection (30 fps)
- 01:58.70–01:59.50 — translation panel close/form reflection (60 fps)

Dense reference frames have been extracted under `motion_reference/<segment>/`
at the approved rates. `motion_reference/manifest.tsv` records exact counts,
resolution, and comparison masks.

For S19–S21 the translation panel occupies source `x=410..659`. That foreground
area is never masked; only the map tiles behind/right of it (`x=660..1489`) are
excluded during comparison. Re-evaluation changed peak/mean luma differences to
S19 `0.4179/0.0390`, S20 `0.3680/0.0524`, and S21 `1.6574/0.3117`. The observed
changes are short updates separated by held states, so the approved 60/30/60 fps
sampling remains appropriate.
