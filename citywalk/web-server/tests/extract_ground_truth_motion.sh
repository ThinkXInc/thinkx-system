#!/bin/sh
# thinkx-system/citywalk/web-server/tests/extract_ground_truth_motion.sh

set -eu

video_path="web-server/tests/golden/ui_legacy/ground_truth/createguideviewdemo.mov"
segments_path="web-server/tests/golden/ui_legacy/ground_truth/animation_segments.tsv"
output_root="web-server/tests/golden/ui_legacy/ground_truth/motion_reference"
tab_character=$(printf '\t')

exec 3< "$segments_path"
while IFS="$tab_character" read -r segment_id start_timestamp end_timestamp _start_frame _end_frame duration_seconds _animation _peak _mean fps <&3; do
    case "$segment_id" in
        \#*|'segment_id'|'') continue ;;
    esac

    segment_dir="$output_root/$segment_id"
    mkdir -p "$segment_dir"
    ffmpeg -hide_banner -loglevel error -nostdin -y \
        -ss "$start_timestamp" -t "$duration_seconds" -i "$video_path" \
        -vf "fps=$fps,scale=745:428:flags=lanczos" -vsync 0 -start_number 0 \
        "$segment_dir/frame-%05d.png"
done
