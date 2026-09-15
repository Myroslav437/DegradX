import scipy.io as sio, numpy as np, glob, os, json, collections, datetime
def dv(v):
    y,mo,dd,h,mi,s=v; return datetime.datetime(int(y),int(mo),int(dd),int(h),int(mi))+datetime.timedelta(seconds=float(s))
for fn in sorted(glob.glob('mat/*.mat')):
    name=os.path.basename(fn)[:-4]
    cyc=sio.loadmat(fn)[name]['cycle'][0,0][0]
    amb_by_type=collections.defaultdict(collections.Counter)
    cap_empty=0; cap_nan=0; lens=[]; imeds=collections.Counter(); starts=[]; tlens=[]; gaps=[]
    prev_end=None
    for c in cyc:
        t=str(c['type'][0]); amb_by_type[t][float(c['ambient_temperature'][0,0])]+=1
        d=c['data'][0,0]
        if t=='discharge':
            cap=d['Capacity']
            if cap.size==0: cap_empty+=1
            elif np.isnan(cap.ravel()[0]): cap_nan+=1
            I=d['Current_measured'].ravel(); V=d['Voltage_measured'].ravel(); T=d['Time'].ravel()
            lens.append(len(I))
            if len(I): imeds[round(float(np.median(I)),1)]+=1
            st=dv(c['time'][0])
            if prev_end is not None: gaps.append((st-prev_end).total_seconds()/3600)
            prev_end=st+datetime.timedelta(seconds=float(T[-1]) if len(T) else 0)
    gaps=np.array(gaps)
    print(json.dumps(dict(cell=name, amb_by_type={k:dict(v) for k,v in amb_by_type.items()}, cap_empty=cap_empty, cap_nan=cap_nan,
        dis_len_min=int(min(lens)), dis_len_median=int(np.median(lens)), dis_len_max=int(max(lens)), n_dis_len_lt_10=int(sum(l<10 for l in lens)),
        median_I_counts=dict(imeds), gap_h_median=round(float(np.median(gaps)),2), gap_h_max=round(float(gaps.max()),1), n_gaps_gt_24h=int((gaps>24).sum()))))
