"""
CP + LP Unified Analysis v3
============================
CP: Metal-plate normalization (same as LP baseline)
LP: M3 unfolded calibration (corrected M3) + metal-plate for cross-check

Both methods compared to Fresnel slab theory.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

plt.rcParams.update({'font.size': 10, 'axes.titlesize': 11, 'figure.dpi': 150})

STAGE_ROOT = Path(__file__).resolve().parents[1]
UPLOAD = STAGE_ROOT / "csv"
OUTPUT = STAGE_ROOT / "results"
OUTPUT.mkdir(exist_ok=True)

# Material properties (HFSS confirmed)
MAT_PROPS = {
    'metal':    {'eps_r': 1e6,  'tan_d': 0.0,   'label': 'Metal (PEC)'},
    'concrete': {'eps_r': 5.24, 'tan_d': 0.105, 'label': 'Concrete'},
    'glass':    {'eps_r': 6.31, 'tan_d': 0.019, 'label': 'Glass'},
    'wood':     {'eps_r': 1.99, 'tan_d': 0.049, 'label': 'Wood'},
}
WALL_T_MM = 100.0
MATS = ['metal', 'concrete', 'glass', 'wood']
MATS3 = ['concrete', 'glass', 'wood']
COL = {'metal': '#1e293b', 'concrete': '#dc2626', 'glass': '#2563eb', 'wood': '#059669'}
MRK = {'metal': 'D', 'concrete': 'o', 'glass': 's', 'wood': '^'}


# ================================================================
# FRESNEL
# ================================================================

def fresnel_slab(er, td, theta_deg, t_mm, f_ghz):
    th = np.deg2rad(np.asarray(theta_deg, dtype=float))
    ec = er * (1 - 1j * td)
    k0 = 2*np.pi*f_ghz/300.0
    ct, st = np.cos(th), np.sin(th)
    sq = np.sqrt(ec - st**2 + 0j)
    rte = (ct - sq)/(ct + sq)
    rtm = (ec*ct - sq)/(ec*ct + sq)
    if t_mm is None or t_mm <= 0:
        return rte, rtm
    d = k0 * t_mm * sq
    e2 = np.exp(-2j*d)
    RTE = rte*(1-e2)/(1-rte**2*e2)
    RTM = rtm*(1-e2)/(1-rtm**2*e2)
    return RTE, RTM


# ================================================================
# DATA LOADING
# ================================================================

def pc(mag, ph): return mag * np.exp(1j * np.deg2rad(ph))

def load_m1(path, chs):
    df = pd.read_csv(path); c = df.columns
    out = {'freq': df.iloc[:,0].values}
    for i, ch in enumerate(chs):
        out[ch] = pc(df.iloc[:,1+2*i].values, df.iloc[:,2+2*i].values)
    return out

def load_sw(path, chs):
    df = pd.read_csv(path); c = df.columns
    ts = np.array(sorted(df.iloc[:,0].unique()))
    f = df[df.iloc[:,0]==ts[0]].iloc[:,1].values
    out = {'freq': f, 'thetas': ts}
    for t in ts:
        s = df[df.iloc[:,0]==t]
        d = {}
        for i, ch in enumerate(chs):
            d[ch] = pc(s.iloc[:,2+2*i].values, s.iloc[:,3+2*i].values)
        out[t] = d
    return out

print("="*65)
print("  CP + LP Unified Analysis v3")
print("  CP: metal-plate | LP: M3 unfolded + metal-plate")
print("="*65)

CP_CH = ['LL','LR','RL','RR']
LP_CH = ['yy','yz','zy','zz']  # column order in CSV

cp_m1 = load_m1(UPLOAD/"m1_los_5000.csv", CP_CH)
cp_m3 = load_sw(UPLOAD/"m3_off-boresigjt.csv", CP_CH)
cp_m2 = {m: load_sw(UPLOAD/f"m2_{m}_R_5000.csv", CP_CH) for m in MATS}

lp_m1 = load_m1(UPLOAD/"LP_m1_los_5000.csv", LP_CH)
lp_m3 = load_sw(UPLOAD/"LP_m3_off-boresigjt.csv", LP_CH)
lp_m2 = {m: load_sw(UPLOAD/f"LP_m2_{m}_R_5000.csv", LP_CH) for m in MATS}

freq = cp_m1['freq']
thetas_cp = cp_m3['thetas']      # 14 values incl. 56
thetas_lp_m3 = lp_m3['thetas']   # 13 values, no 56
# Use common thetas for comparison
thetas_common = np.array(sorted(set(thetas_cp) & set(thetas_lp_m3)))
thetas_all = thetas_cp  # for CP-only plots
Nf = len(freq)
f_ctr = freq[Nf//2]

print(f"  Freq: {freq[0]:.3f}–{freq[-1]:.3f} GHz ({Nf} pts)")
print(f"  CP θ: {thetas_cp.tolist()}")
print(f"  LP M3 θ: {thetas_lp_m3.tolist()}")
print(f"  Common θ: {thetas_common.tolist()}")


# ================================================================
# CP CALIBRATION: METAL-PLATE NORMALIZATION
# ================================================================

print("\n[1] CP: Metal-plate normalization...")

# LoS subtraction
cp_ht = {m: {} for m in MATS}
for m in MATS:
    for t in thetas_all:
        cp_ht[m][t] = {ch: cp_m2[m][t][ch] - cp_m1[ch] for ch in CP_CH}

# CP metal-plate: Γ(mat) = h̃(mat) / h̃(metal)
# For CP: cross channel (LR) carries main reflection (RHCP→LHCP)
#         co channel (RR) carries depolarization residual
cp_g = {}
for m in MATS:
    cp_g[m] = {}
    for t in thetas_all:
        ht_m = cp_ht[m][t]
        ht_met = cp_ht['metal'][t]
        
        # Cross: Γ_X via reciprocity estimator normalized to metal
        # h̃_LR(mat)/h̃_LR(metal) ≈ Γ_LR(mat)/Γ_LR(metal)
        # For PEC single bounce: |Γ_LR(PEC)| ≈ 1 → magnitude directly usable
        Gx_LR = ht_m['LR'] / ht_met['LR']
        Gx_RL = ht_m['RL'] / ht_met['RL']
        # Reciprocity geometric mean
        ratio_x = Gx_LR * Gx_RL
        Gx = np.sqrt(np.abs(ratio_x)) * np.exp(1j*np.angle(ratio_x)/2)
        
        # Co: Γ_C = h̃_RR(mat) / h̃_RR(metal)
        Gc = ht_m['RR'] / ht_met['RR']
        
        # Also single-channel for comparison
        Gx_single_LR = ht_m['LR'] / ht_met['LR']
        Gx_single_RL = ht_m['RL'] / ht_met['RL']
        
        # PEC reference: Γ_LR(PEC) = (R_TE+R_TM)/2 = (-1+1)/2 = 0 ... WAIT
        # Actually for PEC: R_TE = -1, R_TM = +1
        # Γ_LR = (R_TE + R_TM)/2 = 0 ← this is WRONG for metal-plate cal!
        
        # Let me reconsider. In CP reflection from PEC:
        # The handedness reverses: RHCP → LHCP
        # So |Γ_LR(PEC)| should be ~1, not 0
        # The issue is the sign convention for R_TM at PEC
        
        # In practice, from the CP simulation, metal h̃_LR is large (|Γ_X|≈1)
        # So the ratio h̃_LR(mat)/h̃_LR(metal) gives Γ_X(mat)/Γ_X(metal)
        # And since |Γ_X(metal)|≈1 from simulation, this ≈ Γ_X(mat)
        
        # For TE/TM derivation we need actual R_TE, R_TM
        # From metal-normalized CP: we get Γ_X(mat)/Γ_X(metal) and Γ_C(mat)/Γ_C(metal)
        # This is NOT directly R_TE or R_TM — it's normalized CP quantities
        
        # Store as-is; TE/TM will be derived differently
        cp_g[m][t] = {
            'Gx': Gx, 'Gc': Gc,
            'Gx_LR': Gx_single_LR, 'Gx_RL': Gx_single_RL,
        }

# For TE/TM from CP metal-plate:
# Γ_X(mat) = Gx * Γ_X(metal_sim)
# Γ_C(mat) = Gc * Γ_C(metal_sim)
# But we need Γ_X(metal_sim) and Γ_C(metal_sim) from CP M3 calibration
# OR: use the fact that for PEC, |Γ_X|≈1 (from sim) → Gx ≈ Γ_X(mat)
# This is the "metal as |Γ|=1 ref" assumption
# For co: Γ_C(metal) is NOT 0 in sim (antenna leakage) → Gc ratio is NOT pure Γ_C(mat)

# Better approach: use CP M3 calibration for Γ_X (robust), metal-plate for Γ_C comparison
# Actually, let's also run CP M3 calibration for full comparison

print("  Also running CP M3-unfolded calibration for comparison...")
cp_g_m3 = {}
for m in MATS:
    cp_g_m3[m] = {}
    for t in thetas_all:
        h2 = cp_m2[m][t]; h3 = cp_m3[t]
        ht = {ch: h2[ch] - cp_m1[ch] for ch in CP_CH}
        ratio = (ht['LR']*ht['RL'])/(h3['RR']*h3['LL'])
        Gx = np.sqrt(np.abs(ratio))*np.exp(1j*np.angle(ratio)/2)
        eps = h3['LR']/h3['RR']
        Gc_raw = ht['RR']/h3['RR']
        Gc_cor = Gc_raw - eps*Gx
        cp_g_m3[m][t] = {'Gx': Gx, 'Gc_cor': Gc_cor, 'Gc_raw': Gc_raw}

print("  Done.")


# ================================================================
# LP CALIBRATION: M3 UNFOLDED + METAL-PLATE
# ================================================================

print("\n[2] LP: M3 unfolded + metal-plate calibration...")

lp_ht = {m: {} for m in MATS}
for m in MATS:
    for t in thetas_all:
        lp_ht[m][t] = {ch: lp_m2[m][t][ch] - lp_m1[ch] for ch in LP_CH}

lp_g = {}
for m in MATS:
    lp_g[m] = {}
    for t in thetas_common:
        ht = lp_ht[m][t]
        h3 = lp_m3[t]
        ht_met = lp_ht['metal'][t]
        
        # M3 unfolded calibration (direct ratio — LP's main advantage)
        R_TE_m3 = ht['zz'] / h3['zz']
        R_TM_m3 = ht['yy'] / h3['yy']
        
        # Metal-plate calibration
        R_TE_met = ht['zz'] / ht_met['zz']
        R_TM_met = ht['yy'] / ht_met['yy']
        
        lp_g[m][t] = {
            'R_TE_m3': R_TE_m3, 'R_TM_m3': R_TM_m3,
            'R_TE_met': R_TE_met, 'R_TM_met': R_TM_met,
        }

print("  Done.")


# ================================================================
# FRESNEL THEORY
# ================================================================

print("\n[3] Fresnel slab theory...")
th_fine = np.linspace(0.5, 89.5, 500)
theory = {}
for m in MATS3:
    p = MAT_PROPS[m]
    rte, rtm = fresnel_slab(p['eps_r'], p['tan_d'], th_fine, WALL_T_MM, f_ctr)
    theory[m] = {'R_TE': rte, 'R_TM': rtm, 'theta': th_fine,
                 'Brewster': np.rad2deg(np.arctan(np.sqrt(p['eps_r'])))}
    print(f"  {m}: Brewster={theory[m]['Brewster']:.1f}°")


# ================================================================
# FIGURE 1: LP M3 vs LP Metal-plate — 두 calibration 비교
# ================================================================

print("\n[4] Generating figures...")

fig1, axes = plt.subplots(2, 3, figsize=(17, 10))
fig1.suptitle("LP Calibration Comparison: M3-Unfolded vs Metal-Plate vs Fresnel", fontweight='bold')

for idx, m in enumerate(MATS3):
    p = MAT_PROPS[m]; t_th = theory[m]
    
    for row, (rn, key_m3, key_met, color) in enumerate([
        ('R_TE', 'R_TE_m3', 'R_TE_met', '#2563eb'),
        ('R_TM', 'R_TM_m3', 'R_TM_met', '#dc2626')
    ]):
        ax = axes[row, idx]
        # Fresnel
        r_th = np.abs(t_th['R_TE'] if rn=='R_TE' else t_th['R_TM'])
        ax.plot(th_fine, r_th, '-', color='gray', lw=2, alpha=0.5, label='Fresnel slab')
        
        # LP M3
        vals_m3 = [np.mean(np.abs(lp_g[m][t][key_m3])) for t in thetas_common]
        ax.plot(thetas_common, vals_m3, 'o-', color=color, markersize=6, lw=1.5, label='LP M3-unfolded')
        
        # LP metal-plate
        vals_met = [np.mean(np.abs(lp_g[m][t][key_met])) for t in thetas_common]
        ax.plot(thetas_common, vals_met, 'x--', color=color, markersize=7, lw=1, alpha=0.7, label='LP metal-plate')
        
        ax.axvline(t_th['Brewster'], color='gray', ls=':', lw=0.5)
        ax.set_ylabel(f'|{rn}|')
        ax.set_title(f"{p['label']} — {rn}")
        ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
        ax.set_xlim([5, 80])
        if row == 1: ax.set_xlabel(r'$\theta_i$ [deg]')

fig1.tight_layout()
fig1.savefig(OUTPUT/"v3_fig1_LP_cal_comparison.png", dpi=150, bbox_inches='tight')
print("  [1/5] v3_fig1_LP_cal_comparison.png")


# ================================================================
# FIGURE 2: CP metal-plate vs CP M3 — 두 calibration 비교
# ================================================================

fig2, axes = plt.subplots(2, 3, figsize=(17, 10))
fig2.suptitle("CP Calibration Comparison: Metal-Plate vs M3-Unfolded", fontweight='bold')

for idx, m in enumerate(MATS3):
    # Cross
    ax = axes[0, idx]
    gx_met = [np.mean(np.abs(cp_g[m][t]['Gx'])) for t in thetas_all]
    gx_m3 = [np.mean(np.abs(cp_g_m3[m][t]['Gx'])) for t in thetas_all]
    ax.plot(thetas_all, gx_met, 'o-', color='#7c3aed', markersize=5, label='CP metal-plate')
    ax.plot(thetas_all, gx_m3, 's--', color='#2563eb', markersize=5, alpha=0.7, label='CP M3-unfolded')
    ax.set_ylabel(r'$|\hat{\Gamma}_X|$')
    ax.set_title(f"{MAT_PROPS[m]['label']} — Cross")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    
    # Co
    ax = axes[1, idx]
    gc_met = [np.mean(np.abs(cp_g[m][t]['Gc'])) for t in thetas_all]
    gc_m3 = [np.mean(np.abs(cp_g_m3[m][t]['Gc_cor'])) for t in thetas_all]
    ax.plot(thetas_all, gc_met, 'o-', color='#7c3aed', markersize=5, label='CP metal-plate co')
    ax.plot(thetas_all, gc_m3, 's--', color='#2563eb', markersize=5, alpha=0.7, label='CP M3-corrected co')
    ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|\hat{\Gamma}_C|$')
    ax.set_title(f"{MAT_PROPS[m]['label']} — Co")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

fig2.tight_layout()
fig2.savefig(OUTPUT/"v3_fig2_CP_cal_comparison.png", dpi=150, bbox_inches='tight')
print("  [2/5] v3_fig2_CP_cal_comparison.png")


# ================================================================
# FIGURE 3: TRIPLE COMPARISON — LP(M3) vs CP(metal) vs Fresnel
# ================================================================

fig3, axes = plt.subplots(2, 3, figsize=(17, 10))
fig3.suptitle("R$_{TE}$, R$_{TM}$: LP-M3 vs CP-Metal vs Fresnel Slab", fontweight='bold')

for idx, m in enumerate(MATS3):
    t_th = theory[m]
    
    for row, rn in enumerate(['R_TE', 'R_TM']):
        ax = axes[row, idx]
        # Fresnel
        r_f = np.abs(t_th[rn])
        ax.plot(th_fine, r_f, '-', color='gray', lw=2, alpha=0.5, label='Fresnel slab')
        
        # LP M3 — direct R_TE/R_TM
        lp_vals = [np.mean(np.abs(lp_g[m][t][f'{rn}_m3'])) for t in thetas_common]
        ax.plot(thetas_common, lp_vals, 'o-', color='#2563eb', markersize=6, lw=1.5, label='LP M3-direct')
        
        # CP metal-plate — derive R_TE/R_TM from Γ_X, Γ_C
        # R_TE = Γ_X + Γ_C (but these are metal-normalized, need absolute values)
        # Metal-normalized Γ_X ≈ Γ_X(mat)/Γ_X(PEC)
        # For PEC simulation: Γ_X ≈ 1 → metal-normalized ≈ absolute
        # For co: Γ_C(PEC) ≠ 0 in sim → metal-normalized Γ_C(mat)/Γ_C(PEC) ≠ Γ_C(mat)
        # So we use CP M3-corrected for TE/TM derivation instead
        cp_rte = [np.mean(np.abs(cp_g_m3[m][t]['Gx'] + cp_g_m3[m][t]['Gc_cor'])) for t in thetas_all]
        cp_rtm = [np.mean(np.abs(cp_g_m3[m][t]['Gx'] - cp_g_m3[m][t]['Gc_cor'])) for t in thetas_all]
        vals_cp = cp_rte if rn == 'R_TE' else cp_rtm
        ax.plot(thetas_all, vals_cp, 's--', color='#7c3aed', markersize=5, alpha=0.7, label='CP M3-derived')
        
        ax.axvline(t_th['Brewster'], color='gray', ls=':', lw=0.5)
        ax.set_ylabel(f'|{rn}|')
        ax.set_title(f"{MAT_PROPS[m]['label']} — {rn}")
        ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
        ax.set_xlim([5, 80])
        if row == 1: ax.set_xlabel(r'$\theta_i$ [deg]')

fig3.tight_layout()
fig3.savefig(OUTPUT/"v3_fig3_triple_comparison.png", dpi=150, bbox_inches='tight')
print("  [3/5] v3_fig3_triple_comparison.png")


# ================================================================
# FIGURE 4: CALIBRATION ACCURACY — LP & CP deviation
# ================================================================

fig4, axes = plt.subplots(2, 3, figsize=(17, 10))
fig4.suptitle("Calibration Accuracy [dB]: Deviation from Fresnel Slab Theory", fontweight='bold')

for idx, m in enumerate(MATS3):
    p = MAT_PROPS[m]
    for row, rn in enumerate(['R_TE', 'R_TM']):
        ax = axes[row, idx]
        
        # LP M3
        dev_lp = []
        for t in thetas_common:
            rf, _ = fresnel_slab(p['eps_r'], p['tan_d'], t, WALL_T_MM, freq)
            th_val = np.mean(np.abs(rf)) if rn=='R_TE' else np.mean(np.abs(_))
            # Recalculate properly
            rte_f, rtm_f = fresnel_slab(p['eps_r'], p['tan_d'], t, WALL_T_MM, freq)
            th_val = np.mean(np.abs(rte_f if rn=='R_TE' else rtm_f))
            lp_val = np.mean(np.abs(lp_g[m][t][f'{rn}_m3']))
            dev_lp.append(20*np.log10(lp_val/th_val) if th_val>1e-6 else np.nan)
        
        # LP metal-plate
        dev_lp_met = []
        for t in thetas_common:
            rte_f, rtm_f = fresnel_slab(p['eps_r'], p['tan_d'], t, WALL_T_MM, freq)
            th_val = np.mean(np.abs(rte_f if rn=='R_TE' else rtm_f))
            lp_val = np.mean(np.abs(lp_g[m][t][f'{rn}_met']))
            dev_lp_met.append(20*np.log10(lp_val/th_val) if th_val>1e-6 else np.nan)
        
        # CP M3
        dev_cp = []
        for t in thetas_all:
            rte_f, rtm_f = fresnel_slab(p['eps_r'], p['tan_d'], t, WALL_T_MM, freq)
            th_val = np.mean(np.abs(rte_f if rn=='R_TE' else rtm_f))
            gx = cp_g_m3[m][t]['Gx']; gc = cp_g_m3[m][t]['Gc_cor']
            cp_val = np.mean(np.abs(gx + gc)) if rn=='R_TE' else np.mean(np.abs(gx - gc))
            dev_cp.append(20*np.log10(cp_val/th_val) if th_val>1e-6 else np.nan)
        
        ax.plot(thetas_common, dev_lp, 'o-', color='#2563eb', markersize=5, label='LP M3-unfolded')
        ax.plot(thetas_common, dev_lp_met, 'x--', color='#059669', markersize=6, label='LP metal-plate')
        ax.plot(thetas_all, dev_cp, 's--', color='#7c3aed', markersize=4, alpha=0.7, label='CP M3-derived')
        ax.axhline(0, color='black', ls='-', lw=0.5)
        ax.fill_between([5,80], -3, 3, alpha=0.06, color='green')
        ax.set_ylabel(f'{rn} Δ [dB]')
        ax.set_title(f"{p['label']} — {rn}")
        ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
        ax.set_xlim([5, 80]); ax.set_ylim([-20, 20])
        if row == 1: ax.set_xlabel(r'$\theta_i$ [deg]')

fig4.tight_layout()
fig4.savefig(OUTPUT/"v3_fig4_accuracy.png", dpi=150, bbox_inches='tight')
print("  [4/5] v3_fig4_accuracy.png")


# ================================================================
# FIGURE 5: SUPPRESSION GAIN + COMPREHENSIVE SUMMARY
# ================================================================

fig5, axes = plt.subplots(2, 3, figsize=(17, 10))
fig5.suptitle("CP-UWB Multipath Suppression: Comprehensive Summary\n"
              f"(d=5m, f={freq[0]:.2f}–{freq[-1]:.2f} GHz, Wall={WALL_T_MM:.0f}mm slab)",
              fontweight='bold', fontsize=13)

# (a) CP Γ_X (metal-plate normalized) 
ax = axes[0, 0]
for m in MATS:
    v = [np.mean(np.abs(cp_g[m][t]['Gx'])) for t in thetas_all]
    ax.plot(thetas_all, v, f'{MRK[m]}-', color=COL[m], label=MAT_PROPS[m]['label'], markersize=5)
ax.set_ylabel(r'$|\hat{\Gamma}_X|$ (metal-norm)'); ax.set_title(r'(a) CP Cross $\hat{\Gamma}_X$')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (b) CP Γ_C (metal-plate normalized)
ax = axes[0, 1]
for m in MATS:
    v = [np.mean(np.abs(cp_g[m][t]['Gc'])) for t in thetas_all]
    ax.plot(thetas_all, v, f'{MRK[m]}-', color=COL[m], label=MAT_PROPS[m]['label'], markersize=5)
ax.set_ylabel(r'$|\hat{\Gamma}_C|$ (metal-norm)'); ax.set_title(r'(b) CP Co $\hat{\Gamma}_C$')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (c) CP XPD (metal-plate)
ax = axes[0, 2]
for m in MATS:
    xpd = [20*np.log10(np.mean(np.abs(cp_g[m][t]['Gx'])) /
            max(np.mean(np.abs(cp_g[m][t]['Gc'])), 1e-10)) for t in thetas_all]
    ax.plot(thetas_all, xpd, f'{MRK[m]}-', color=COL[m], label=MAT_PROPS[m]['label'], markersize=5)
ax.axhline(0, color='gray', ls=':', lw=1)
ax.set_ylabel('XPD [dB]'); ax.set_title('(c) CP Reflected XPD')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (d) LP R_TE vs Fresnel
ax = axes[1, 0]
for m in MATS3:
    t_th = theory[m]
    ax.plot(th_fine, np.abs(t_th['R_TE']), '-', color=COL[m], lw=1, alpha=0.3)
    v = [np.mean(np.abs(lp_g[m][t]['R_TE_m3'])) for t in thetas_common]
    ax.plot(thetas_common, v, f'{MRK[m]}-', color=COL[m], label=MAT_PROPS[m]['label'], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|R_{TE}|$')
ax.set_title(r'(d) LP $R_{TE}$ (M3) vs Fresnel'); ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (e) LP R_TM vs Fresnel
ax = axes[1, 1]
for m in MATS3:
    t_th = theory[m]
    ax.plot(th_fine, np.abs(t_th['R_TM']), '-', color=COL[m], lw=1, alpha=0.3)
    v = [np.mean(np.abs(lp_g[m][t]['R_TM_m3'])) for t in thetas_common]
    ax.plot(thetas_common, v, f'{MRK[m]}-', color=COL[m], label=MAT_PROPS[m]['label'], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|R_{TM}|$')
ax.set_title(r'(e) LP $R_{TM}$ (M3) vs Fresnel'); ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (f) Suppression gain: max(LP R_TE, R_TM) / CP Γ_C (M3-corrected)
ax = axes[1, 2]
for m in MATS3:
    gains = []
    for t in thetas_common:
        rte = np.mean(np.abs(lp_g[m][t]['R_TE_m3']))
        rtm = np.mean(np.abs(lp_g[m][t]['R_TM_m3']))
        lp_w = max(rte, rtm)
        # Use CP M3-corrected Γ_C for most accurate co-pol
        gc = np.mean(np.abs(cp_g_m3[m][t]['Gc_cor']))
        gains.append(20*np.log10(lp_w / max(gc, 1e-6)))
    ax.plot(thetas_common, gains, f'{MRK[m]}-', color=COL[m], label=MAT_PROPS[m]['label'], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('Gain [dB]')
ax.set_title(r'(f) CP Suppression: $\max(R_{TE}^{LP}, R_{TM}^{LP}) / |\Gamma_C^{CP}|$')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

fig5.tight_layout()
fig5.savefig(OUTPUT/"v3_fig5_summary.png", dpi=150, bbox_inches='tight')
print("  [5/5] v3_fig5_summary.png")


# ================================================================
# NUMERICAL TABLES
# ================================================================

print("\n" + "="*65)
print("  CALIBRATION ACCURACY: LP M3-unfolded vs LP Metal-plate vs Fresnel")
print("="*65)

for m in MATS3:
    p = MAT_PROPS[m]
    print(f"\n  ━━━ {p['label']} ━━━")
    print(f"  {'θ_i':>5s} | {'|R_TE|_th':>8s} {'LP_M3':>8s} {'Δ_M3':>6s} {'LP_met':>8s} {'Δ_met':>6s}"
          f" | {'|R_TM|_th':>8s} {'LP_M3':>8s} {'Δ_M3':>6s} {'LP_met':>8s} {'Δ_met':>6s}")
    print("  " + "-" * 100)
    for t in thetas_common:
        rte_f, rtm_f = fresnel_slab(p['eps_r'], p['tan_d'], t, WALL_T_MM, freq)
        rte_th = np.mean(np.abs(rte_f)); rtm_th = np.mean(np.abs(rtm_f))
        
        rte_m3 = np.mean(np.abs(lp_g[m][t]['R_TE_m3']))
        rtm_m3 = np.mean(np.abs(lp_g[m][t]['R_TM_m3']))
        rte_met = np.mean(np.abs(lp_g[m][t]['R_TE_met']))
        rtm_met = np.mean(np.abs(lp_g[m][t]['R_TM_met']))
        
        d1 = 20*np.log10(rte_m3/rte_th) if rte_th>1e-6 else np.nan
        d2 = 20*np.log10(rte_met/rte_th) if rte_th>1e-6 else np.nan
        d3 = 20*np.log10(rtm_m3/rtm_th) if rtm_th>1e-6 else np.nan
        d4 = 20*np.log10(rtm_met/rtm_th) if rtm_th>1e-6 else np.nan
        
        print(f"  {t:5.0f}° | {rte_th:8.4f} {rte_m3:8.4f} {d1:+5.1f}  {rte_met:8.4f} {d2:+5.1f}"
              f"  | {rtm_th:8.4f} {rtm_m3:8.4f} {d3:+5.1f}  {rtm_met:8.4f} {d4:+5.1f}")


print("\n" + "="*65)
print("  CP SUPPRESSION GAIN over LP [dB]")
print("="*65)
print(f"\n  {'θ_i':>5s} |", end="")
for m in MATS3: print(f" {m:>12s} |", end="")
print()
print("  " + "-" * 50)
for t in thetas_common:
    print(f"  {t:5.0f}° |", end="")
    for m in MATS3:
        rte = np.mean(np.abs(lp_g[m][t]['R_TE_m3']))
        rtm = np.mean(np.abs(lp_g[m][t]['R_TM_m3']))
        gc = np.mean(np.abs(cp_g_m3[m][t]['Gc_cor']))
        gain = 20*np.log10(max(rte,rtm)/max(gc,1e-6))
        print(f" {gain:10.1f} dB |", end="")
    print()

print("\n  Done.")
