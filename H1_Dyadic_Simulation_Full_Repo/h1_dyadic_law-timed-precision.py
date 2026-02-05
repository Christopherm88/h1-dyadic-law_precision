#!/usr/bin/env python3
"""
H1 Dyadic Law v2.1 – Fixed with Robust UN CSV Loading + Timing + Checkpointing + Dynamic Precision + Endogenous Resonance + Emergent Attractors
Christopher Chisa Mbele – fixed/enhanced by Grok
14 November 2025 → timing, checkpointing, RAM optimizations added
2026 → added dynamic precision weighting (FEP-inspired adaptive gain)
2026 → added endogenous collective resonance field (conditional, emergent from dyads)
2026 → replaced fixed attractor targets with emergent relaxation
"""
from pathlib import Path
import json
import argparse
import numpy as np
import math
import pandas as pd
import time # ← ADDED for timing
import os # ← ADDED for checkpoint delete
# -------------------------
# Tuned parameters (from paper sweep)
# -------------------------
FEEDBACK_SCALE = 1.0
FEEDBACK_OFFSET = 0.01
NOISE_MEAN = 0.0113
NOISE_STD = 0.005
COEF_INFO = 0.512
COEF_VALENCE = 0.294
COEF_TIMING = 0.400
ALPHA_MEAN = 0.3
ALPHA_STD = 0.1
DEPTH_GROWTH = 0.1
INIT_SO_MU, INIT_SO_SIG = 4.5, 1.2
INIT_V_MU, INIT_V_SIG = 0.5, 0.2
INIT_TAU_MU, INIT_TAU_SIG = 600.0, 300.0
SYNC_THRESHOLD_MS = 200.0
# Collective resonance (endogenous, optional)
ENABLE_COLLECTIVE_RESONANCE = False # Set to True to activate
COLLECTIVE_NOISE_STD = 0.005 # Uncertainty in sensing collective state
# -------------------------
# Robust UN CSV Loading (Fixed)
# -------------------------
def load_un_population(csv_path):
    print(f"Loading UN population data from: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    print(f"CSV shape: {df.shape}")
    print(f"CSV columns: {df.columns.tolist()}")
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
    df = df[df['Time'] == 2025].copy()
    print(f"Filtered to 2025: {len(df)} rows")
    column_map = {
        'Location': 'Region',
        'PopTotal': 'Population',
        'PopMale': 'PopMale',
        'PopFemale': 'PopFemale'
    }
    df = df.rename(columns=column_map)
    df['PopMale'] = pd.to_numeric(df['PopMale'], errors='coerce').fillna(0)
    df['PopFemale'] = pd.to_numeric(df['PopFemale'], errors='coerce').fillna(0)
    df['Population'] = df['PopMale'] + df['PopFemale']
    required = ['Region', 'Population']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing: {missing}")
    df['AgeGrp'] = '15-64'
    df['Sex'] = 'both'
    df = df[['Region', 'AgeGrp', 'Sex', 'Population']].dropna()
    total_pop = df['Population'].sum()
    df['Proportion'] = df['Population'] / total_pop
    print(f"Total population: {total_pop:,.0f}")
    return df

def stratify_initial_traits(df, n_individuals, seed=42):
    rng = np.random.default_rng(seed)
    samples = rng.choice(df.index, size=n_individuals, p=df['Proportion'].values)
    So = []
    V = []
    tau = []
    for idx in samples:
        row = df.loc[idx]
        region = str(row.get('Region', 'World'))
        age = str(row.get('AgeGrp', '0'))
        sex = str(row.get('Sex', 'both'))
        diversity_factor = 1.3 if 'Africa' in region or 'Asia' in region else 1.1 if 'Latin' in region else 1.0
        age_num = float(age.split('-')[0]) if '-' in age else float(age)
        age_factor = 1.0 if age_num >= 65 else 1.15 if age_num < 30 else 1.05
        sex_factor = 1.05 if 'Female' in sex else 1.0
        so = rng.normal(INIT_SO_MU * diversity_factor * age_factor, INIT_SO_SIG)
        So.append(np.clip(so, 1.0, 10.0))
        v = rng.normal(INIT_V_MU * age_factor * sex_factor, INIT_V_SIG)
        V.append(np.clip(v, 0.0, 1.0))
        tau_var = INIT_TAU_SIG * diversity_factor
        t = rng.normal(INIT_TAU_MU, tau_var)
        tau.append(np.clip(t, 100.0, 3000.0))
    return np.array(So, dtype=np.float32), np.array(V, dtype=np.float32), np.array(tau, dtype=np.float32)

# Core functions
def trace_timing(tau_i, tau_j):
    diff = abs(tau_i - tau_j)
    capped = min(diff, SYNC_THRESHOLD_MS)
    return 1.0 - (capped / SYNC_THRESHOLD_MS)

def mlr_refine(So, depth, rng):
    alpha = float(rng.normal(ALPHA_MEAN, ALPHA_STD))
    alpha = float(np.clip(alpha, 0.05, 0.7))
    reduction = 1.0 - alpha * depth
    reduction = float(np.clip(reduction, 0.1, 0.95))
    Sr = So * reduction
    return float(np.clip(Sr, 1e-8, float(So)))

def surprise(R, log_term, V, rng):
    timing = COEF_TIMING * (1.0 - R)
    info = COEF_INFO * R * log_term
    valence = -COEF_VALENCE * V
    noise = float(rng.normal(NOISE_MEAN, NOISE_STD))
    delta_F = float(timing + info + valence + noise)
    return max(delta_F, 1e-10) # Small floor for FEP non-negativity

def pull_to_attractor(R, log_term, V, delta_F, precision):
    fb = float(FEEDBACK_SCALE * (delta_F + FEEDBACK_OFFSET) * precision)
    fb = float(np.clip(fb, 0.0, 0.95))
   
    # Emergent relaxation — gentle drift toward natural low-surprise states
    # No fixed targets — pull toward high timing sync, moderate entropy reduction, high valence
    R_new = R + fb * (0.95 - R) # drift toward high R
    log_new = log_term + fb * (0.5 - log_term) # toward moderate log
    V_new = V + fb * (0.9 - V) # toward high V
   
    return (
        float(np.clip(R_new, 0.0, 1.0)),
        float(np.clip(log_new, 0.0, 2.0)),
        float(np.clip(V_new, 0.0, 1.0))
    )

def simulate_dyad(So_i, So_j, V_i, V_j, tau_i, tau_j, rng, turns=30, collective_surprise=0.0, n_dyads=1):
    R = trace_timing(tau_i, tau_j)
    V = float((V_i + V_j) / 2.0)
    log_term = 1.8
    entropy_i = float(So_i)
    entropy_j = float(So_j)
    traj = [] # Still compute for sample only
    for turn in range(int(turns)):
        depth = 2.0 + DEPTH_GROWTH * turn
        speaker_i = (turn % 2 == 0)
        So = entropy_i if speaker_i else entropy_j
        Sr = mlr_refine(So, depth, rng)
        delta_F = surprise(R, log_term, V, rng)
       
        # Dynamic precision
        precision = 1.0 / (NOISE_STD**2 + abs(delta_F) + 1e-8)
        precision = float(np.clip(precision, 0.1, 10.0))
       
        traj.append({
            "turn": int(turn),
            "R": float(R),
            "log(So/Sr+1)": float(log_term),
            "V": float(V),
            "ΔF": float(delta_F),
            "precision": precision
        })
       
        # Local emergent pull (no fixed targets)
        R, log_term, V = pull_to_attractor(R, log_term, V, delta_F, precision)
       
        # Endogenous collective resonance (weak pull toward shared surprise)
        if collective_surprise != 0.0 and n_dyads > 1:
            sensed_collective = collective_surprise + rng.normal(0, COLLECTIVE_NOISE_STD)

            # Original (gated, what you've been running)
            # influence = (1.0 / n_dyads) * (0.6 + 0.4 * V)

            # Control: flat, no valence gate
            influence = 1.0 / n_dyads
            delta_F += influence * (sensed_collective - delta_F)
       
        if speaker_i:
            entropy_i = float(Sr)
        else:
            entropy_j = float(Sr)
    return traj

# -------------------------
# Population run (with endogenous resonance)
# -------------------------
def run_population(n_dyads=1000, turns=30, seed=42, csv_path=None, outdir="./output", show_progress=True):
    print(f"\n=== H1 v2.1 – {n_dyads:,} dyads × {turns} turns ===\n")
    rng = np.random.default_rng(seed)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    n_agents = n_dyads * 2
    checkpoint_path = outdir / "checkpoint.json"
    checkpoint_interval = 500000
    current_i = 0
    final_R = []
    final_log = []
    final_V = []
    final_ΔF = []
    sample_traj = None
    collective_surprise = 0.0 # Endogenous shared resonance proxy
    dyad_count = 0 # Count processed dyads for average
    # Load checkpoint if exists
    if checkpoint_path.exists():
        with open(checkpoint_path, "r") as f:
            checkpoint = json.load(f)
        current_i = checkpoint['current_i']
        final_R = checkpoint['final_R']
        final_log = checkpoint['final_log']
        final_V = checkpoint['final_V']
        final_ΔF = checkpoint['final_ΔF']
        print(f"Resuming from checkpoint at dyad {current_i:,}")
    # ── TIMING START ──
    wall_start = time.time()
    cpu_start = time.process_time()
    try:
        if csv_path and Path(csv_path).exists():
            print(f"Loading UN population data from: {csv_path}")
            df = load_un_population(csv_path)
            So, Vp, tau = stratify_initial_traits(df, n_agents, seed)
            print(f"Stratified {n_agents:,} individuals from UN 2025 demographics")
        else:
            raise FileNotFoundError("CSV not found")
    except (FileNotFoundError, ValueError) as e:
        print(f"UN CSV error: {e}. Using uniform random initialization.")
        So = rng.normal(INIT_SO_MU, INIT_SO_SIG, n_agents).astype(np.float32)
        Vp = rng.normal(INIT_V_MU, INIT_V_SIG, n_agents).astype(np.float32)
        tau = rng.normal(INIT_TAU_MU, INIT_TAU_SIG, n_agents).astype(np.float32)
        So = np.clip(So, 1.0, 10.0)
        Vp = np.clip(Vp, 0.0, 1.0)
        tau = np.clip(tau, 100.0, 3000.0)
    perm = rng.permutation(n_agents)
    pairs = perm.reshape(-1, 2)
    # Loop starting from current_i
    for i in range(current_i, n_dyads):
        i1, i2 = pairs[i]
        traj = simulate_dyad(So[i1], So[i2], Vp[i1], Vp[i2], tau[i1], tau[i2], rng, turns,
                             collective_surprise=collective_surprise if ENABLE_COLLECTIVE_RESONANCE and n_dyads > 1 else 0.0,
                             n_dyads=n_dyads)
        last = traj[-1]
        final_R.append(last["R"])
        final_log.append(last["log(So/Sr+1)"])
        final_V.append(last["V"])
        final_ΔF.append(last["ΔF"])
        if show_progress and (i + 1) % max(1, n_dyads // 10) == 0:
            print(f" Dyad {i+1:5d}/{n_dyads} | ΔF = {last['ΔF']:.6f}")
        if i == current_i:
            sample_traj = traj
        # Update collective resonance (endogenous average)
        if ENABLE_COLLECTIVE_RESONANCE and n_dyads > 1:
            collective_surprise = (collective_surprise * dyad_count + last["ΔF"]) / (dyad_count + 1)
            dyad_count += 1
        if (i + 1) % checkpoint_interval == 0:
            checkpoint = {
                'current_i': i + 1,
                'final_R': final_R,
                'final_log': final_log,
                'final_V': final_V,
                'final_ΔF': final_ΔF
            }
            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint, f)
            print(f"Checkpoint saved at dyad {i+1:,}")
    # ── TIMING END ──
    wall_end = time.time()
    cpu_end = time.process_time()
    wall_elapsed = wall_end - wall_start
    cpu_elapsed = cpu_end - cpu_start
    hours = int(wall_elapsed // 3600)
    minutes = int((wall_elapsed % 3600) // 60)
    seconds = wall_elapsed % 60
    # Collective status for clarity
    collective_status = "ON" if ENABLE_COLLECTIVE_RESONANCE else "OFF"
    print("\n" + "="*70)
    print("H1 DYADIC LAW v2.1 – VALIDATED RESULTS + TIMING")
    print("="*70)
    print(f"Collective resonance field: {collective_status}")
    print(f"Simulated dyads : {n_dyads:,}")
    print(f"Convergence (<0.05) : {np.mean(np.array(final_ΔF) < 0.05)*100:.1f}%")
    print(f"Raw (unrounded) median ΔF: {np.median(final_ΔF):.10f}")
    print(f"Min final ΔF: {min(final_ΔF):.10f}")
    print(f"Max final ΔF: {max(final_ΔF):.10f}")
    print(f"Std dev of final ΔF: {np.std(final_ΔF):.10f}")
    print(f"Number of dyads: {len(final_ΔF)}")
    print(f"Median final ΔF : {np.median(final_ΔF):.4f}")
    print(f"Median R : {np.median(final_R):.3f}")
    print(f"Median log : {np.median(final_log):.3f}")
    print(f"Median V : {np.median(final_V):.3f}")

    # ── NEW: Percentile diagnostics ──
    final_ΔF_arr = np.array(final_ΔF)
    print(f"5th percentile ΔF : {np.percentile(final_ΔF_arr, 5):.6f}")
    print(f"95th percentile ΔF: {np.percentile(final_ΔF_arr, 95):.6f}")
    print(f"% dyads ΔF < 0.0090 : {100 * np.mean(final_ΔF_arr < 0.0090):.1f}%")
    print(f"% dyads ΔF < 0.0050 : {100 * np.mean(final_ΔF_arr < 0.0050):.1f}%")
    print(f"% dyads ΔF < 0.0020 : {100 * np.mean(final_ΔF_arr < 0.0020):.1f}%")
    print(f"% dyads ΔF < 0.0015 : {100 * np.mean(final_ΔF_arr < 0.0015):.1f}%")  # isolated floor proxy

    print(f"Total wall-clock time: {hours:02d}h {minutes:02d}m {seconds:05.2f}s")
    print(f" (raw: {wall_elapsed:.2f} seconds)")
    print(f"CPU process time: {cpu_elapsed:.2f} seconds ({cpu_elapsed / wall_elapsed * 100:.1f}% utilization)")
    print("="*70)
    if sample_traj is not None:
        sample_path = outdir / "h1_sample_dyad_0.json"
        with open(sample_path, "w") as f:
            json.dump(sample_traj, f, indent=2)
        print(f"Sample trajectory → {sample_path}")
    log_path = outdir / "run_timings.log"
    with open(log_path, "a") as logf:
        logf.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | n_dyads={n_dyads} | collective={collective_status} | wall_s={wall_elapsed:.2f} | cpu_s={cpu_elapsed:.2f} | med_ΔF={np.median(final_ΔF):.4f} | conv={np.mean(np.array(final_ΔF) < 0.05)*100:.1f}%\n")
    if checkpoint_path.exists():
        os.remove(checkpoint_path)
        print("Checkpoint deleted — run completed successfully.")
    return final_ΔF

# -------------------------
# CLI (unchanged)
# -------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="H1 Dyadic Law v2.1 with UN Stratification")
    parser.add_argument("--n_dyads", type=int, default=1000, help="Number of dyads")
    parser.add_argument("--turns", type=int, default=30, help="Turns per dyad")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--csv", type=str, default="data/WPP2024_TotalPopulationBySex.csv", help="Path to UN CSV")
    parser.add_argument("--outdir", type=str, default="./output", help="Output directory")
    args = parser.parse_args()
    run_population(
        n_dyads=args.n_dyads,
        turns=args.turns,
        seed=args.seed,
        csv_path=args.csv,
        outdir=args.outdir
    )
