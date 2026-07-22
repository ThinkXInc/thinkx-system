#!/bin/sh
set -eu

root="web-server/tests/golden/ui_legacy"
ground_truth="$root/ground_truth/createguideviewdemo.mov"
local_reproduction="$root/motion/local_reproduction.webm"
output="$root/motion/ground_truth_vs_local.mp4"

test -f "$ground_truth"
test -f "$local_reproduction"

ffmpeg -hide_banner -loglevel error -y \
  -i "$ground_truth" \
  -i "$local_reproduction" \
  -filter_complex \
  "[0:v]scale=745:428:force_original_aspect_ratio=decrease,pad=745:428:(ow-iw)/2:(oh-ih)/2:black[left];[1:v]scale=745:428:force_original_aspect_ratio=decrease,pad=745:428:(ow-iw)/2:(oh-ih)/2:black[right];[left][right]hstack=inputs=2[v]" \
  -map "[v]" \
  -an \
  -r 30 \
  -c:v libx264 \
  -crf 20 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$output"

printf '%s\n' "$output"
