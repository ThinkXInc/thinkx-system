#!/bin/sh
set -eu

root="web-server/tests/golden/ui_legacy"
ground_truth="$root/ground_truth/createguideviewdemo.mov"
test -f "$ground_truth"

build_review() {
  flow_id="$1"
  ground_truth_start="$2"
  ground_truth_duration="$3"
  local_fps="$4"
  local_frames="$root/motion/$flow_id/frame-%05d.png"
  output="$root/motion/review_$flow_id.mp4"

  test -f "$root/motion/$flow_id/frame-00000.png"
  ffmpeg -hide_banner -loglevel error -y \
    -ss "$ground_truth_start" \
    -t "$ground_truth_duration" \
    -i "$ground_truth" \
    -framerate "$local_fps" \
    -i "$local_frames" \
    -filter_complex \
    "[0:v]setpts=PTS-STARTPTS,scale=745:428:force_original_aspect_ratio=decrease,pad=745:428:(ow-iw)/2:(oh-ih)/2:black[left];[1:v]setpts=PTS-STARTPTS,scale=745:428:force_original_aspect_ratio=decrease,pad=745:428:(ow-iw)/2:(oh-ih)/2:black[right];[left][right]hstack=inputs=2:shortest=1[v]" \
    -map "[v]" \
    -an \
    -r 30 \
    -c:v libx264 \
    -crf 20 \
    -pix_fmt yuv420p \
    -movflags +faststart \
    "$output"
  printf '%s\n' "$output"
}

# Canonical first match from motion/alignment.tsv: S02, S04, and S10.
build_review content-selection 1.20 1.00 30
build_review edit-panel-close 5.60 1.60 60
build_review map-pan-zoom 32.55 2.20 20
