import sys, json, h5py, numpy as np, time
sys.path.insert(0,'.')
from cachedrange import CachedRange
fid, fname, size, ncell_sample = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
url=f"https://data.matr.io/1/api/v1/file/{fid}/download"
import urllib.request
real=urllib.request.urlopen(urllib.request.Request(url, headers={'Range':'bytes=0-0'})).geturl()
r=CachedRange(real, size)
t0=time.time()
f=h5py.File(r,'r')
batch=f['batch']
out={'file':fname,'batch_keys':list(batch.keys()),'top_keys':list(f.keys())}
n=batch['summary'].shape[0]; out['num_cells']=int(n)
cells=[]
for i in range(n):
    cyc=f[batch['cycles'][i,0]]
    summ=f[batch['summary'][i,0]]
    cl=f[batch['cycle_life'][i,0]][()]
    pol=f[batch['policy_readable'][i,0]][()].tobytes()[::2].decode()
    c={'i':i,'n_cycles':int(cyc['I'].shape[0]),'summary_len':int(summ['cycle'].shape[1]) if summ['cycle'].ndim==2 else int(summ['cycle'].shape[0]),
       'cycle_life':float(np.ravel(cl)[0]) if np.size(cl) else None,'policy':pol,'summary_fields':list(summ.keys()),'cycle_fields':list(cyc.keys())}
    cells.append(c)
out['cells']=cells
# sample per-cycle array lengths & filters
samp=[]
idx=np.linspace(0,n-1,ncell_sample).astype(int)
for i in idx:
    cyc=f[batch['cycles'][i,0]]; m=cyc['I'].shape[0]
    for j in sorted(set([0,1,m//2,m-1])):
        rec={'cell':int(i),'cycle':int(j)}
        for k in cyc.keys():
            d=f[cyc[k][j,0]]
            rec[k]=[int(x) for x in d.shape]; rec[k+'_dtype']=str(d.dtype)
        d=f[cyc['I'][j,0]]; rec['I_compression']=d.compression; rec['I_chunks']=d.chunks
        samp.append(rec)
out['samples']=samp
out['bytes_fetched']=r.fetched; out['requests']=r.requests; out['seconds']=round(time.time()-t0,1)
json.dump(out,open(f'probe_{fname}.json','w'),indent=1)
print(json.dumps({k:v for k,v in out.items() if k not in('cells','samples')}))
