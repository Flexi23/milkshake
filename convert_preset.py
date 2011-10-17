import os,re,sys

dirname = sys.argv[1]
fnames = """
Flexi - Thread of Transience.milk""".split('\n')


eqn_subs = [(re.compile(pat),sub) for pat,sub in
            [(r'if ?\(', r'ifcond(')]]

def serialize_eqns(eqns,indent="    "):
    js = ""
    for eqn,lines in eqns.iteritems():
        js += "%s%s: function(_){with(_){\n" % (indent, eqn)
        lines = lines.items()
        lines.sort(key = lambda line: line[0])
        for lineno,expr in lines:
            js += "%s  %s\n" % (indent, expr)
        js += "%s}},\n" % indent
    return js

def serialize_subs(subs,subs_eqns,name):
    js = "    %s: [\n"%name
    subs = subs.items()
    subs.sort(key = lambda x: x[0])
    for subn,sub in subs:
        js += "      {\n"
        for key,val in sub:
            js += "       %s: %s,\n" % (key,val)
        js += serialize_eqns(subs_eqns.get(subn,{}), indent = "       ")
        js += "      },\n"
    js += "    ],\n"
    return js

def convert_eqn(eqn):
    if eqn.startswith("//"): return eqn
    for patt,repl in eqn_subs:
        eqn = patt.sub(repl,eqn)
    return eqn

js = "var Presets = {};\n\n"

for fname in fnames:
    if not fname.endswith(".milk"): continue

    contents = open(os.path.join(dirname,fname),"rb").read()
    if "\r\n" in contents:
        lines = contents.split("\r\n")
    else:
        lines = contents.split("\n")

    for i,line in enumerate(lines):
        if line.startswith("[preset"):
            lines = lines[i+1:]
            break

    preset = []
    equations = {}
    waves = {}
    wave_eqns = {}
    shapes = {}
    shape_eqns = {}

    def parse_sub_eqn(key,val,sub_eqns,sub):
        keysplit = key.split("_")
        subn = int(keysplit[1])
        subkey = '_'.join(keysplit[2:])
        eqns = sub_eqns.setdefault(subn,{})
        sub = sub_eqns.setdefault(subn,{})
        for type in ["init","per_frame","per_point"]:
            if subkey.startswith(type):
                lineno = int(subkey[len(type):])
                eqns.setdefault(type + "_code",{})[lineno] = convert_eqn(val);
            

    for line in lines:
        if not line: continue
        key,val = line.split("=",1)
        key = key.strip()
        val = val.strip()
        if key.startswith("per_frame_init_"):
            lineno = int(key.split("_")[-1])
            equations.setdefault('init_code', {})[lineno] = convert_eqn(val)
        elif key.startswith("per_frame_"):
            lineno = int(key.split("_")[-1])
            equations.setdefault('per_frame_code', {})[lineno] = convert_eqn(val)
        elif key.startswith("per_pixel_"):
            lineno = int(key.split("_")[-1])
            equations.setdefault('per_pixel_code', {})[lineno] = convert_eqn(val)
        elif key.startswith("wavecode_"):
            keysplit = key.split("_")
            subn = int(keysplit[1])
            subkey = '_'.join(keysplit[2:])
            sub = waves.setdefault(subn,[])
            sub.append((subkey,val))
        elif key.startswith("shapecode_"):
            keysplit = key.split("_")
            subn = int(keysplit[1])
            subkey = '_'.join(keysplit[2:])
            sub = shapes.setdefault(subn,[])
            sub.append((subkey,val))
        elif key.startswith("wave_") and key[5].isdigit():
            parse_sub_eqn(key,val,wave_eqns,waves)
        elif key.startswith("shape_"):
            parse_sub_eqn(key,val,shape_eqns,shapes)

        else:
            try:
                val = int(val)
            except ValueError:
                val = float(val)
            preset.append((key,val))

    js += "Presets[\"%s\"] = {\n" % fname
    for key,val in preset:
        js += "    %s: %s,\n" % (key, val)
    js += serialize_eqns(equations)
    js += serialize_subs(shapes,shape_eqns,"shapes")
    js += serialize_subs(waves,wave_eqns,"waves")

    js += "  };\n\n"

print js

