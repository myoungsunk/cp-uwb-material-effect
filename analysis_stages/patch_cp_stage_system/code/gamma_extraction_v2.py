"""
CP-UWB Patch-CP Stage Reflection Metric Extraction Pipeline (v2)
================================================================
Key update: Co-term correction using M3 leakage ratio (NOT metal floor)

Γ̂_C_corrected = Γ̂_C_raw − (h3_LR / h3_RR) · Γ̂_X

This removes first-order antenna leakage contamination proportional to each
material's own cross reflection, using only M1/M3 data.

Important scope note:
  - All outputs in this script are patch-inclusive system-stage results.
  - Ideal plane-wave / material-only results are NOT produced here.
  - Derived TE/TM outputs below are proxies inferred from patch-stage data.

Convention:
  Channel h_pq: p = RX port, q = TX port
  S(RX_LH_p1, TX_RH_p1) → h_LR (RX=L, TX=R)
  θ_i = angle from wall normal (= θ_r by Snell)
  α = 90° − θ_i = off-boresight angle
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

plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'legend.fontsize': 8,
    'figure.dpi': 150,
})

UPLOAD = Path("/mnt/user-data/uploads")
STAGE_ROOT = Path(__file__).resolve().parents[1]
UPLOAD = STAGE_ROOT / "csv"
OUTPUT = STAGE_ROOT / "results"
OUTPUT.mkdir(exist_ok=True)

CHANNELS = ['LL', 'LR', 'RL', 'RR']
MATERIALS = ['metal', 'concrete', 'glass', 'wood']
MAT_COLORS = {'metal': '#1e293b', 'concrete': '#dc2626', 'glass': '#2563eb', 'wood': '#059669'}
MAT_MARKERS = {'metal': 'D', 'concrete': 'o', 'glass': 's', 'wood': '^'}
MAT_LABELS = {'metal': 'Metal (PEC ref)', 'concrete': 'Concrete', 'glass': 'Glass', 'wood': 'Wood'}


# ================================================================
# STEP 0: DATA LOADING
# ================================================================

def parse_complex(mag, phase_deg):
    """Convert magnitude + phase(deg) to complex."""
    return mag * np.exp(1j * np.deg2rad(phase_deg))


def load_m1(path):
    """Load M1 LoS: returns {freq, LL, LR, RL, RR} as arrays."""
    df = pd.read_csv(path)
    c = df.columns.tolist()
    out = {'freq': df[c[0]].values}
    for i, ch in enumerate(CHANNELS):
        out[ch] = parse_complex(df[c[1+2*i]].values, df[c[2+2*i]].values)
    return out


def load_sweep(path):
    """Load M2/M3 with theta sweep: returns {freq, thetas, theta_val: {LL,LR,RL,RR}}."""
    df = pd.read_csv(path)
    c = df.columns.tolist()
    thetas = np.array(sorted(df[c[0]].unique()))
    freq = df[df[c[0]] == thetas[0]][c[1]].values
    out = {'freq': freq, 'thetas': thetas}
    for t in thetas:
        sub = df[df[c[0]] == t]
        d = {}
        for i, ch in enumerate(CHANNELS):
            d[ch] = parse_complex(sub[c[2+2*i]].values, sub[c[3+2*i]].values)
        out[t] = d
    return out


print("=" * 65)
print("  CP-UWB Patch-Stage Reflection Metric Extraction Pipeline v2")
print("  M3-based first-order co-term leakage correction")
print("  Scope: patch-inclusive system response, not ideal plane-wave material truth")
print("=" * 65)

print("\n[Step 0] Loading data...")
m1 = load_m1(UPLOAD / "m1_los_5000.csv")
m3 = load_sweep(UPLOAD / "m3_off-boresigjt.csv")
m2 = {mat: load_sweep(UPLOAD / f"m2_{mat}_R_5000.csv") for mat in MATERIALS}

freq = m1['freq']
thetas = m3['thetas']
Nf, Nt = len(freq), len(thetas)
print(f"  Freq: {freq[0]:.3f}–{freq[-1]:.3f} GHz ({Nf} pts, BW={freq[-1]-freq[0]:.0f} MHz)")
print(f"  θ_i:  {thetas.tolist()}")
print(f"  Materials: {MATERIALS}")


# ================================================================
# STEP 1: PHASE 0 — ANTENNA DIAGNOSTICS
# ================================================================

print("\n[Step 1] Phase 0: Antenna diagnostics from M3...")

# Per-theta, band-averaged diagnostics
diag = {
    'eps_LR_RR': np.zeros(Nt),   # |h3_LR|/|h3_RR| — combined TX+RX leakage (TX=R path)
    'eps_RL_LL': np.zeros(Nt),   # |h3_RL|/|h3_LL| — combined TX+RX leakage (TX=L path)
    'port_asym': np.zeros(Nt),   # |h3_RR|/|h3_LL| in dB — port symmetry
    'eps_eff':   np.zeros(Nt, dtype=complex),  # h3_LR/h3_RR — complex ε_eff for co-term correction
}

for i, t in enumerate(thetas):
    d = m3[t]
    diag['eps_LR_RR'][i] = np.mean(np.abs(d['LR']) / np.abs(d['RR']))
    diag['eps_RL_LL'][i] = np.mean(np.abs(d['RL']) / np.abs(d['LL']))
    diag['port_asym'][i] = 20 * np.log10(np.mean(np.abs(d['RR'])) / np.mean(np.abs(d['LL'])))
    # Complex ε_eff per frequency (used in Step 4)
    # Stored per-theta as full freq array
    diag[f'eps_eff_complex_{t}'] = d['LR'] / d['RR']

print(f"\n  {'θ_i':>5s} | {'ε(LR/RR)':>10s} | {'ε(RL/LL)':>10s} | {'PortAsym':>10s}")
print("  " + "-" * 48)
for i, t in enumerate(thetas):
    e1 = 20 * np.log10(diag['eps_LR_RR'][i])
    e2 = 20 * np.log10(diag['eps_RL_LL'][i])
    print(f"  {t:5.0f}° | {e1:8.1f} dB | {e2:8.1f} dB | {diag['port_asym'][i]:8.2f} dB")

a1_worst = max(20*np.log10(diag['eps_LR_RR'].max()), 20*np.log10(diag['eps_RL_LL'].max()))
a2_worst = np.abs(diag['port_asym']).max()
print(f"\n  A1 (diagonal dominance): worst = {a1_worst:.1f} dB  {'✓' if a1_worst < -20 else '✗ (co-term correction 필수)'}")
print(f"  A2 (port symmetry):      worst = {a2_worst:.2f} dB  {'✓' if a2_worst < 1 else '✗'}")


# ================================================================
# STEP 2: LoS SUBTRACTION
# ================================================================

print("\n[Step 2] LoS subtraction (M2 − M1)...")
h_tilde = {mat: {} for mat in MATERIALS}
for mat in MATERIALS:
    for t in thetas:
        h_tilde[mat][t] = {}
        for ch in CHANNELS:
            h_tilde[mat][t][ch] = m2[mat][t][ch] - m1[ch]

print("  Done. h̃_pq(f, θ) computed for all materials.")


# ================================================================
# STEP 3: CROSS ESTIMATOR — Γ̂_X
# ================================================================

print("\n[Step 3] Cross estimator Γ̂_X (reciprocity geometric mean)...")
gamma = {mat: {} for mat in MATERIALS}

for mat in MATERIALS:
    for t in thetas:
        ht = h_tilde[mat][t]
        h3 = m3[t]
        
        # Γ̂_X = sqrt( h̃_LR · h̃_RL / (h3_RR · h3_LL) )
        ratio = (ht['LR'] * ht['RL']) / (h3['RR'] * h3['LL'])
        Gamma_X = np.sqrt(np.abs(ratio)) * np.exp(1j * np.angle(ratio) / 2)
        
        gamma[mat][t] = {'Gamma_X': Gamma_X}

print("  Done.")


# ================================================================
# STEP 4: CO ESTIMATOR — RAW + M3-CORRECTED
# ================================================================

print("\n[Step 4] Co estimator: raw + M3-based leakage correction...")

for mat in MATERIALS:
    for t in thetas:
        ht = h_tilde[mat][t]
        h3 = m3[t]
        
        # Raw: Γ̂_C_raw = h̃_RR / h3_RR
        Gamma_C_raw = ht['RR'] / h3['RR']
        
        # M3 leakage correction:
        # ε_eff(f, α) = h3_LR(f) / h3_RR(f)  — frequency-resolved complex ratio
        # contamination ≈ ε_eff · Γ_LR ≈ ε_eff · Γ̂_X
        # corrected = raw − contamination
        eps_eff = diag[f'eps_eff_complex_{t}']
        Gamma_X = gamma[mat][t]['Gamma_X']
        
        Gamma_C_corr = Gamma_C_raw - eps_eff * Gamma_X
        
        gamma[mat][t]['Gamma_C_raw'] = Gamma_C_raw
        gamma[mat][t]['Gamma_C_corr'] = Gamma_C_corr

# Print correction impact
print(f"\n  Correction impact (band-avg |Γ_C_raw| → |Γ_C_corr|):")
print(f"  {'Mat':>10s} {'θ_i':>5s} | {'|Γ_C_raw|':>10s} → {'|Γ_C_corr|':>10s} | {'Δ dB':>8s}")
print("  " + "-" * 55)
for mat in ['metal', 'glass', 'wood']:
    for t in [20, 45, 65]:
        raw = np.mean(np.abs(gamma[mat][t]['Gamma_C_raw']))
        cor = np.mean(np.abs(gamma[mat][t]['Gamma_C_corr']))
        delta = 20*np.log10(cor/raw) if raw > 1e-10 and cor > 1e-10 else float('nan')
        print(f"  {mat:>10s} {t:5.0f}° | {raw:10.4f} → {cor:10.4f} | {delta:8.1f}")


# ================================================================
# STEP 5: TE/TM DERIVATION
# ================================================================

print("\n[Step 5] Derived TE/TM proxies from patch-stage CP quantities...")

for mat in MATERIALS:
    for t in thetas:
        gx = gamma[mat][t]['Gamma_X']
        gc_raw = gamma[mat][t]['Gamma_C_raw']
        gc_cor = gamma[mat][t]['Gamma_C_corr']
        
        # Using corrected co-term
        gamma[mat][t]['R_TE'] = gx + gc_cor
        gamma[mat][t]['R_TM'] = gx - gc_cor
        
        # Also store raw-based for comparison
        gamma[mat][t]['R_TE_raw'] = gx + gc_raw
        gamma[mat][t]['R_TM_raw'] = gx - gc_raw
        
        # Single-channel estimators for reciprocity check
        gamma[mat][t]['Gamma_LR_single'] = h_tilde[mat][t]['LR'] / m3[t]['RR']
        gamma[mat][t]['Gamma_RL_single'] = h_tilde[mat][t]['RL'] / m3[t]['LL']

print("  Done.")


# ================================================================
# STEP 6: VALIDATION
# ================================================================

print("\n[Step 6] Validation checks...")

# 6a. Metal diagnostic
print("\n  --- Metal Diagnostic (basis-dependent; not a strict zero criterion) ---")
print(f"  {'θ_i':>5s} | {'|Γ_X|':>7s} | {'|Γ_C_raw|':>9s} | {'|Γ_C_corr|':>10s} | {'XPD_raw':>8s} | {'XPD_corr':>9s}")
print("  " + "-" * 65)
for t in thetas:
    gx = np.mean(np.abs(gamma['metal'][t]['Gamma_X']))
    gc_raw = np.mean(np.abs(gamma['metal'][t]['Gamma_C_raw']))
    gc_cor = np.mean(np.abs(gamma['metal'][t]['Gamma_C_corr']))
    xpd_raw = 20*np.log10(gx/gc_raw) if gc_raw > 1e-10 else 999
    xpd_cor = 20*np.log10(gx/gc_cor) if gc_cor > 1e-10 else 999
    print(f"  {t:5.0f}° | {gx:7.3f} | {gc_raw:9.4f} | {gc_cor:10.4f} | {xpd_raw:8.1f} | {xpd_cor:9.1f}")

# 6b. Reciprocity check
print("\n  --- Reciprocity Check (|Γ_LR/Γ_RL| deviation) ---")
print(f"  {'θ_i':>5s} |", end="")
for mat in MATERIALS:
    print(f" {mat:>10s} |", end="")
print()
print("  " + "-" * 55)
for t in thetas:
    print(f"  {t:5.0f}° |", end="")
    for mat in MATERIALS:
        glr = np.mean(np.abs(gamma[mat][t]['Gamma_LR_single']))
        grl = np.mean(np.abs(gamma[mat][t]['Gamma_RL_single']))
        dev = 20*np.log10(glr/grl) if grl > 1e-10 else float('nan')
        print(f" {dev:8.2f} dB |", end="")
    print()


# ================================================================
# STEP 7: VISUALIZATION
# ================================================================

print("\n[Step 7] Generating figures...")


# ---- Figure 1: Phase 0 Antenna Diagnostics ----

fig1, axes = plt.subplots(1, 3, figsize=(16, 5))
fig1.suptitle("Phase 0: Antenna Diagnostics (M3 Off-Boresight)", fontweight='bold')

ax = axes[0]
ax.plot(thetas, 20*np.log10(diag['eps_LR_RR']), 'o-', label=r'$|h_{3,LR}|/|h_{3,RR}|$', color='#2563eb')
ax.plot(thetas, 20*np.log10(diag['eps_RL_LL']), 's--', label=r'$|h_{3,RL}|/|h_{3,LL}|$', color='#dc2626')
ax.axhline(-20, color='gray', ls=':', lw=1, label='−20 dB threshold')
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('Leakage [dB]')
ax.set_title(r'A1: Cross-pol Leakage $\epsilon(\theta)$')
ax.legend(); ax.grid(True, alpha=0.3)

ax = axes[1]
ax.plot(thetas, diag['port_asym'], 'o-', color='#059669')
ax.axhline(1, color='gray', ls=':', lw=1); ax.axhline(-1, color='gray', ls=':', lw=1)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('[dB]')
ax.set_title('A2: R/L Port Symmetry')
ax.grid(True, alpha=0.3)

ax = axes[2]
eps_mag = [20*np.log10(np.mean(np.abs(diag[f'eps_eff_complex_{t}']))) for t in thetas]
ax.plot(thetas, eps_mag, 'o-', color='#7c3aed')
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|\epsilon_{eff}|$ [dB]')
ax.set_title(r'$\epsilon_{eff}(\alpha) = h_{3,LR}/h_{3,RR}$ (Correction Factor)')
ax.grid(True, alpha=0.3)

fig1.tight_layout()
fig1.savefig(OUTPUT / "fig1_phase0_diagnostics.png", dpi=150, bbox_inches='tight')
print("  [1/6] fig1_phase0_diagnostics.png")


# ---- Figure 2: Co-term Correction Effect ----

fig2, axes = plt.subplots(1, 3, figsize=(16, 5))
fig2.suptitle("Patch-Stage Co-term Correction: Raw vs M3-Corrected", fontweight='bold')

# (a) |Γ_C| raw vs corrected for all materials
ax = axes[0]
for mat in MATERIALS:
    raw = [np.mean(np.abs(gamma[mat][t]['Gamma_C_raw'])) for t in thetas]
    cor = [np.mean(np.abs(gamma[mat][t]['Gamma_C_corr'])) for t in thetas]
    ax.plot(thetas, raw, f'{MAT_MARKERS[mat]}--', color=MAT_COLORS[mat], alpha=0.4, markersize=4)
    ax.plot(thetas, cor, f'{MAT_MARKERS[mat]}-', color=MAT_COLORS[mat], label=MAT_LABELS[mat], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|\hat{\Gamma}_C|$ (linear)')
ax.set_title(r'(a) $|\hat{\Gamma}_C|$ — dashed=raw, solid=corrected')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# (b) Metal co-term (should approach 0 after correction)
ax = axes[1]
raw = [np.mean(np.abs(gamma['metal'][t]['Gamma_C_raw'])) for t in thetas]
cor = [np.mean(np.abs(gamma['metal'][t]['Gamma_C_corr'])) for t in thetas]
ax.plot(thetas, raw, 'D--', color='gray', label='Metal raw', markersize=5)
ax.plot(thetas, cor, 'D-', color='#1e293b', label='Metal corrected', markersize=5)
ax.axhline(0, color='black', ls='-', lw=0.5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|\hat{\Gamma}_C|$ (linear)')
ax.set_title('(b) Metal Co-term Diagnostic (basis-dependent)')
ax.legend(); ax.grid(True, alpha=0.3)

# (c) XPD improvement
ax = axes[2]
for mat in MATERIALS:
    xpd_raw = [20*np.log10(np.mean(np.abs(gamma[mat][t]['Gamma_X'])) /
                max(np.mean(np.abs(gamma[mat][t]['Gamma_C_raw'])), 1e-10)) for t in thetas]
    xpd_cor = [20*np.log10(np.mean(np.abs(gamma[mat][t]['Gamma_X'])) /
                max(np.mean(np.abs(gamma[mat][t]['Gamma_C_corr'])), 1e-10)) for t in thetas]
    ax.plot(thetas, xpd_raw, f'{MAT_MARKERS[mat]}--', color=MAT_COLORS[mat], alpha=0.4, markersize=4)
    ax.plot(thetas, xpd_cor, f'{MAT_MARKERS[mat]}-', color=MAT_COLORS[mat], label=MAT_LABELS[mat], markersize=5)
ax.axhline(0, color='gray', ls=':', lw=1)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('XPD [dB]')
ax.set_title('(c) XPD — dashed=raw, solid=corrected')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

fig2.tight_layout()
fig2.savefig(OUTPUT / "fig2_coterm_correction.png", dpi=150, bbox_inches='tight')
print("  [2/6] fig2_coterm_correction.png")


# ---- Figure 3: Main Results — Γ_X, Γ_C, XPD vs θ_i ----

fig3, axes = plt.subplots(1, 3, figsize=(16, 5))
fig3.suptitle("Patch-Stage Calibrated CP Metrics (Band-Averaged)", fontweight='bold')

# (a) |Γ_X|
ax = axes[0]
for mat in MATERIALS:
    vals = [np.mean(np.abs(gamma[mat][t]['Gamma_X'])) for t in thetas]
    ax.plot(thetas, vals, f'{MAT_MARKERS[mat]}-', label=MAT_LABELS[mat], color=MAT_COLORS[mat], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|\hat{\Gamma}_X|$ (linear)')
ax.set_title(r'(a) Cross $|\hat{\Gamma}_X|$ — Main Patch-Stage Reflection Metric')
ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

# (b) |Γ_C_corr|
ax = axes[1]
for mat in MATERIALS:
    vals = [np.mean(np.abs(gamma[mat][t]['Gamma_C_corr'])) for t in thetas]
    ax.plot(thetas, vals, f'{MAT_MARKERS[mat]}-', label=MAT_LABELS[mat], color=MAT_COLORS[mat], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|\hat{\Gamma}_C^{corr}|$ (linear)')
ax.set_title(r'(b) Co $|\hat{\Gamma}_C^{corr}|$ — M3-Corrected Patch-Stage Metric')
ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

# (c) XPD (corrected)
ax = axes[2]
for mat in MATERIALS:
    xpd = [20*np.log10(np.mean(np.abs(gamma[mat][t]['Gamma_X'])) /
            max(np.mean(np.abs(gamma[mat][t]['Gamma_C_corr'])), 1e-10)) for t in thetas]
    ax.plot(thetas, xpd, f'{MAT_MARKERS[mat]}-', label=MAT_LABELS[mat], color=MAT_COLORS[mat], markersize=5)
ax.axhline(0, color='gray', ls=':', lw=1)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel('XPD [dB]')
ax.set_title(r'(c) $XPD_{refl}$ (Corrected)')
ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

fig3.tight_layout()
fig3.savefig(OUTPUT / "fig3_main_results.png", dpi=150, bbox_inches='tight')
print("  [3/6] fig3_main_results.png")


# ---- Figure 4: R_TE / R_TM — Brewster Analysis ----

fig4, axes = plt.subplots(1, 3, figsize=(16, 5))
fig4.suptitle("Derived TE/TM Proxies from Patch-Stage CP Metrics", fontweight='bold')

# (a) |R_TE|
ax = axes[0]
for mat in MATERIALS:
    vals = [np.mean(np.abs(gamma[mat][t]['R_TE'])) for t in thetas]
    ax.plot(thetas, vals, f'{MAT_MARKERS[mat]}-', label=MAT_LABELS[mat], color=MAT_COLORS[mat], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|R_{TE}|$ (linear)')
ax.set_title(r'(a) $|R_{TE}|$ proxy'); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

# (b) |R_TM|
ax = axes[1]
for mat in ['concrete', 'glass', 'wood']:
    vals = [np.mean(np.abs(gamma[mat][t]['R_TM'])) for t in thetas]
    ax.plot(thetas, vals, f'{MAT_MARKERS[mat]}-', label=MAT_LABELS[mat], color=MAT_COLORS[mat], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|R_{TM}|$ (linear)')
ax.set_title(r'(b) $|R_{TM}|$ proxy — Brewster-like dip'); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

# (c) Raw vs Corrected R_TM comparison
ax = axes[2]
for mat in ['concrete', 'glass', 'wood']:
    raw = [np.mean(np.abs(gamma[mat][t]['R_TM_raw'])) for t in thetas]
    cor = [np.mean(np.abs(gamma[mat][t]['R_TM'])) for t in thetas]
    ax.plot(thetas, raw, f'{MAT_MARKERS[mat]}--', color=MAT_COLORS[mat], alpha=0.4, markersize=4)
    ax.plot(thetas, cor, f'{MAT_MARKERS[mat]}-', color=MAT_COLORS[mat], label=MAT_LABELS[mat], markersize=5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|R_{TM}|$ (linear)')
ax.set_title(r'(c) $|R_{TM}|$ proxy — dashed=raw, solid=corrected')
ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

fig4.tight_layout()
fig4.savefig(OUTPUT / "fig4_TE_TM_brewster.png", dpi=150, bbox_inches='tight')
print("  [4/6] fig4_TE_TM_brewster.png")


# ---- Figure 5: Frequency-Resolved at Key Angles ----

key_angles = [20, 35, 56, 65]
fig5, axes = plt.subplots(len(key_angles), 3, figsize=(16, 4*len(key_angles)))
fig5.suptitle("Frequency-Resolved Patch-Stage Metrics at Key Angles", fontweight='bold', y=1.01)

for row, t in enumerate(key_angles):
    # |Γ_X|
    ax = axes[row, 0]
    for mat in MATERIALS:
        ax.plot(freq, 20*np.log10(np.abs(gamma[mat][t]['Gamma_X'])),
                label=MAT_LABELS[mat], color=MAT_COLORS[mat], lw=0.8, alpha=0.85)
    ax.set_ylabel(r'$|\hat{\Gamma}_X|$ [dB]')
    ax.set_title(f'θ_i={t}° — Cross patch-stage metric')
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
    
    # |Γ_C_corr|
    ax = axes[row, 1]
    for mat in MATERIALS:
        ax.plot(freq, 20*np.log10(np.maximum(np.abs(gamma[mat][t]['Gamma_C_corr']), 1e-6)),
                label=MAT_LABELS[mat], color=MAT_COLORS[mat], lw=0.8, alpha=0.85)
    ax.set_ylabel(r'$|\hat{\Gamma}_C^{corr}|$ [dB]')
    ax.set_title(f'θ_i={t}° — Co patch-stage metric (corrected)')
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
    
    # |R_TM|
    ax = axes[row, 2]
    for mat in ['concrete', 'glass', 'wood']:
        ax.plot(freq, 20*np.log10(np.maximum(np.abs(gamma[mat][t]['R_TM']), 1e-6)),
                label=MAT_LABELS[mat], color=MAT_COLORS[mat], lw=0.8, alpha=0.85)
    ax.set_ylabel(r'$|R_{TM}|$ [dB]')
    ax.set_title(f'θ_i={t}° — R_TM proxy')
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
    
    if row == len(key_angles) - 1:
        for c in range(3):
            axes[row, c].set_xlabel('Freq [GHz]')

fig5.tight_layout()
fig5.savefig(OUTPUT / "fig5_freq_resolved.png", dpi=150, bbox_inches='tight')
print("  [5/6] fig5_freq_resolved.png")


# ---- Figure 6: Reciprocity Validation ----

fig6, axes = plt.subplots(1, 2, figsize=(14, 5))
fig6.suptitle("Reciprocity Validation: Γ_LR vs Γ_RL", fontweight='bold')

ax = axes[0]
for mat in MATERIALS:
    glr = [np.mean(np.abs(gamma[mat][t]['Gamma_LR_single'])) for t in thetas]
    grl = [np.mean(np.abs(gamma[mat][t]['Gamma_RL_single'])) for t in thetas]
    ax.plot(thetas, glr, f'{MAT_MARKERS[mat]}-', color=MAT_COLORS[mat], label=f'{mat} LR', markersize=5)
    ax.plot(thetas, grl, f'{MAT_MARKERS[mat]}--', color=MAT_COLORS[mat], label=f'{mat} RL', markersize=4, alpha=0.5)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|\Gamma|$ (linear)')
ax.set_title('(a) Magnitude Overlay'); ax.legend(fontsize=6, ncol=2); ax.grid(True, alpha=0.3)

ax = axes[1]
for mat in MATERIALS:
    dev = [20*np.log10(np.mean(np.abs(gamma[mat][t]['Gamma_LR_single'])) /
            max(np.mean(np.abs(gamma[mat][t]['Gamma_RL_single'])), 1e-10)) for t in thetas]
    ax.plot(thetas, dev, f'{MAT_MARKERS[mat]}-', color=MAT_COLORS[mat], label=MAT_LABELS[mat], markersize=5)
ax.axhline(0, color='gray', ls=':', lw=1)
ax.set_xlabel(r'$\theta_i$ [deg]'); ax.set_ylabel(r'$|\Gamma_{LR}|/|\Gamma_{RL}|$ [dB]')
ax.set_title('(b) Reciprocity Deviation (ideal = 0 dB)')
ax.legend(); ax.grid(True, alpha=0.3)

fig6.tight_layout()
fig6.savefig(OUTPUT / "fig6_reciprocity.png", dpi=150, bbox_inches='tight')
print("  [6/6] fig6_reciprocity.png")


# ================================================================
# FINAL NUMERICAL SUMMARY
# ================================================================

print("\n" + "=" * 65)
print("  FINAL NUMERICAL SUMMARY (Patch-Stage, Band-Averaged, M3-Corrected)")
print("=" * 65)

for mat in MATERIALS:
    print(f"\n  ━━━ {mat.upper()} ━━━")
    print(f"  {'θ_i':>5s} | {'|Γ_X|':>7s} | {'|Γ_C_cor|':>9s} | {'XPD':>7s} | {'|R_TE|':>7s} | {'|R_TM|':>7s}")
    print("  " + "-" * 58)
    for t in thetas:
        gx = np.mean(np.abs(gamma[mat][t]['Gamma_X']))
        gc = np.mean(np.abs(gamma[mat][t]['Gamma_C_corr']))
        xpd = 20*np.log10(gx/gc) if gc > 1e-10 else float('inf')
        rte = np.mean(np.abs(gamma[mat][t]['R_TE']))
        rtm = np.mean(np.abs(gamma[mat][t]['R_TM']))
        print(f"  {t:5.0f}° | {gx:7.4f} | {gc:9.4f} | {xpd:5.1f} dB | {rte:7.4f} | {rtm:7.4f}")

print("\n" + "=" * 65)
print(f"  Pipeline complete. All outputs in {OUTPUT}")
print("=" * 65)
