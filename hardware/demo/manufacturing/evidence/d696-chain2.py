import json, subprocess, sys, os
B=sys.argv[1]; REF=sys.argv[2]; DX=sys.argv[3]; DY=sys.argv[4]
NETS=sys.argv[5].split("|")
ROT=sys.argv[6] if len(sys.argv)>6 else None
APPLY = os.environ.get("APPLY")=="1"
extra=[]; seen=set()
for i in range(400):
    cmd=["python3","apply_part_shift.py","--board",B,"--ref",REF,"--dx-nm",DX,"--dy-nm",DY,
         "--release","--allow-via-in-pad","--report","/tmp/chain.json"]
    if ROT: cmd += ["--rot-deg",ROT]
    for n in NETS: cmd += ["--release-net",n]
    cmd += extra
    subprocess.run(cmd,capture_output=True)
    d=json.load(open("/tmp/chain.json"))
    if d["verdict"]=="PASS":
        print("PASS after",i,"probes; released",d["released_count"],"extras",len(extra))
        print(" ".join(extra))
        json.dump(extra,open("/tmp/chain-extra.json","w"))
        if APPLY:
            subprocess.run(cmd+["--apply"],capture_output=True)
            print("APPLIED")
        sys.exit(0)
    nxt=None
    for r in d.get("release_refusals") or []:
        if r["reason"]=="RELEASE_WOULD_STRAND":
            if r.get("surviving_tracks",0)>0:
                t=("--release-point","%s:%g,%g"%(r["net"],r["at_mm"][0],r["at_mm"][1]))
            elif r.get("pads"):
                t=("--release-bare-pad",r["pads"][0])
            else: continue
            if t not in seen: nxt=t; break
        elif r["reason"]=="RELEASE_NET_NOT_DECLARED":
            print("NET NOT DECLARED:",r); sys.exit(2)
        else:
            print("OTHER REFUSAL:",r); sys.exit(3)
    if not nxt:
        print("STUCK at probe",i,"released",d["released_count"],"verdict",d["verdict"])
        for k in ("release_refusals","courtyard_overlaps_new","vias_in_moved_pads"):
            v=d.get(k)
            if v: print(" ",k,json.dumps(v)[:600])
        sys.exit(1)
    seen.add(nxt); extra += list(nxt)
print("no convergence")
