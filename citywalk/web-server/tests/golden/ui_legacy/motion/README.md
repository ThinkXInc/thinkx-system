# Legacy local motion reproduction

`npm run capture:legacy-motion` drives the original business blueprint in
Chrome at the production-demo viewport (1490×856). It writes:

- `local_reproduction.webm`: owner-review recording.
- `motion_trace.json`: requestAnimationFrame samples of element geometry,
  opacity, transform, display state, map center, and map zoom.
- `<flow-id>/frame-NNNNN.png`: Chrome DevTools screencast frames captured only
  during that operation. `motion_trace.json` records each filename and browser
  timestamp; comparison never relies on unlisted stale files.

The automated sequence currently covers content selection, edit-panel close,
and map pan/zoom. Translation-panel population and selection remain pending;
the local translation service is not replaced with invented behavior.

The browser key is accepted only through `CITYWALK_GOOGLE_MAPS_API_KEY`. Its
value is neither written to these outputs nor included in diagnostics.

After capture, `npm run build:motion-review` places the canonical production
segment on the left and the matching local flow on the right. It produces one
file per automated flow: `review_content-selection.mp4`,
`review_edit-panel-close.mp4`, and `review_map-pan-zoom.mp4`. Map tile pixels
remain outside the acceptance decision; flow order, timing, trajectories, and
non-map UI are reviewed.

`npm run validate:motion-trace` rejects missing flows, non-monotonic sampling,
missing content-cell motion, an incomplete edit-panel close, or a map center and
zoom response that differs from the frozen contract.

`alignment.tsv` maps each local flow to the exact ground-truth S-segments,
comparison surface, and acceptance criteria. Its status remains pending until
the generated trace and video have passed automated and owner review.
