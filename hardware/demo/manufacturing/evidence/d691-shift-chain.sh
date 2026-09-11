#!/bin/bash
# D-691: move REF by (dx,dy), releasing whatever the chain demands -- stranded
# ends, bare pads, copper swept under a moved land, and barrels that end up
# inside one -- one object at a time until apply_part_shift PASSES.
B="$1"; REF="$2"; DX="$3"; DY="$4"; shift 4
NETS=(); for n in "$@"; do NETS+=(--release-net "$n"); done
EXTRA=()
for i in $(seq 1 200); do
  python3 apply_part_shift.py --board "$B" --ref "$REF" --dx-nm "$DX" --dy-nm "$DY" \
    --release "${NETS[@]}" "${EXTRA[@]}" --report /tmp/shift.json >/dev/null 2>&1
  read V N R < <(python3 -c "import json;d=json.load(open('/tmp/shift.json'));print(d['verdict'],d['released_count'],len(d['release_refusals']))")
  if [ "$V" = "PASS" ]; then echo "PASS after $i probes, released $N, extras ${#EXTRA[@]}"
    python3 apply_part_shift.py --board "$B" --ref "$REF" --dx-nm "$DX" --dy-nm "$DY" \
      --release "${NETS[@]}" "${EXTRA[@]}" --apply --report "w/d691/mv-$REF.json" >/dev/null 2>&1
    printf '%s\n' "${EXTRA[@]}" > "w/d691/args-$REF.txt"; echo APPLIED; exit 0; fi
  NEW=$(python3 -c "
import json;d=json.load(open('/tmp/shift.json'))
rs=[r for r in d['release_refusals'] if r['reason']=='RELEASE_WOULD_STRAND']
if rs:
    r=rs[0]
    if r.get('surviving_tracks',0)>0: print('P %s:%g,%g'%(r['net'],r['at_mm'][0],r['at_mm'][1]))
    elif r.get('pads'): print('B %s'%r['pads'][0])
    else: print('')
    raise SystemExit
sw=d.get('endpoints_swept_under_moved_land') or []
if sw: print('P %s:%g,%g'%(sw[0]['net'],sw[0]['at_mm'][0],sw[0]['at_mm'][1])); raise SystemExit
vp=d.get('vias_in_moved_pads') or []
if vp: print('V %s:%g,%g'%(vp[0]['net'],vp[0]['at_mm'][0],vp[0]['at_mm'][1])); raise SystemExit
st=d.get('endpoints_stranded') or []
if st: print('P %s:%g,%g'%(st[0][0],st[0][1],st[0][2])); raise SystemExit
print('')")
  case "$NEW" in
    P\ *) EXTRA+=(--release-point "${NEW#P }");;
    B\ *) EXTRA+=(--release-bare-pad "${NEW#B }");;
    V\ *) EXTRA+=(--release-via "${NEW#V }");;
    *) echo "STUCK at probe $i: verdict=$V released=$N refusals=$R"
       python3 -c "
import json;d=json.load(open('/tmp/shift.json'))
for k in ('release_refusals','endpoints_swept_under_moved_land','vias_in_moved_pads','endpoints_stranded'):
    v=d.get(k) or []
    if v: print(k,json.dumps(v)[:400])"; exit 1;;
  esac
done
echo "no convergence"; exit 1
