# thinkx-system/citywalk/web-server/tests/golden/ui_legacy/MASKS.md
#
# Screenshot mask and live Google Maps verification ledger for the legacy UI oracle.

Pixel comparison threshold: 0 differing bytes outside the declared masks.

Masked regions:

- `/business/createguide`: the visible map tile region from the right edge of `#leftwindow` to the viewport's right edge.
  The overlaid left panel is never masked. At mobile width the left panel covers the map, so no map mask is applied.

Each map-bearing route is required to pass these live checks before a screenshot is accepted:

- The container has non-zero rendered width and height and contains `.gm-style`.
- At least one loaded tile image or non-empty canvas exists.
- The center is readable and zoom changes by exactly one through the Maps API.
- Signup is separately navigated to `#page=1`; its map is hidden on the initial screenshot and therefore needs no mask.
- Expected custom pointer count is one on signup page 2 and zero on create-guide.
