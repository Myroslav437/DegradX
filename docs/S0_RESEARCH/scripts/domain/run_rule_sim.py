# Monte Carlo: false-detection rate of the rule "run of >= m consecutive residuals with r > k*scale (same sign)"
# under stationary Gaussian AR(1) noise with lag-1 autocorrelation phi; scale = 1.4826*MAD of the series.
import numpy as np
from scipy.stats import median_abs_deviation
from scipy.signal import savgol_filter
rng=np.random.default_rng(20260915)
def ar1(n,phi):
    e=rng.standard_normal(n)
    x=np.empty(n); x[0]=e[0]/np.sqrt(1-phi**2)
    for i in range(1,n): x[i]=phi*x[i-1]+e[i]
    return x*np.sqrt(1-phi**2)  # unit marginal variance
def runs(r,thr,m):
    cnt=0
    for sgn in (1,-1):
        above=(sgn*r)>thr
        run=0
        for a in above:
            if a: run+=1
            else:
                if run>=m: cnt+=1
                run=0
        if run>=m: cnt+=1
    return cnt
n=1000; reps=200
print("phi  k    m  false_runs_per_1000_positions (mean over %d series of length %d)"%(reps,n))
for phi in (0.0,0.3,0.6):
    for k in (2.0,2.5,3.0):
        for m in (1,2,3):
            tot=0
            for _ in range(reps):
                x=ar1(n,phi); s=median_abs_deviation(x,scale='normal')
                tot+=runs(x,k*s,m)
            print(f"{phi:.1f}  {k:.1f}  {m}  {tot/reps:.2f}")
# Attenuation of a regeneration-like pattern by SG smoothing (jump A=1 at t0, geometric decay ratio rho_d)
print("\nSG peak retention for jump+geometric decay pattern (peak of smoothed pattern / true peak)")
for decay in (0.5,0.7,0.85):
    p=np.zeros(200); t0=100
    for j in range(0,100): p[t0+j]=decay**j
    for W in (7,11,21):
        s=savgol_filter(p,W,2)
        print(f"decay={decay} W={W}: retention={s.max():.2f}")
