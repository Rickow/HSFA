"""Refait toute la rosette : API (3 passes de vote), soutien indépendant, champs, rapport. ~20-40 min."""
import json, collections, subprocess, sys
import rosette
from champs import collect, chain
r1 = rosette.all_chars(); C1, V1 = rosette.consensus(r1)
r2 = rosette.all_chars(C1); C2, _ = rosette.consensus(r2, share=0.6)
r3 = rosette.all_chars(C2); C3, V3 = rosette.consensus(r3, share=0.6)
json.dump({"%06x" % a: "%06x" % p for a, p in sorted(C3.items())}, open("api_arcade_psp.json", "w"), indent=0)
json.dump({"%06x" % ta: {("%06x" % k): n for k, n in v.items()} for ta, v in V1.items()}, open("votes_passe1.json", "w"), indent=0)
print("API : %d paires (passe 1 : %d)" % (len(C3), len(C1)))
votes, n = collect(); ch = chain(votes)
json.dump({"votes": {"%x" % o: {"%x" % p: k for p, k in v.items()} for o, v in votes.items()},
           "chaine": [[o, p, k] for o, p, k in ch]}, open("champs_votes.json", "w"))
print("champs : %d paires de routines, %d champs dans la chaîne" % (n, len(ch)))
open("tableau_api.md", "w").write(subprocess.run([sys.executable, "rapport.py"], capture_output=True, text=True).stdout)
