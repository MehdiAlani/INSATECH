import sys; sys.path.insert(0,".")
import gen_schematic as G
from sexp import head
def pinnames(lib):
    node=G.flat_symbol(lib); out={}
    def walk(n):
        if head(n)=="pin":
            num=name=None
            for ch in n[1:]:
                if head(ch)=="number": num=ch[1][1]
                elif head(ch)=="name": name=ch[1][1]
            if num: out[num]=name
        for ch in n[1:]:
            if isinstance(ch,list): walk(ch)
    walk(node); return out
for lib in ("Battery_Management:BQ76920PW","Battery_Management:BQ24610",
            "Interface_USB:STUSB4500QTR","Regulator_Switching:TPS61040DBV",
            "Connector:USB_C_Receptacle_PowerOnly_6P"):
    d=pinnames(lib)
    print("\n=== %s (%d)" % (lib,len(d)))
    print("  "+"  ".join("%s=%s" % (k,v) for k,v in sorted(d.items(), key=lambda kv:(len(kv[0]),kv[0]))))
