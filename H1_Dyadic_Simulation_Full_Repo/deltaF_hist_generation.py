import numpy as np
import matplotlib.pyplot as plt

# === STEP 1: Load or simulate your Delta_F data ===
# Option A: Load your real data (uncomment and adjust path)
# delta_f = np.load('your_large_n_delta_f.npy')          # or pd.read_csv(...)
# delta_f = delta_f.flatten()[:1000000]                  # subsample if too big

# Option B: Synthetic placeholder matching your stats (use this now, replace later)
np.random.seed(42)
n_points = 800000
# Bulk: lognormal around median 0.0099, std ~0.0049 → approximate log params
log_mean = np.log(0.0099)
log_std = 0.55
bulk = np.exp(np.random.normal(log_mean, log_std, int(n_points * 0.954)))
# Tail: 4.6% uniform low values
tail_frac = 0.046
tail_points = int(n_points * tail_frac)
tail = np.random.uniform(3e-4, 1.5e-3, tail_points)  # low tail
delta_f = np.concatenate([bulk, tail])
np.random.shuffle(delta_f)
delta_f = np.clip(delta_f, 1e-5, 0.15)  # realistic bounds

# Quick stats check (should ≈ your reported)
print(f"Median: {np.median(delta_f):.4f}")
print(f"Std: {np.std(delta_f):.4f}")
print(f"Fraction ≤ 0.0015: {np.mean(delta_f <= 0.0015)*100:.2f}%")

# === STEP 2: Plot ===
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(delta_f, bins=250, density=True, color='steelblue', alpha=0.85,
        histtype='stepfilled', edgecolor='none')

# Log scale for tail visibility
ax.set_xscale('log')
ax.set_xlim(1e-4, 0.1)
ax.set_ylim(0, None)  # auto

# Highlight resonant core
ax.axvline(0.0015, color='firebrick', linestyle='--', lw=1.8, alpha=0.9,
           label=r'$\Delta F \leq 0.0015$')
tail_pct = np.mean(delta_f <= 0.0015) * 100
ax.text(0.0018, ax.get_ylim()[1]*0.75,
        f'φ_R ≈ {tail_pct:.2f}%\nof realizations\n(invariant across scales)',
        color='firebrick', fontsize=11, fontweight='bold',
        bbox=dict(facecolor='white', alpha=0.85, edgecolor='firebrick', boxstyle='round,pad=0.4'))

ax.set_xlabel(r'$\Delta F$ (log scale)', fontsize=12)
ax.set_ylabel('Density', fontsize=12)
ax.set_title('Distribution of Surprise Minimization (ΔF) in Large Collectives\n'
             '(example from n ≈ 10⁷ dyads)', fontsize=13)
ax.grid(True, which="both", ls="--", alpha=0.3)
ax.legend(fontsize=11, loc='upper right')

plt.tight_layout()
plt.savefig('deltaF_hist_example.pdf', format='pdf', bbox_inches='tight', dpi=300)
plt.show()  # or plt.close() if batch
