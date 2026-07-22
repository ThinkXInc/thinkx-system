# Legacy local motion reproduction

`npm run capture:legacy-motion` drives the original business blueprint in
Chrome at the production-demo viewport (1490×856). It writes:

- `local_reproduction.webm`: owner-review recording.
- `motion_trace.json`: requestAnimationFrame samples of element geometry,
  opacity, transform, display state, map center, and map zoom.

The automated sequence currently covers content selection, edit-panel close,
and map pan/zoom. Translation-panel population and selection remain pending;
the local translation service is not replaced with invented behavior.

The browser key is accepted only through `CITYWALK_GOOGLE_MAPS_API_KEY`. Its
value is neither written to these outputs nor included in diagnostics.
