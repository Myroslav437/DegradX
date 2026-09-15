import scipy.io as sio, numpy as np, glob, os, json, collections
rows=[]
fieldsets=collections.defaultdict(set)
for fn in sorted(glob.glob('mat/*.mat')):
    name=os.path.basename(fn)[:-4]
    m=sio.loadmat(fn, simplify_cells=False)
    keys=[k for k in m if not k.startswith('__')]
    top=m[name]
    cyc=top['cycle'][0,0][0]
    types=collections.Counter(); amb=collections.Counter(); caps=[]; dtimes=[]; badfields=0
    first=None
    for c in cyc:
        t=str(c['type'][0]); types[t]+=1
        amb[float(c['ambient_temperature'][0,0])]+=1
        d=c['data'][0,0]
        fieldsets[t].add(tuple(d.dtype.names))
        tv=c['time'][0]
        dtimes.append(tv)
        if t=='discharge':
            cap=d['Capacity']
            caps.append(float(cap.ravel()[0]) if cap.size else np.nan)
    caps=np.array(caps)
    # time monotonicity of cycle start datevecs
    import datetime
    def dv(v):
        y,mo,dd,h,mi,s=v; return datetime.datetime(int(y),int(mo),int(dd),int(h),int(mi))+datetime.timedelta(seconds=float(s))
    ts=[dv(v) for v in dtimes]
    nonmono=sum(1 for a,b in zip(ts,ts[1:]) if b<a)
    rows.append(dict(cell=name, top_keys=keys, n_ops=len(cyc), types=dict(types), ambient=dict(amb),
        n_discharge=len(caps), cap_first=round(float(caps[0]),4) if len(caps) else None, cap_max=round(float(np.nanmax(caps)),4),
        cap_min=round(float(np.nanmin(caps)),4), cap_last=round(float(caps[-1]),4), n_cap_nan=int(np.isnan(caps).sum()),
        n_cap_lt_1=int((caps<1.0).sum()), n_cap_le_1p4=int((caps<=1.4).sum()), first_below_1p4=(int(np.argmax(caps<=1.4))+1 if (caps<=1.4).any() else None),
        first_below_1p6=(int(np.argmax(caps<=1.6))+1 if (caps<=1.6).any() else None),
        start=str(ts[0]), end=str(ts[-1]), nonmono_starts=nonmono))
for r in rows: print(json.dumps(r))
for t,s in fieldsets.items(): print(t, s)
