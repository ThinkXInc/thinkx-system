#!/bin/sh
# thinkx-system/citywalk/web-server/tests/extract_ground_truth_keyframes.sh

set -eu

video_path="web-server/tests/golden/ui_legacy/ground_truth/createguideviewdemo.mov"
manifest_path="web-server/tests/golden/ui_legacy/ground_truth/keyframes/manifest.tsv"
output_dir="web-server/tests/golden/ui_legacy/ground_truth/keyframes"

exec 3< "$manifest_path"
selection=""
sequence_number=1

while IFS="	" read -r output_name frame_number _timestamp _observation <&3; do
    case "$output_name" in
        \#*|'') continue ;;
    esac
    expected_name=$(printf 'frame-%04d.png' "$sequence_number")
    test "$output_name" = "$expected_name"
    sequence_number=$((sequence_number + 1))
    if test -n "$selection"; then
        selection="$selection+"
    fi
    selection="${selection}eq(n\\,${frame_number})"
done

ffmpeg -hide_banner -loglevel error -nostdin -y -i "$video_path" \
    -vf "select=${selection}" -vsync 0 -start_number 1 \
    "$output_dir/frame-%04d.png"
