"""
CP + LP Unified Reflection Analysis Pipeline
=============================================
LP M3 issue: M3 = M1 (RX not moved) → unfolded calibration impossible
Workaround: Metal-plate normalization for LP

LP calibration:
  |R̂_TE(mat, θ)| = |h̃_LP,zz(mat, θ)| / |h̃_LP,zz(metal, θ)|  × |R_TE(PEC)|
  |R̂_TM(mat, θ)| = |h̃_LP,yy(mat, θ)| / |h̃_LP,yy(metal, θ)|  × |R_TM(PEC)|

For PEC: |R_TE| = |R_TM| = 1 → denominator is absolute reference.
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

# ================================================================
# MATERIAL PROPERTIES (user-confirmed HFSS values)
# ================================================================

MAT_PROPS = {
    'metal':    {'eps_r': 1e6,  'tan_d': 0.0,   'label': 'Metal (PEC)'},
    'concrete': {'eps_r': 5.24, 'tan_d': 0.105, 'label': 'Concrete'},
    'glass':    {'eps_r': 6.31, 'tan_d': 0.019, 'label': 'Glass'},
    'wood':     {'eps_r': 1.99, 'tan_d': 0.049, 'label': 'Wood'},
}
WALL_THICKNESS_MM = 100.0
MATERIALS = ['metal', 'concrete', 'glass', 'wood']
MATS_NON_METAL = ['concrete', 'glass', 'wood']
COL = {'metal': '#1e293b', 'concrete': '#dc2626', 'glass': '#2563eb', 'wood': '#059669'}
MRK = {'metal': 'D', 'concrete': 'o', 'glass': 's', 'wood': '^'}

# ================================================================
# FRESNEL THEORY
# ================================================================

def fresnel_slab(eps_r, tan_d, theta_deg, thickness_mm, freq_ghz):
    """Slab reflection: Air → dielectric → Air."""
    theta = np.deg2rad(np.asarray(theta_deg, dtype=float))
    eps_c = eps_r * (1 - 1j * tan_d)
    lam = 300.0 / freq_ghz
    k0 = 2 * np.pi / lam
    ct = np.cos(theta); st = np.sin(theta)
    sq = np.sqrt(eps_c - st**2 + 0j)
    r_te = (ct - sq) / (ct + sq)
    r_tm = (eps_c * ct - sq) / (eps_c * ct + sq)
    if thickness_mm is None or thickness_mm <= 0:
        return r_te, r_tm
    delta = k0 * thickness_mm * sq
    e2d = np.exp(-2j * delta)
    R_TE = r_te * (1 - e2d) / (1 - r_te**2 * e2d)
    R_TM = r_tm * (1 - e2d) / (1 - r_tm**2 * e2d)
    return R_TE, R_TM


# ================================================================
# DATA LOADING
# ================================================================

def parse_c(mag, phase_deg):
    return mag * np.exp(1j * np.deg2rad(phase_deg))

def load_m1(path, ch_names):
    df = pd.read_csv(path); c = df.columns.tolist()
    out = {'freq': df[c[0]].values}
    for i, ch in enumerate(ch_names):
        out[ch] = parse_c(df[c[1+2*i]].values, df[c[2+2*i]].values)
    return out

def load_sweep(path, ch_names):
    df = pd.read_csv(path); c = df.columns.tolist()
    thetas = np.array(sorted(df[c[0]].unique()))
    freq = df[df[c[0]] == thetas[0]][c[1]].values
    out = {'freq': freq, 'thetas': thetas}
    for t in thetas:
        sub = df[df[c[0]] == t]; d = {}
        for i, ch in enumerate(ch_names):
            d[ch] = parse_c(sub[c[2+2*i]].values, sub[c[3+2*i]].values)
        out[t] = d
    return out

print("=" * 65)
print("  CP + LP Unified Reflection Analysis")
print("=" * 65)

# --- CP data ---
CP_CH = ['LL', 'LR', 'RL', 'RR']
cp_m1 = load_m1(UPLOAD / "m1_los_5000.csv", CP_CH)
cp_m3 = load_sweep(UPLOAD / "m3_off-boresigjt.csv", CP_CH)
cp_m2 = {m: load_sweep(UPLOAD / f"m2_{m}_R_5000.csv", CP_CH) for m in MATERIALS}

# --- LP data (column order: yy, yz, zy, zz) ---
LP_CH = ['yy', 'yz', 'zy', 'zz']
lp_m1 = load_m1(UPLOAD / "LP_m1_los_5000.csv", LP_CH)
lp_m2 = {m: load_sweep(UPLOAD / f"LP_m2_{m}_R_5000.csv", LP_CH) for m in MATERIALS}

freq = cp_m1['freq']
thetas = cp_m3['thetas']
Nf, Nt = len(freq), len(thetas)
f_center = freq[Nf // 2]
print(f"  Freq: {freq[0]:.3f}–{freq[-1]:.3f} GHz ({Nf} pts)")
print(f"  θ_i: {thetas.tolist()}")
print(f"  Wall thickness: {WALL_THICKNESS_MM} mm")
for m in MATS_NON_METAL:
    p = MAT_PROPS[m]
    print(f"  {m}: ε_r={p['eps_r']}, tanδ={p['tan_d']}")


# ================================================================
# CP CALIBRATION (v2 — M3 corrected)
# ================================================================

print("\n[1] CP calibration (M3-corrected)...")
cp_g = {}
for mat in MATERIALS:
    cp_g[mat] = {}
    for t in thetas:
        h2 = cp_m2[mat][t]; h3 = cp_m3[t]
        ht = {ch: h2[ch] - cp_m1[ch] for ch in CP_CH}
        ratio = (ht['LR'] * ht['RL']) / (h3['RR'] * h3['LL'])
        Gx = np.sqrt(np.abs(ratio)) * np.exp(1j * np.angle(ratio) / 2)
        eps_eff = h3['LR'] / h3['RR']
        Gc_raw = ht['RR'] / h3['RR']
        Gc_cor = Gc_raw - eps_eff * Gx
        cp_g[mat][t] = {
            'Gx': Gx, 'Gc_raw': Gc_raw, 'Gc_cor': Gc_cor,
            'R_TE': Gx + Gc_cor, 'R_TM': Gx - Gc_cor,
        }
print("  Done.")


# ================================================================
# LP CALIBRATION (Metal-plate normalization)
# ================================================================

print("[2] LP calibration (metal-plate normalization)...")
print("    ⚠ LP M3 = M1 (flat) → unfolded calibration unavailable")
print("    → Using metal as |R|=1 reference instead\n")

# LoS subtraction for LP
lp_ht = {}
for mat in MATERIALS:
    lp_ht[mat] = {}
    for t in thetas:
        lp_ht[mat][t] = {ch: lp_m2[mat][t][ch] - lp_m1[ch] for ch in LP_CH}

lp_g = {}
for mat in MATERIALS:
    lp_g[mat] = {}
    for t in thetas:
        ht_mat = lp_ht[mat][t]
        ht_met = lp_ht['metal'][t]
        
        # Metal-plate normalization: R(mat) = h̃(mat) / h̃(metal) × R(PEC)
        # |R_TE(PEC)| = 1, |R_TM(PEC)| = 1
        # For complex: keep phase relative to metal
        R_TE_lp = ht_mat['zz'] / ht_met['zz']   # × R_TE(PEC) = × (-1) for phase
        R_TM_lp = ht_mat['yy'] / ht_met['yy']   # × R_TM(PEC) = × (+1) for phase
        
        # Cross-pol check
        cross_zy = np.mean(np.abs(ht_mat['zy'])) / max(np.mean(np.abs(ht_mat['zz'])), 1e-12)
        cross_yz = np.mean(np.abs(ht_mat['yz'])) / max(np.mean(np.abs(ht_mat['yy'])), 1e-12)
        
        # CP quantities derived from LP
        Gamma_LR = (R_TE_lp + R_TM_lp) / 2
        Gamma_RR = (R_TE_lp - R_TM_lp) / 2
        
        lp_g[mat][t] = {
            'R_TE': R_TE_lp, 'R_TM': R_TM_lp,
            'Gamma_LR': Gamma_LR, 'Gamma_RR': Gamma_RR,
            'cross_zy': cross_zy, 'cross_yz': cross_yz,
        }

# LP cross-pol isolation check
print("  LP Cross-pol isolation (h̃_cross / h̃_co):")
print(f"  {'θ_i':>5s} | {'zy/zz [dB]':>11s} | {'yz/yy [dB]':>11s}")
print("  " + "-" * 38)
for t in [10, 30, 50, 70]:
    zy = lp_g['concrete'][t]['cross_zy']
    yz = lp_g['concrete'][t]['cross_yz']
    print(f"  {t:5.0f}° | {20*np.log10(max(zy,1e-10)):11.1f} | {20*np.log10(max(yz,1e-10)):11.1f}")
print("  (concrete shown; isotropic wall → should be << -20 dB)")


# ================================================================
# FRESNEL THEORY CURVES
# ================================================================

print("\n[3] Fresnel theory (slab model, t=100mm)...")
theta_th = np.linspace(0.5, 89.5, 500)
theory = {}
for mat in MATS_NON_METAL:
    p = MAT_PROPS[mat]
    rte, rtm = fresnel_slab(p['eps_r'], p['tan_d'], theta_th, WALL_THICKNESS_MM, f_center)
    # Also at measurement angles (band-averaged over freq)
    rte_pts = np.zeros(Nt, dtype=complex)
    rtm_pts = np.zeros(Nt, dtype=complex)
    for i, t in enumerate(thetas):
        rte_f, rtm_f = fresnel_slab(p['eps_r'], p['tan_d'], t, WALL_THICKNESS_MM, freq)
        rte_pts[i] = np.mean(rte_f)
        rtm_pts[i] = np.mean(rtm_f)
    theory[mat] = {
        'R_TE': rte, 'R_TM': rtm, 'theta': theta_th,
        'R_TE_pts': rte_pts, 'R_TM_pts': rtm_pts,
        'Brewster': np.rad2deg(np.arctan(np.sqrt(p['eps_r']))),
    }
    print(f"  {mat}: Brewster={theory[mat]['Brewster']:.1f}°")


# ================================================================
# FIGURE 1: LP vs Fresnel — Direct R_TE / R_TM validation
# ================================================================

print("\n[4] Generating figures...")

fig1, axes = plt.subplots(1, 3, figsize=(17, 5.5))
fig1.suptitle("LP-Direct R$_{TE}$, R$_{TM}$ vs Fresnel Slab Theory (100mm)", fontweight='bold')

for idx, mat in enumerate(MATS_NON_METAL):
    ax = axes[idx]
    t = theory[mat]
    
    # Theory curves
    ax.plot(t['theta'], np.abs(t['R_TE']), '-', color='#2563eb', lw=1.5, label=r'$|R_{TE}|$ Fresnel slab', zorder=1)
    ax.plot(t['theta'], np.abs(t['R_TM']), '-', color='#dc2626', lw=1.5, label=r'$|R_{TM}|$ Fresnel slab', zorder=1)
    
    # LP measurement
    rte_lp = [np.mean(np.abs(lp_g[mat][th]['R_TE'])) for th in thetas]
    rtm_lp = [np.mean(np.abs(lp_g[mat][th]['R_TM'])) for th in thetas]
    ax.plot(thetas, rte_lp, 'v', color='#2563eb', markersize=7, label=r'$R_{TE}$ LP-direct', zorder=3)
    ax.plot(thetas, rtm_lp, '^', color='#dc2626', markersize=7, label=r'$R_{TM}$ LP-direct', zorder=3)
    
    ax.axvline(t['Brewster'], color='gray', ls=':', lw=0.8, alpha=0.6)
    ax.text(t['Brewster']+1, 0.95, f"B={t['Brewster']:.0f}°", fontsize=8, color='gray')
    ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('|R| (linear)')
    ax.set_title(f"{MAT_PROPS[mat]['label']} (ε={MAT_PROPS[mat]['eps_r']}, tanδ={MAT_PROPS[mat]['tan_d']})")
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
    ax.set_xlim([5, 80]); ax.set_ylim([0, 1.05])

fig1.tight_layout()
fig1.savefig(OUTPUT / "unified_fig1_LP_vs_fresnel.png", dpi=150, bbox_inches='tight')
print("  [1/5] unified_fig1_LP_vs_fresnel.png")


# ================================================================
# FIGURE 2: LP vs CP vs Fresnel — Triple comparison
# ================================================================

fig2, axes = plt.subplots(2, 3, figsize=(17, 10))
fig2.suptitle("Triple Comparison: LP-Direct vs CP-Derived vs Fresnel Slab Theory", fontweight='bold')

for idx, mat in enumerate(MATS_NON_METAL):
    t = theory[mat]
    
    # --- R_TE ---
    ax = axes[0, idx]
    ax.plot(t['theta'], np.abs(t['R_TE']), '-', color='gray', lw=2, alpha=0.5, label='Fresnel slab')
    rte_lp = [np.mean(np.abs(lp_g[mat][th]['R_TE'])) for th in thetas]
    rte_cp = [np.mean(np.abs(cp_g[mat][th]['R_TE'])) for th in thetas]
    ax.plot(thetas, rte_lp, 'o-', color='#2563eb', markersize=5, lw=1.5, label='LP-direct')
    ax.plot(thetas, rte_cp, 's--', color='#7c3aed', markersize=5, lw=1, alpha=0.8, label='CP-derived')
    ax.axvline(t['Brewster'], color='gray', ls=':', lw=0.5)
    ax.set_ylabel(r'$|R_{TE}|$')
    ax.set_title(f"{MAT_PROPS[mat]['label']} — R$_{{TE}}$")
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
    ax.set_xlim([5, 80])
    
    # --- R_TM ---
    ax = axes[1, idx]
    ax.plot(t['theta'], np.abs(t['R_TM']), '-', color='gray', lw=2, alpha=0.5, label='Fresnel slab')
    rtm_lp = [np.mean(np.abs(lp_g[mat][th]['R_TM'])) for th in thetas]
    rtm_cp = [np.mean(np.abs(cp_g[mat][th]['R_TM'])) for th in thetas]
    ax.plot(thetas, rtm_lp, 'o-', color='#dc2626', markersize=5, lw=1.5, label='LP-direct')
    ax.plot(thetas, rtm_cp, 's--', color='#ea580c', markersize=5, lw=1, alpha=0.8, label='CP-derived')
    ax.axvline(t['Brewster'], color='gray', ls=':', lw=0.5)
    ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|R_{TM}|$')
    ax.set_title(f"{MAT_PROPS[mat]['label']} — R$_{{TM}}$")
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
    ax.set_xlim([5, 80])

fig2.tight_layout()
fig2.savefig(OUTPUT / "unified_fig2_triple_comparison.png", dpi=150, bbox_inches='tight')
print("  [2/5] unified_fig2_triple_comparison.png")


# ================================================================
# FIGURE 3: Calibration Accuracy — LP & CP deviation from Fresnel
# ================================================================

fig3, axes = plt.subplots(2, 3, figsize=(17, 10))
fig3.suptitle("Calibration Accuracy: Deviation from Fresnel Slab Theory [dB]", fontweight='bold')

for idx, mat in enumerate(MATS_NON_METAL):
    for row, (rname, key_cp, key_lp) in enumerate([('R_TE', 'R_TE', 'R_TE'), ('R_TM', 'R_TM', 'R_TM')]):
        ax = axes[row, idx]
        p = MAT_PROPS[mat]
        
        dev_lp, dev_cp = [], []
        for i, t in enumerate(thetas):
            rte_th, rtm_th = fresnel_slab(p['eps_r'], p['tan_d'], t, WALL_THICKNESS_MM, freq)
            th_val = np.mean(np.abs(rte_th)) if key_cp == 'R_TE' else np.mean(np.abs(rtm_th))
            
            lp_val = np.mean(np.abs(lp_g[mat][t][key_lp]))
            cp_val = np.mean(np.abs(cp_g[mat][t][key_cp]))
            
            dev_lp.append(20*np.log10(lp_val/th_val) if th_val > 1e-6 else float('nan'))
            dev_cp.append(20*np.log10(cp_val/th_val) if th_val > 1e-6 else float('nan'))
        
        ax.plot(thetas, dev_lp, 'o-', color='#2563eb', markersize=5, label='LP-direct')
        ax.plot(thetas, dev_cp, 's--', color='#7c3aed', markersize=5, alpha=0.8, label='CP-derived')
        ax.axhline(0, color='black', ls='-', lw=0.5)
        ax.axhline(3, color='gray', ls=':', lw=0.5, alpha=0.5)
        ax.axhline(-3, color='gray', ls=':', lw=0.5, alpha=0.5)
        ax.fill_between([5, 80], -3, 3, alpha=0.05, color='green')
        ax.set_xlabel(r'$\theta_i$ [deg]')
        ax.set_ylabel(f'{rname} deviation [dB]')
        ax.set_title(f"{MAT_PROPS[mat]['label']} — {rname}")
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
        ax.set_xlim([5, 80]); ax.set_ylim([-15, 15])

fig3.tight_layout()
fig3.savefig(OUTPUT / "unified_fig3_accuracy.png", dpi=150, bbox_inches='tight')
print("  [3/5] unified_fig3_accuracy.png")


# ================================================================
# FIGURE 4: CP MULTIPATH SUPPRESSION GAIN (핵심 Track 2 지표)
# ================================================================

fig4, axes = plt.subplots(1, 3, figsize=(17, 5.5))
fig4.suptitle("CP Multipath Suppression Gain over LP (Single-Bounce)", fontweight='bold')

# (a) |R_TE|_LP (z-pol co-pol multipath) vs |Γ_RR|_CP (CP co-pol residual)
ax = axes[0]
for mat in MATS_NON_METAL:
    rte_lp = np.array([np.mean(np.abs(lp_g[mat][t]['R_TE'])) for t in thetas])
    grr_cp = np.array([np.mean(np.abs(cp_g[mat][t]['Gc_cor'])) for t in thetas])
    gain = 20 * np.log10(rte_lp / np.maximum(grr_cp, 1e-6))
    ax.plot(thetas, gain, f'{MRK[mat]}-', color=COL[mat], label=MAT_PROPS[mat]['label'], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('Suppression Gain [dB]')
ax.set_title(r'(a) vs z-pol LP: $|R_{TE}^{LP}| / |\Gamma_{RR}^{CP}|$')
ax.legend(); ax.grid(True, alpha=0.3)

# (b) |R_TM|_LP (y-pol co-pol multipath) vs |Γ_RR|_CP
ax = axes[1]
for mat in MATS_NON_METAL:
    rtm_lp = np.array([np.mean(np.abs(lp_g[mat][t]['R_TM'])) for t in thetas])
    grr_cp = np.array([np.mean(np.abs(cp_g[mat][t]['Gc_cor'])) for t in thetas])
    gain = 20 * np.log10(rtm_lp / np.maximum(grr_cp, 1e-6))
    ax.plot(thetas, gain, f'{MRK[mat]}-', color=COL[mat], label=MAT_PROPS[mat]['label'], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('Suppression Gain [dB]')
ax.set_title(r'(b) vs y-pol LP: $|R_{TM}^{LP}| / |\Gamma_{RR}^{CP}|$')
ax.legend(); ax.grid(True, alpha=0.3)

# (c) Worst-case LP vs CP
ax = axes[2]
for mat in MATS_NON_METAL:
    rte_lp = np.array([np.mean(np.abs(lp_g[mat][t]['R_TE'])) for t in thetas])
    rtm_lp = np.array([np.mean(np.abs(lp_g[mat][t]['R_TM'])) for t in thetas])
    lp_worst = np.maximum(rte_lp, rtm_lp)
    grr_cp = np.array([np.mean(np.abs(cp_g[mat][t]['Gc_cor'])) for t in thetas])
    gain = 20 * np.log10(lp_worst / np.maximum(grr_cp, 1e-6))
    ax.plot(thetas, gain, f'{MRK[mat]}-', color=COL[mat], label=MAT_PROPS[mat]['label'], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('Suppression Gain [dB]')
ax.set_title(r'(c) Worst-case LP: $\max(|R_{TE}|,|R_{TM}|) / |\Gamma_{RR}^{CP}|$')
ax.legend(); ax.grid(True, alpha=0.3)

fig4.tight_layout()
fig4.savefig(OUTPUT / "unified_fig4_suppression_gain.png", dpi=150, bbox_inches='tight')
print("  [4/5] unified_fig4_suppression_gain.png")


# ================================================================
# FIGURE 5: COMPREHENSIVE SUMMARY (6-panel)
# ================================================================

fig5, axes = plt.subplots(2, 3, figsize=(17, 10))
fig5.suptitle("Comprehensive Summary: CP-UWB Reflection Analysis\n"
              f"(d=5m, f={freq[0]:.2f}–{freq[-1]:.2f} GHz, Wall={WALL_THICKNESS_MM:.0f}mm)",
              fontweight='bold', fontsize=13)

# (a) CP Cross Γ_X
ax = axes[0, 0]
for mat in MATERIALS:
    vals = [np.mean(np.abs(cp_g[mat][t]['Gx'])) for t in thetas]
    ax.plot(thetas, vals, f'{MRK[mat]}-', color=COL[mat], label=MAT_PROPS[mat]['label'], markersize=5)
ax.set_ylabel(r'$|\hat{\Gamma}_X|$ (linear)'); ax.set_title(r'(a) CP Cross $\hat{\Gamma}_X$')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (b) CP Co Γ_C (corrected)
ax = axes[0, 1]
for mat in MATERIALS:
    vals = [np.mean(np.abs(cp_g[mat][t]['Gc_cor'])) for t in thetas]
    ax.plot(thetas, vals, f'{MRK[mat]}-', color=COL[mat], label=MAT_PROPS[mat]['label'], markersize=5)
ax.set_ylabel(r'$|\hat{\Gamma}_C^{corr}|$ (linear)'); ax.set_title(r'(b) CP Co $\hat{\Gamma}_C^{corr}$')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (c) CP XPD
ax = axes[0, 2]
for mat in MATERIALS:
    xpd = [20*np.log10(np.mean(np.abs(cp_g[mat][t]['Gx'])) /
            max(np.mean(np.abs(cp_g[mat][t]['Gc_cor'])), 1e-10)) for t in thetas]
    ax.plot(thetas, xpd, f'{MRK[mat]}-', color=COL[mat], label=MAT_PROPS[mat]['label'], markersize=5)
ax.axhline(0, color='gray', ls=':', lw=1)
ax.set_ylabel('XPD [dB]'); ax.set_title(r'(c) CP Reflected XPD')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (d) LP R_TE vs theory
ax = axes[1, 0]
for mat in MATS_NON_METAL:
    t = theory[mat]
    ax.plot(t['theta'], np.abs(t['R_TE']), '-', color=COL[mat], lw=1, alpha=0.4)
    rte_lp = [np.mean(np.abs(lp_g[mat][th]['R_TE'])) for th in thetas]
    ax.plot(thetas, rte_lp, f'{MRK[mat]}-', color=COL[mat], label=MAT_PROPS[mat]['label'], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|R_{TE}|$')
ax.set_title(r'(d) LP $R_{TE}$ (markers) vs Fresnel (line)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (e) LP R_TM vs theory
ax = axes[1, 1]
for mat in MATS_NON_METAL:
    t = theory[mat]
    ax.plot(t['theta'], np.abs(t['R_TM']), '-', color=COL[mat], lw=1, alpha=0.4)
    rtm_lp = [np.mean(np.abs(lp_g[mat][th]['R_TM'])) for th in thetas]
    ax.plot(thetas, rtm_lp, f'{MRK[mat]}-', color=COL[mat], label=MAT_PROPS[mat]['label'], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|R_{TM}|$')
ax.set_title(r'(e) LP $R_{TM}$ (markers) vs Fresnel (line)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (f) Suppression gain (worst-case LP)
ax = axes[1, 2]
for mat in MATS_NON_METAL:
    rte_lp = np.array([np.mean(np.abs(lp_g[mat][t]['R_TE'])) for t in thetas])
    rtm_lp = np.array([np.mean(np.abs(lp_g[mat][t]['R_TM'])) for t in thetas])
    lp_worst = np.maximum(rte_lp, rtm_lp)
    grr_cp = np.array([np.mean(np.abs(cp_g[mat][t]['Gc_cor'])) for t in thetas])
    gain = 20 * np.log10(lp_worst / np.maximum(grr_cp, 1e-6))
    ax.plot(thetas, gain, f'{MRK[mat]}-', color=COL[mat], label=MAT_PROPS[mat]['label'], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('Gain [dB]')
ax.set_title(r'(f) CP Suppression Gain over LP')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

fig5.tight_layout()
fig5.savefig(OUTPUT / "unified_fig5_summary.png", dpi=150, bbox_inches='tight')
print("  [5/5] unified_fig5_summary.png")


# ================================================================
# NUMERICAL TABLES
# ================================================================

print("\n" + "=" * 65)
print("  LP CALIBRATION ACCURACY vs Fresnel Slab Theory")
print("=" * 65)

for mat in MATS_NON_METAL:
    p = MAT_PROPS[mat]
    print(f"\n  ━━━ {p['label']} ━━━")
    print(f"  {'θ_i':>5s} | {'|R_TE|_th':>8s} {'|R_TE|_LP':>8s} {'Δ_LP':>6s} {'|R_TE|_CP':>8s} {'Δ_CP':>6s}"
          f" | {'|R_TM|_th':>8s} {'|R_TM|_LP':>8s} {'Δ_LP':>6s} {'|R_TM|_CP':>8s} {'Δ_CP':>6s}")
    print("  " + "-" * 100)
    for t in thetas:
        rte_f, rtm_f = fresnel_slab(p['eps_r'], p['tan_d'], t, WALL_THICKNESS_MM, freq)
        rte_th = np.mean(np.abs(rte_f)); rtm_th = np.mean(np.abs(rtm_f))
        rte_lp = np.mean(np.abs(lp_g[mat][t]['R_TE']))
        rtm_lp = np.mean(np.abs(lp_g[mat][t]['R_TM']))
        rte_cp = np.mean(np.abs(cp_g[mat][t]['R_TE']))
        rtm_cp = np.mean(np.abs(cp_g[mat][t]['R_TM']))
        
        d_te_lp = 20*np.log10(rte_lp/rte_th) if rte_th>1e-6 else float('nan')
        d_te_cp = 20*np.log10(rte_cp/rte_th) if rte_th>1e-6 else float('nan')
        d_tm_lp = 20*np.log10(rtm_lp/rtm_th) if rtm_th>1e-6 else float('nan')
        d_tm_cp = 20*np.log10(rtm_cp/rtm_th) if rtm_th>1e-6 else float('nan')
        
        print(f"  {t:5.0f}° | {rte_th:8.4f} {rte_lp:8.4f} {d_te_lp:+5.1f}  {rte_cp:8.4f} {d_te_cp:+5.1f}"
              f"  | {rtm_th:8.4f} {rtm_lp:8.4f} {d_tm_lp:+5.1f}  {rtm_cp:8.4f} {d_tm_cp:+5.1f}")

print("\n" + "=" * 65)
print("  CP SUPPRESSION GAIN over LP (band-averaged)")
print("=" * 65)
print(f"\n  {'θ_i':>5s} |", end="")
for mat in MATS_NON_METAL:
    print(f" {mat:>20s} |", end="")
print()
print("  " + "-" * 72)
for t in thetas:
    print(f"  {t:5.0f}° |", end="")
    for mat in MATS_NON_METAL:
        rte = np.mean(np.abs(lp_g[mat][t]['R_TE']))
        rtm = np.mean(np.abs(lp_g[mat][t]['R_TM']))
        lp_w = max(rte, rtm)
        gc = np.mean(np.abs(cp_g[mat][t]['Gc_cor']))
        gain = 20*np.log10(lp_w/gc) if gc > 1e-6 else float('inf')
        print(f" {gain:18.1f} dB |", end="")
    print()

print("\n  Done. All outputs in /mnt/user-data/outputs/")
