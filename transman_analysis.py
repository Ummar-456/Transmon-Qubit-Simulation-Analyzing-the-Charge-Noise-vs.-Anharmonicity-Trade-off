# ==============================================================================
# Transmon Qubit Simulation & Analysis
#
# This script simulates a superconducting transmon qubit by numerically solving
# its Hamiltonian. It performs a parameter sweep over the Ej/Ec ratio to
# analyze and visualize the core engineering trade-off between charge noise
# sensitivity (charge dispersion) and qubit anharmonicity.
#
# ==============================================================================

import numpy as np
import matplotlib.pyplot as plt
from qutip import Qobj, qdiags
import time

def simulate_transmon_properties(ej_ec_ratios, Ec, N, ng_sweep_points):
    """
    Simulates transmon properties over a range of Ej/Ec ratios.

    Args:
        ej_ec_ratios (array-like): Array of Ej/Ec values to sweep.
        Ec (float): Charging energy in GHz.
        N (int): Number of charge states to include around n=0.
        ng_sweep_points (int): Number of ng points to sweep for dispersion calculation.

    Returns:
        tuple: (qubit_frequencies, anharmonicities, charge_dispersions)
    """
    charge_states = np.arange(-N, N + 1)
    n_states = 2 * N + 1
    ng_values = np.linspace(0, 1, ng_sweep_points)

    qubit_frequencies = []
    anharmonicities = []
    charge_dispersions = []

    print("Starting parameter sweep...")
    start_time = time.time()

    # Outer loop: sweep Ej/Ec
    for ratio in ej_ec_ratios:
        Ej = ratio * Ec
        
        # --- 1. Calculate Anharmonicity (at ng=0 for simplicity) ---
        ng_fixed = 0.0
        charging_term = 4 * Ec * (charge_states - ng_fixed)**2
        H_c = qdiags(charging_term, 0)
        off_diagonal_elements = np.ones(n_states - 1)
        H_j_off_diagonals = -Ej / 2 * (qdiags(off_diagonal_elements, -1) + qdiags(off_diagonal_elements, 1))
        H = H_c + H_j_off_diagonals
        
        # Find the first 3 energy levels
        eigenvalues = H.eigenstates(eigvals=3)[0]
        freq_01 = eigenvalues[1] - eigenvalues[0]
        freq_12 = eigenvalues[2] - eigenvalues[1]
        anharmonicity = freq_12 - freq_01
        
        qubit_frequencies.append(freq_01)
        anharmonicities.append(anharmonicity)
        
        # --- 2. Calculate Charge Dispersion ---
        frequencies_for_ng_sweep = []
        # Inner loop: sweep ng
        for ng in ng_values:
            charging_term_ng = 4 * Ec * (charge_states - ng)**2
            H_c_ng = qdiags(charging_term_ng, 0)
            H_ng = H_c_ng + H_j_off_diagonals
            eigenvalues_ng = H_ng.eigenstates(eigvals=2)[0]
            freq_01_ng = eigenvalues_ng[1] - eigenvalues_ng[0]
            frequencies_for_ng_sweep.append(freq_01_ng)
        
        dispersion = np.max(frequencies_for_ng_sweep) - np.min(frequencies_for_ng_sweep)
        charge_dispersions.append(dispersion)
        
        print(f"  Ej/Ec = {ratio:5.1f} -> Freq = {freq_01:.2f} GHz | Anharmonicity = {anharmonicity*1000:.1f} MHz | Dispersion = {dispersion*1000:.4f} MHz")

    end_time = time.time()
    print(f"Parameter sweep finished in {end_time - start_time:.2f} seconds.")
    
    return qubit_frequencies, anharmonicities, charge_dispersions

def plot_results(ej_ec_ratios, Ec, freqs, alphas, disps):
    """Plots the final results in a 3-panel figure."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
    fig.suptitle("Transmon Qubit Design: Simulation & Analysis", fontsize=16)

    # Plot 1: Qubit Frequency vs. Ej/Ec
    ax1.plot(ej_ec_ratios, freqs, 'b-', label=r'Qubit Frequency ($f_{01}$)')
    ax1.set_ylabel("Frequency (GHz)")
    ax1.set_title("Qubit Frequency")
    ax1.legend()
    ax1.grid(True)

    # Plot 2: Anharmonicity vs. Ej/Ec
    ax2.plot(ej_ec_ratios, np.array(alphas) * 1000, 'r-', label=r'Anharmonicity ($\alpha$)')
    ax2.axhline(-Ec * 1000, color='gray', linestyle='--', label=f'Approximation: -Ec = {-Ec*1000:.0f} MHz')
    ax2.set_ylabel("Anharmonicity (MHz)")
    ax2.set_title("Anharmonicity (Cost of Noise Immunity)")
    ax2.legend()
    ax2.grid(True)
    
    # Plot 3: Charge Dispersion vs. Ej/Ec
    ax3.plot(ej_ec_ratios, np.array(disps) * 1000, 'g-', marker='.', markersize=5, label='Charge Dispersion')
    ax3.set_yscale('log')
    ax3.set_xlabel("$E_J/E_C$ Ratio")
    ax3.set_ylabel("Charge Dispersion (MHz) [log scale]")
    ax3.set_title("Charge Noise Sensitivity (Benefit of Transmon Regime)")
    ax3.legend()
    ax3.grid(True, which="both", ls="--")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show(block=True)


if __name__ == '__main__':
    # --- Simulation Parameters ---
    EC_PARAM = 0.3  # Charging energy in GHz
    HILBERT_SPACE_SIZE = 10 # Number of charge states to include (+/- N)
    NG_SWEEP_POINTS = 21 # Number of points for the ng sweep
    EJ_EC_RATIOS_TO_SWEEP = np.linspace(1, 100, 50)
    
    # --- Run Simulation and Plot ---
    frequencies, anharmonicities, dispersions = simulate_transmon_properties(
        EJ_EC_RATIOS_TO_SWEEP, EC_PARAM, HILBERT_SPACE_SIZE, NG_SWEEP_POINTS
    )
    
    plot_results(EJ_EC_RATIOS_TO_SWEEP, EC_PARAM, frequencies, anharmonicities, dispersions)
