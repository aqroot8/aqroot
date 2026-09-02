#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "$0")/../../.." && pwd)
project_dir="$repo_dir/hardware/demo/kicad/aqroot-demo"
board="$project_dir/aqroot-Beta-v2.kicad_pcb"
schematic="$project_dir/aqroot-Beta-v2.kicad_sch"
output_dir=${1:-}

if [[ -z "$output_dir" ]]; then
  echo "usage: $0 OUTPUT_DIRECTORY" >&2
  exit 2
fi
if [[ -e "$output_dir" ]]; then
  echo "refusing to overwrite existing output: $output_dir" >&2
  exit 2
fi

mkdir -p "$output_dir/gerbers"

kicad-cli sch export bom \
  --fields 'Reference,Value,Footprint,Manufacturer,MPN,LCSC,QUANTITY,DNP' \
  --labels 'Refs,Value,Footprint,Manufacturer,MPN,LCSC,Qty,DNP' \
  --group-by 'Value,Footprint,Manufacturer,MPN,LCSC,DNP' \
  -o "$output_dir/aqroot-demo-bom-full.csv" "$schematic"

kicad-cli sch export bom --exclude-dnp \
  --fields 'Reference,Value,Footprint,Manufacturer,MPN,LCSC,QUANTITY' \
  --labels 'Refs,Value,Footprint,Manufacturer,MPN,LCSC,Qty' \
  --group-by 'Value,Footprint,Manufacturer,MPN,LCSC' \
  -o "$output_dir/aqroot-demo-bom-fitted.csv" "$schematic"

kicad-cli pcb export pos --format csv --units mm --side both --exclude-dnp \
  -o "$output_dir/aqroot-demo-cpl.csv" "$board"

kicad-cli pcb export gerbers --check-zones \
  -l 'F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts' \
  -o "$output_dir/gerbers" "$board"

kicad-cli pcb export drill --format excellon --excellon-units mm \
  --excellon-separate-th --generate-report \
  --report-path "$output_dir/gerbers/drill-report.txt" \
  -o "$output_dir/gerbers" "$board"

python3 "$repo_dir/hardware/demo/manufacturing/check_candidate.py" \
  "$output_dir" "$board"
