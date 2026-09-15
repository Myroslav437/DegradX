# Compute 3 dB cutoff (normalized to Nyquist, as in Schafer 2011) of centered SG smoothing filters
import numpy as np
from scipy.signal import savgol_coeffs, freqz
rows=[]
for W in [5,7,9,11,15,21,31,51]:
    for N in [1,2,3]:
        if N>=W: continue
        h=savgol_coeffs(W,N)
        w,H=freqz(h,worN=200000)
        mag=np.abs(H)
        idx=np.argmax(mag<10**(-3/20))
        fc=w[idx]/np.pi
        # attenuation of a pulse: response of SG to a unit step-then-geometric-decay (regeneration-like) is not computed here
        rows.append((W,N,fc,2/fc))
print("W  N  fc(norm. to Nyquist)  period_at_cutoff(cycles)")
for W,N,fc,p in rows: print(f"{W:2d} {N}  {fc:.3f}  {p:.1f}")
# Schafer Table 1 check: M=5,N=2 -> 0.197 ; M=6,N=2 -> 0.165
