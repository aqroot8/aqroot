timeout 3000 python3 hardware/demo/manufacturing/checks/contract_regression.py --baseline d718 --emit-baseline d719 \
  --claim placement:--move --claim placement:U12:3000000:-3800000 \
  --claim placement:--move --claim placement:L1:7500000:1000000:90 \
  --claim placement:--move --claim placement:C28:925000:8155000:270 \
  --claim placement:--move --claim placement:C31:49375000:-29455000:90 \
  --claim placement:--move --claim placement:C32:47085000:-30005000:90 \
  --claim placement:--move --claim placement:R39:900000:22150000:90 \
  --claim placement:--move --claim placement:R40:7900000:16450000:90 \
  --claim placement:--move --claim placement:R41:59685000:-17735000:180 \
  --claim placement:--move --claim placement:R43:52985000:-19435000:0 \
  --claim placement:--move --claim placement:TP6:4750000:-7500000 \
  --claim placement:--move --claim placement:TP8:37700000:-22800000 \
  $(for p in C28.2 C31.1 C31.2 C32.1 C32.2 L1.1 L1.2 R39.1 R39.2 R40.1 R40.2 R41.1 R41.2 R43.1 R43.2 TP6.1 TP8.1 U12.2 U12.3 U12.4 U12.5 U12.6 U12.7 U12.8 U12.9 U12.12 U12.13 U12.14 U12.15; do printf -- "--claim placement:--release --claim placement:%s " $p; done) \
  $(for r in U12 L1 C28 C31 C32 R39 R40 R41 R43 TP6 TP8; do printf -- "--claim pour_partition:--moved --claim pour_partition:%s " $r; done) \
  -o w/d719/d719-contract-regression.json
