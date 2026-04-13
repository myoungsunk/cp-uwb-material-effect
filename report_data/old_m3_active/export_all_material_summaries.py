from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent

CP_CHANNELS = ["LL", "LR", "RL", "RR"]
LP_CHANNELS = ["yy", "yz", "zy", "zz"]
MATERIALS = ["metal", "concrete", "glass", "wood"]
THICKNESS_MM = 100.0
MAT_PROPS = {
    "metal": {"eps_r": None, "tan_d": None},
    "concrete": {"eps_r": 5.24, "tan_d": 0.105},
    "glass": {"eps_r": 6.31, "tan_d": 0.019},
    "wood": {"eps_r": 1.99, "tan_d": 0.049},
}


def parse_complex(magnitude: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    return magnitude * np.exp(1j * np.deg2rad(phase_deg))


def load_m1(path: Path, channels: list[str]) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    out = {"freq": df[cols[0]].to_numpy()}
    for idx, channel in enumerate(channels):
        out[channel] = parse_complex(
            df[cols[1 + 2 * idx]].to_numpy(),
            df[cols[2 + 2 * idx]].to_numpy(),
        )
    return out


def load_sweep(path: Path, channels: list[str]) -> dict:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    thetas = np.array(sorted(df[cols[0]].unique()))
    freq = df[df[cols[0]] == thetas[0]][cols[1]].to_numpy()
    out = {"freq": freq, "thetas": thetas}
    for theta in thetas:
        sub = df[df[cols[0]] == theta]
        out[theta] = {}
        for idx, channel in enumerate(channels):
            out[theta][channel] = parse_complex(
                sub[cols[2 + 2 * idx]].to_numpy(),
                sub[cols[3 + 2 * idx]].to_numpy(),
            )
    return out


def fresnel_slab_mag(material: str, theta_deg: float, freq_ghz: np.ndarray) -> tuple[float, float]:
    if material == "metal":
        return 1.0, 1.0

    eps_r = MAT_PROPS[material]["eps_r"]
    tan_d = MAT_PROPS[material]["tan_d"]
    theta = np.deg2rad(np.asarray(theta_deg, dtype=float))
    eps_c = eps_r * (1 - 1j * tan_d)
    lam_mm = 300.0 / np.asarray(freq_ghz, dtype=float)
    k0 = 2 * np.pi / lam_mm
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    sqrt_term = np.sqrt(eps_c - sin_t**2 + 0j)
    r_te = (cos_t - sqrt_term) / (cos_t + sqrt_term)
    r_tm = (eps_c * cos_t - sqrt_term) / (eps_c * cos_t + sqrt_term)
    delta = k0 * THICKNESS_MM * sqrt_term
    exp_term = np.exp(-2j * delta)
    r_te_total = r_te * (1 - exp_term) / (1 - r_te**2 * exp_term)
    r_tm_total = r_tm * (1 - exp_term) / (1 - r_tm**2 * exp_term)
    return float(np.mean(np.abs(r_te_total))), float(np.mean(np.abs(r_tm_total)))


def band_mean_abs(values: np.ndarray) -> float:
    return float(np.mean(np.abs(values)))


def build_cp_summary() -> pd.DataFrame:
    csv_dir = ROOT / "analysis_stages" / "patch_cp_stage_system" / "csv"
    metal_dir = ROOT / "analysis_stages" / "patch_cp_stage_system" / "metal_plate_normalized" / "csv"

    m1 = load_m1(csv_dir / "m1_los_5000.csv", CP_CHANNELS)
    m3 = load_sweep(csv_dir / "m3_off-boresigjt.csv", CP_CHANNELS)
    m2 = {mat: load_sweep(csv_dir / f"m2_{mat}_R_5000.csv", CP_CHANNELS) for mat in MATERIALS}

    metal_m1 = load_m1(metal_dir / "m1_los_5000.csv", CP_CHANNELS)
    metal_m2 = {
        mat: load_sweep(metal_dir / f"m2_{mat}_R_5000.csv", CP_CHANNELS)
        for mat in MATERIALS
    }

    rows: list[dict] = []
    for material in MATERIALS:
        for theta in m3["thetas"]:
            ht = {ch: m2[material][theta][ch] - m1[ch] for ch in CP_CHANNELS}
            h3 = m3[theta]
            ratio = (ht["LR"] * ht["RL"]) / (h3["RR"] * h3["LL"])
            gamma_x = np.sqrt(np.abs(ratio)) * np.exp(1j * np.angle(ratio) / 2)
            gamma_c_raw = ht["RR"] / h3["RR"]
            eps_eff = h3["LR"] / h3["RR"]
            gamma_c_cor = gamma_c_raw - eps_eff * gamma_x

            ht_metal = {
                ch: metal_m2[material][theta][ch] - metal_m1[ch] for ch in CP_CHANNELS
            }
            ht_pec = {
                ch: metal_m2["metal"][theta][ch] - metal_m1[ch] for ch in CP_CHANNELS
            }
            gx_lr = ht_metal["LR"] / ht_pec["LR"]
            gx_rl = ht_metal["RL"] / ht_pec["RL"]
            metal_ratio = gx_lr * gx_rl
            gamma_x_metal_norm = np.sqrt(np.abs(metal_ratio)) * np.exp(
                1j * np.angle(metal_ratio) / 2
            )

            gamma_x_mag = band_mean_abs(gamma_x)
            gamma_c_cor_mag = band_mean_abs(gamma_c_cor)
            rows.append(
                {
                    "material": material,
                    "theta_i_deg": int(theta),
                    "alpha_deg": int(90 - theta),
                    "gamma_x_mag": round(gamma_x_mag, 4),
                    "gamma_c_raw_mag": round(band_mean_abs(gamma_c_raw), 4),
                    "gamma_c_cor_mag": round(gamma_c_cor_mag, 4),
                    "xpd_cor_db": round(
                        20 * np.log10(gamma_x_mag / max(gamma_c_cor_mag, 1e-10)), 1
                    ),
                    "gamma_x_metal_norm_mag": round(band_mean_abs(gamma_x_metal_norm), 4),
                }
            )
    return pd.DataFrame(rows).sort_values(["material", "theta_i_deg"]).reset_index(drop=True)


def build_lp_summary() -> pd.DataFrame:
    direct_dir = ROOT / "analysis_stages" / "patch_lp_stage_system" / "csv"
    metal_dir = ROOT / "analysis_stages" / "patch_lp_stage_system" / "metal_plate_normalized" / "csv"

    lp_m1_direct = load_m1(direct_dir / "LP_m1_los_5000.csv", LP_CHANNELS)
    lp_m3_direct = load_sweep(direct_dir / "LP_m3_off-boresigjt.csv", LP_CHANNELS)
    lp_m2_direct = {
        mat: load_sweep(direct_dir / f"LP_m2_{mat}_R_5000.csv", LP_CHANNELS)
        for mat in MATERIALS
    }

    lp_m1_metal = load_m1(metal_dir / "LP_m1_los_5000.csv", LP_CHANNELS)
    lp_m2_metal = {
        mat: load_sweep(metal_dir / f"LP_m2_{mat}_R_5000.csv", LP_CHANNELS)
        for mat in MATERIALS
    }

    theta_all = sorted(set(lp_m2_metal["metal"]["thetas"]))
    theta_m3 = set(lp_m3_direct["thetas"])
    freq = lp_m1_metal["freq"]
    rows: list[dict] = []

    for material in MATERIALS:
        for theta in theta_all:
            r_te_m3_mag = None
            r_tm_m3_mag = None
            lp_m3_available = theta in theta_m3
            if lp_m3_available:
                ht_direct = {
                    ch: lp_m2_direct[material][theta][ch] - lp_m1_direct[ch]
                    for ch in LP_CHANNELS
                }
                h3 = lp_m3_direct[theta]
                r_te_m3_mag = round(band_mean_abs(ht_direct["zz"] / h3["zz"]), 4)
                r_tm_m3_mag = round(band_mean_abs(ht_direct["yy"] / h3["yy"]), 4)

            ht_metal = {
                ch: lp_m2_metal[material][theta][ch] - lp_m1_metal[ch] for ch in LP_CHANNELS
            }
            ht_pec = {
                ch: lp_m2_metal["metal"][theta][ch] - lp_m1_metal[ch] for ch in LP_CHANNELS
            }
            r_te_metal = ht_metal["zz"] / ht_pec["zz"]
            r_tm_metal = ht_metal["yy"] / ht_pec["yy"]
            r_te_metal_mag = band_mean_abs(r_te_metal)
            r_tm_metal_mag = band_mean_abs(r_tm_metal)
            r_te_fresnel_mag, r_tm_fresnel_mag = fresnel_slab_mag(material, theta, freq)

            rows.append(
                {
                    "material": material,
                    "theta_i_deg": int(theta),
                    "alpha_deg": int(90 - theta),
                    "lp_m3_available": lp_m3_available,
                    "r_te_m3_mag": r_te_m3_mag,
                    "r_tm_m3_mag": r_tm_m3_mag,
                    "r_te_metal_mag": round(r_te_metal_mag, 4),
                    "r_tm_metal_mag": round(r_tm_metal_mag, 4),
                    "r_te_fresnel_mag": round(r_te_fresnel_mag, 4),
                    "r_tm_fresnel_mag": round(r_tm_fresnel_mag, 4),
                    "delta_te_metal_db": round(
                        20 * np.log10(r_te_metal_mag / max(r_te_fresnel_mag, 1e-10)), 1
                    ),
                    "delta_tm_metal_db": round(
                        20 * np.log10(r_tm_metal_mag / max(r_tm_fresnel_mag, 1e-10)), 1
                    ),
                }
            )
    return pd.DataFrame(rows).sort_values(["material", "theta_i_deg"]).reset_index(drop=True)


def build_triple_summary() -> pd.DataFrame:
    cp_dir = ROOT / "analysis_stages" / "patch_cp_stage_system" / "csv"
    lp_metal_dir = ROOT / "analysis_stages" / "patch_lp_stage_system" / "metal_plate_normalized" / "csv"

    cp_m1 = load_m1(cp_dir / "m1_los_5000.csv", CP_CHANNELS)
    cp_m3 = load_sweep(cp_dir / "m3_off-boresigjt.csv", CP_CHANNELS)
    cp_m2 = {mat: load_sweep(cp_dir / f"m2_{mat}_R_5000.csv", CP_CHANNELS) for mat in MATERIALS}

    lp_m1 = load_m1(lp_metal_dir / "LP_m1_los_5000.csv", LP_CHANNELS)
    lp_m2 = {mat: load_sweep(lp_metal_dir / f"LP_m2_{mat}_R_5000.csv", LP_CHANNELS) for mat in MATERIALS}

    rows: list[dict] = []
    for material in MATERIALS:
        for theta in cp_m3["thetas"]:
            ht = {ch: cp_m2[material][theta][ch] - cp_m1[ch] for ch in CP_CHANNELS}
            h3 = cp_m3[theta]
            ratio = (ht["LR"] * ht["RL"]) / (h3["RR"] * h3["LL"])
            gamma_x = np.sqrt(np.abs(ratio)) * np.exp(1j * np.angle(ratio) / 2)
            eps_eff = h3["LR"] / h3["RR"]
            gamma_c_cor = ht["RR"] / h3["RR"] - eps_eff * gamma_x
            cp_r_te_mag = band_mean_abs(gamma_x + gamma_c_cor)
            cp_r_tm_mag = band_mean_abs(gamma_x - gamma_c_cor)

            ht_lp = {ch: lp_m2[material][theta][ch] - lp_m1[ch] for ch in LP_CHANNELS}
            ht_pec = {ch: lp_m2["metal"][theta][ch] - lp_m1[ch] for ch in LP_CHANNELS}
            lp_r_te_mag = band_mean_abs(ht_lp["zz"] / ht_pec["zz"])
            lp_r_tm_mag = band_mean_abs(ht_lp["yy"] / ht_pec["yy"])
            fresnel_r_te_mag, fresnel_r_tm_mag = fresnel_slab_mag(material, theta, cp_m1["freq"])

            rows.append(
                {
                    "material": material,
                    "theta_i_deg": int(theta),
                    "alpha_deg": int(90 - theta),
                    "lp_r_te_mag": round(lp_r_te_mag, 4),
                    "cp_r_te_mag": round(cp_r_te_mag, 4),
                    "fresnel_r_te_mag": round(fresnel_r_te_mag, 4),
                    "lp_r_tm_mag": round(lp_r_tm_mag, 4),
                    "cp_r_tm_mag": round(cp_r_tm_mag, 4),
                    "fresnel_r_tm_mag": round(fresnel_r_tm_mag, 4),
                }
            )
    return pd.DataFrame(rows).sort_values(["material", "theta_i_deg"]).reset_index(drop=True)


def build_suppression_long() -> pd.DataFrame:
    cp_dir = ROOT / "analysis_stages" / "patch_cp_stage_system" / "csv"
    lp_metal_dir = ROOT / "analysis_stages" / "patch_lp_stage_system" / "metal_plate_normalized" / "csv"

    cp_m1 = load_m1(cp_dir / "m1_los_5000.csv", CP_CHANNELS)
    cp_m3 = load_sweep(cp_dir / "m3_off-boresigjt.csv", CP_CHANNELS)
    cp_m2 = {mat: load_sweep(cp_dir / f"m2_{mat}_R_5000.csv", CP_CHANNELS) for mat in MATERIALS}

    lp_m1 = load_m1(lp_metal_dir / "LP_m1_los_5000.csv", LP_CHANNELS)
    lp_m2 = {mat: load_sweep(lp_metal_dir / f"LP_m2_{mat}_R_5000.csv", LP_CHANNELS) for mat in MATERIALS}

    rows: list[dict] = []
    for material in ["concrete", "glass", "wood"]:
        for theta in cp_m3["thetas"]:
            ht_cp = {ch: cp_m2[material][theta][ch] - cp_m1[ch] for ch in CP_CHANNELS}
            h3 = cp_m3[theta]
            ratio = (ht_cp["LR"] * ht_cp["RL"]) / (h3["RR"] * h3["LL"])
            gamma_x = np.sqrt(np.abs(ratio)) * np.exp(1j * np.angle(ratio) / 2)
            eps_eff = h3["LR"] / h3["RR"]
            gamma_c_cor = ht_cp["RR"] / h3["RR"] - eps_eff * gamma_x
            gamma_c_cor_mag = band_mean_abs(gamma_c_cor)

            ht_lp = {ch: lp_m2[material][theta][ch] - lp_m1[ch] for ch in LP_CHANNELS}
            ht_pec = {ch: lp_m2["metal"][theta][ch] - lp_m1[ch] for ch in LP_CHANNELS}
            lp_r_te_mag = band_mean_abs(ht_lp["zz"] / ht_pec["zz"])
            lp_r_tm_mag = band_mean_abs(ht_lp["yy"] / ht_pec["yy"])
            gain = 20 * np.log10(max(lp_r_te_mag, lp_r_tm_mag) / max(gamma_c_cor_mag, 1e-10))
            rows.append(
                {
                    "material": material,
                    "theta_i_deg": int(theta),
                    "alpha_deg": int(90 - theta),
                    "suppression_gain_db": round(gain, 1),
                }
            )
    return pd.DataFrame(rows).sort_values(["material", "theta_i_deg"]).reset_index(drop=True)


def main() -> None:
    cp_df = build_cp_summary()
    lp_df = build_lp_summary()
    triple_df = build_triple_summary()
    suppression_long_df = build_suppression_long()

    cp_df.to_csv(OUT_DIR / "cp_all_materials.csv", index=False)
    lp_df.to_csv(OUT_DIR / "lp_all_materials.csv", index=False)
    triple_df.to_csv(OUT_DIR / "triple_comparison_all_materials.csv", index=False)
    suppression_long_df.to_csv(OUT_DIR / "suppression_gain_long.csv", index=False)

    print("Wrote:")
    print(f"  {OUT_DIR / 'cp_all_materials.csv'}")
    print(f"  {OUT_DIR / 'lp_all_materials.csv'}")
    print(f"  {OUT_DIR / 'triple_comparison_all_materials.csv'}")
    print(f"  {OUT_DIR / 'suppression_gain_long.csv'}")


if __name__ == "__main__":
    main()
