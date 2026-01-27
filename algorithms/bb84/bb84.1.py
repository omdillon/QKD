import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, pauli_error, amplitude_damping_error, phase_damping_error
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Tuple, List

class EnhancedBB84Protocol:
    """
    Enhanced BB84 Quantum Key Distribution Protocol Simulation
    
    Features:
    - Configurable QBER (target artificial error rate)
    - Multiple realistic noise models (Depolarizing, Bit-flip, Phase-damping, Amplitude-damping)
    - Eavesdropper (Eve) simulation with variable interception rates
    - Comprehensive data visualization suite
    
    Attributes:
        n_qubits (int): Number of qubits to transmit
        interception_rate (float): Probability Eve intercepts a qubit [0.0-1.0]
        target_qber (float): Artificial QBER to inject (simulates channel imperfections)
        noise_type (str): Type of quantum noise model to apply
        noise_strength (float): Strength parameter for the noise model
    """

    def __init__(self, 
                 n_qubits: int = 100, 
                 interception_rate: float = 0.0,
                 target_qber: float = 0.0,
                 noise_type: str = 'none',
                 noise_strength: float = 0.01):
        """
        Initialize the enhanced BB84 simulation.
        
        Args:
            n_qubits: Total number of bits/qubits to transmit
            interception_rate: Eve's interception probability [0.0 = secure, 1.0 = full eavesdrop]
            target_qber: Artificial error rate to inject [0.0-1.0]
            noise_type: Quantum noise model ['none', 'depolarizing', 'bitflip', 'phaseflip', 
                                              'amplitude_damping', 'phase_damping']
            noise_strength: Noise parameter intensity [0.0-1.0]
        """
        self.n_qubits = n_qubits
        self.interception_rate = interception_rate
        self.target_qber = target_qber
        self.noise_type = noise_type
        self.noise_strength = noise_strength
        
        # Initialize backend with optional noise model
        self.backend_sim = self._configure_backend()
        
        # Protocol data storage
        self.alice_bits = []          # Alice's raw random bits (0 or 1)
        self.alice_bases = []         # Alice's bases (0=Z-basis, 1=X-basis)
        self.bob_bases = []           # Bob's bases (0=Z-basis, 1=X-basis)
        self.bob_results = []         # Bob's measurement results
        self.eve_presence = []        # Track which qubits Eve intercepted
        self.sifted_key_alice = []    # Alice's key after sifting
        self.sifted_key_bob = []      # Bob's key after sifting
        self.match_indices = []       # Indices where bases matched
        self.calculated_qber = 0.0    # Final calculated QBER
        
    def _configure_backend(self) -> AerSimulator:
        """
        Configure the Qiskit Aer backend with the specified noise model.
        
        Returns:
            AerSimulator with appropriate noise configuration
        """
        # Start with a clean noise model
        noise_model = NoiseModel()
        
        if self.noise_type == 'none':
            # No noise applied - ideal quantum channel
            return AerSimulator()
        
        elif self.noise_type == 'depolarizing':
            # Depolarizing noise: Qubit randomly flips to X, Y, Z with equal probability
            # Models white noise from all Pauli errors
            # param = probability that a Pauli error occurs (X, Y, or Z with equal weight)
            error = depolarizing_error(self.noise_strength, 1)
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            print(f"[Noise Model] Depolarizing channel with strength {self.noise_strength}")
            
        elif self.noise_type == 'bitflip':
            # Bit-flip (X) noise: Qubit flips from |0⟩ to |1⟩ and vice versa
            # Models polarization drift in fiber optic channels
            error = pauli_error([('X', self.noise_strength), ('I', 1 - self.noise_strength)])
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            print(f"[Noise Model] Bit-flip channel with strength {self.noise_strength}")
            
        elif self.noise_type == 'phaseflip':
            # Phase-flip (Z) noise: Relative phase changes between |0⟩ and |1⟩
            # Less critical for BB84 due to basis sifting, but included for completeness
            error = pauli_error([('Z', self.noise_strength), ('I', 1 - self.noise_strength)])
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            print(f"[Noise Model] Phase-flip channel with strength {self.noise_strength}")
            
        elif self.noise_type == 'amplitude_damping':
            # Amplitude damping: Models energy dissipation (photon loss)
            # Qubit loses energy and decays from |1⟩ to |0⟩
            # Critical for long-distance fiber optic QKD
            error = amplitude_damping_error(self.noise_strength)
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            print(f"[Noise Model] Amplitude damping with strength {self.noise_strength}")
            
        elif self.noise_type == 'phase_damping':
            # Phase damping: Loss of quantum coherence without energy loss
            # Converts pure states to mixed states
            error = phase_damping_error(self.noise_strength)
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            print(f"[Noise Model] Phase damping with strength {self.noise_strength}")
            
        return AerSimulator(noise_model=noise_model)

    def alicePreparation(self) -> List[QuantumCircuit]:
        """
        Alice generates random bits and bases, then prepares quantum states.
        
        BB84 Encoding:
        - Bit=0, Basis=Z(0): |0⟩ (computational basis)
        - Bit=1, Basis=Z(0): |1⟩ 
        - Bit=0, Basis=X(1): |+⟩ = (|0⟩ + |1⟩)/√2 (Hadamard basis)
        - Bit=1, Basis=X(1): |−⟩ = (|0⟩ - |1⟩)/√2
        
        Returns:
            List of QuantumCircuit objects representing the photon stream
        """
        print(f"\n{'='*60}")
        print(f"STEP 1: Alice prepares {self.n_qubits} qubits")
        print(f"{'='*60}")
        
        # Generate random bits and bases using quantum randomness simulation
        self.alice_bits = np.random.randint(2, size=self.n_qubits)
        self.alice_bases = np.random.randint(2, size=self.n_qubits)
        
        qubit_stream = []
        
        for i in range(self.n_qubits):
            # Create a single-qubit circuit (1 qubit, 1 classical bit)
            qc = QuantumCircuit(1, 1)
            
            # Step 1: Encode the bit value
            # If bit=1, apply X gate to flip |0⟩ → |1⟩
            if self.alice_bits[i] == 1:
                qc.x(0)
            
            # Step 2: Encode the basis choice
            # If basis=1 (X-basis), apply Hadamard gate to create superposition
            if self.alice_bases[i] == 1:
                qc.h(0)
            
            qubit_stream.append(qc)
        
        print(f"[SUCCESS] Encoded {self.n_qubits} qubits")
        print(f"  Sample bits:  {self.alice_bits[:10]}")
        print(f"  Sample bases: {self.alice_bases[:10]} (0=Z, 1=X)")
        
        return qubit_stream

    def quantumChannel(self, qubit_stream: List[QuantumCircuit]) -> List[QuantumCircuit]:
        """
        Simulate the quantum channel with eavesdropper (Eve) and noise.
        
        Eve's Attack Strategy (Intercept-Resend):
        1. Intercepts photon with probability `interception_rate`
        2. Randomly chooses a measurement basis (no knowledge of Alice's choice)
        3. Measures the qubit (collapses superposition)
        4. Prepares a fresh qubit in the measured state
        5. Resends to Bob
        
        This attack introduces errors due to basis mismatch, creating detectable QBER.
        
        Returns:
            List of QuantumCircuit objects after channel transmission
        """
        print(f"\n{'='*60}")
        print(f"STEP 2: Quantum Channel Transmission")
        print(f"{'='*60}")
        print(f"Eve interception rate: {self.interception_rate*100:.1f}%")
        print(f"Noise model: {self.noise_type} (strength: {self.noise_strength})")
        
        intercepted_stream = []
        self.eve_presence = [False] * self.n_qubits
        eve_count = 0
        
        for i, qc in enumerate(qubit_stream):
            # Determine if Eve intercepts this specific qubit
            if np.random.rand() < self.interception_rate:
                self.eve_presence[i] = True
                eve_count += 1
                
                # Eve chooses a random measurement basis (50% chance of matching Alice)
                eve_basis = np.random.randint(2)
                
                # Apply Eve's basis transformation
                if eve_basis == 1:
                    qc.h(0)  # Measure in X-basis
                
                # Eve performs measurement (collapses the quantum state)
                qc.measure(0, 0)
                
                # Execute the circuit to get Eve's measurement result
                instance = self.backend_sim.run(qc, shots=1, memory=True)
                result = instance.result().get_memory()[0]  # '0' or '1'
                
                # --- EVE RESENDS A FRESH QUBIT ---
                # Creates new circuit based on her measurement
                # This is the "no-cloning theorem" in action
                new_qc = QuantumCircuit(1, 1)
                
                if result == '1':
                    new_qc.x(0)  # Prepare |1⟩
                
                # Re-encode in the basis Eve used (she has no other information)
                if eve_basis == 1:
                    new_qc.h(0)  # Encode in X-basis
                
                intercepted_stream.append(new_qc)
            else:
                # Qubit passes through untouched by Eve
                intercepted_stream.append(qc)
        
        print(f"[SUCCESS] Eve intercepted {eve_count}/{self.n_qubits} qubits ({eve_count/self.n_qubits*100:.1f}%)")
        
        return intercepted_stream

    def bobMeasurement(self, incoming_stream: List[QuantumCircuit]):
        """
        Bob receives qubits and measures them using randomly chosen bases.
        
        Bob has no knowledge of:
        - Alice's bit values
        - Alice's basis choices
        - Whether Eve intercepted
        
        He simply chooses random bases and measures, then later compares bases with Alice.
        """
        print(f"\n{'='*60}")
        print(f"STEP 3: Bob measures incoming qubits")
        print(f"{'='*60}")
        
        # Bob generates his own random measurement bases
        self.bob_bases = np.random.randint(2, size=self.n_qubits)
        self.bob_results = []
        
        for i, qc in enumerate(incoming_stream):
            # Apply Bob's basis choice
            if self.bob_bases[i] == 1:
                qc.h(0)  # Measure in X-basis
            
            # Bob performs measurement
            qc.measure(0, 0)
            
            # Execute the circuit to get Bob's result
            instance = self.backend_sim.run(qc, shots=1, memory=True)
            measured_bit = int(instance.result().get_memory()[0])
            self.bob_results.append(measured_bit)
        
        print(f"[SUCCESS] Bob measured all {self.n_qubits} qubits")
        print(f"  Sample results: {self.bob_results[:10]}")
        print(f"  Sample bases:   {self.bob_bases[:10]} (0=Z, 1=X)")

    def injectArtificialErrors(self):
        """
        Inject additional artificial errors to achieve target QBER.
        
        This simulates imperfect detectors, timing jitter, and other classical errors
        that are independent of Eve's presence.
        
        Strategy:
        - Calculate how many errors are needed to reach target_qber
        - Randomly flip bits in Bob's results among the sifted key positions
        - Only apply to positions where bases matched (the sifted key)
        """
        if self.target_qber <= 0:
            return  # No artificial errors requested
        
        print(f"\n[Artificial Error Injection]")
        print(f"Target QBER: {self.target_qber*100:.2f}%")
        
        # Calculate current errors before injection
        current_errors = sum(1 for k in range(len(self.sifted_key_alice)) 
                            if self.sifted_key_alice[k] != self.sifted_key_bob[k])
        current_qber = current_errors / len(self.sifted_key_alice) if len(self.sifted_key_alice) > 0 else 0
        
        # Determine how many additional errors we need
        target_errors = int(self.target_qber * len(self.sifted_key_alice))
        additional_errors_needed = max(0, target_errors - current_errors)
        
        if additional_errors_needed > 0:
            # Identify positions that currently match (no error)
            matching_positions = [i for i in range(len(self.sifted_key_alice))
                                 if self.sifted_key_alice[i] == self.sifted_key_bob[i]]
            
            # Randomly select positions to flip
            if len(matching_positions) >= additional_errors_needed:
                positions_to_flip = np.random.choice(matching_positions, 
                                                     size=additional_errors_needed, 
                                                     replace=False)
                
                # Flip bits at selected positions
                for pos in positions_to_flip:
                    self.sifted_key_bob[pos] = 1 - self.sifted_key_bob[pos]  # Bit flip
                
                print(f"[SUCCESS] Injected {additional_errors_needed} artificial errors")
            else:
                print(f"[WARNING] Not enough matching positions to inject all errors")

    def postProcessing(self) -> Tuple[float, int, int]:
        """
        Sifting Phase and QBER Calculation.
        
        Classical Communication (Public Channel):
        1. Alice and Bob announce their basis choices (but NOT bit values)
        2. They discard all positions where bases didn't match
        3. The remaining bits form the "sifted key"
        4. They sacrifice a random subset to calculate QBER
        5. If QBER > 11%, they abort (eavesdropper detected)
        
        Returns:
            Tuple of (qber, total_sifted, errors)
        """
        print(f"\n{'='*60}")
        print(f"STEP 4: Sifting and QBER Calculation")
        print(f"{'='*60}")
        
        self.sifted_key_alice = []
        self.sifted_key_bob = []
        self.match_indices = []
        
        # Compare bases and keep only matching positions
        for i in range(self.n_qubits):
            if self.alice_bases[i] == self.bob_bases[i]:
                self.sifted_key_alice.append(self.alice_bits[i])
                self.sifted_key_bob.append(self.bob_results[i])
                self.match_indices.append(i)
        
        total_sifted = len(self.sifted_key_alice)
        
        if total_sifted == 0:
            print("[ERROR] No bases matched! (Statistically improbable with >50 qubits)")
            return 0.0, 0, 0
        
        # Inject artificial errors if target QBER is set
        self.injectArtificialErrors()
        
        # Calculate QBER: ratio of mismatched bits in sifted key
        errors = sum(1 for k in range(total_sifted) 
                    if self.sifted_key_alice[k] != self.sifted_key_bob[k])
        
        qber = errors / total_sifted
        self.calculated_qber = qber
        
        # Display results
        print(f"\n[Protocol Statistics]")
        print(f"  Total qubits sent:     {self.n_qubits}")
        print(f"  Basis match rate:      {total_sifted/self.n_qubits*100:.1f}% ({total_sifted}/{self.n_qubits})")
        print(f"  Sifted key length:     {total_sifted} bits")
        print(f"  Errors detected:       {errors}")
        print(f"  Calculated QBER:       {qber:.4f} ({qber*100:.2f}%)")
        
        # Security assessment
        SECURITY_THRESHOLD = 0.11  # 11% is the theoretical maximum for BB84
        print(f"\n[Security Analysis]")
        print(f"  Safety threshold:      {SECURITY_THRESHOLD*100:.0f}%")
        
        if qber > SECURITY_THRESHOLD:
            print(f"  Status:                INSECURE - QBER too high!")
            print(f"  Recommendation:        Abort key exchange. Possible eavesdropper detected.")
        else:
            print(f"  Status:                SECURE - QBER within safe limits")
            print(f"  Recommendation:        Proceed with privacy amplification & error correction.")
        
        return qber, total_sifted, errors

    def executeSim(self) -> Dict:
        """
        Execute the full BB84 protocol simulation.
        
        Returns:
            Dictionary containing all simulation results for analysis
        """
        qubits = self.alicePreparation()
        qubits = self.quantumChannel(qubits)
        self.bobMeasurement(qubits)
        qber, sifted_length, errors = self.postProcessing()
        
        # Return comprehensive results
        return {
            'qber': qber,
            'sifted_length': sifted_length,
            'errors': errors,
            'eve_interceptions': sum(self.eve_presence),
            'alice_bits': self.alice_bits,
            'alice_bases': self.alice_bases,
            'bob_bases': self.bob_bases,
            'bob_results': self.bob_results,
            'sifted_key_alice': self.sifted_key_alice,
            'sifted_key_bob': self.sifted_key_bob,
            'match_indices': self.match_indices
        }


# =============================================================================
# VISUALIZATION SUITE
# =============================================================================

class BB84Visualizer:
    """
    Comprehensive visualization suite for BB84 protocol analysis.
    """
    
    @staticmethod
    def plot_qber_vs_interception(n_trials: int = 20, n_qubits: int = 200):
        """
        Plot 1: QBER vs Eve's Interception Rate
        
        Demonstrates the theoretical 25% QBER limit when Eve intercepts 100%.
        This is the signature of quantum eavesdropping in BB84.
        """
        print("\n" + "="*60)
        print("VISUALIZATION 1: QBER vs Interception Rate")
        print("="*60)
        
        interception_rates = np.linspace(0, 1, 11)  # 0%, 10%, ..., 100%
        qber_values = []
        qber_std = []
        
        for rate in interception_rates:
            qbers = []
            for _ in range(n_trials):
                sim = EnhancedBB84Protocol(n_qubits=n_qubits, interception_rate=rate)
                result = sim.executeSim()
                qbers.append(result['qber'])
            
            qber_values.append(np.mean(qbers))
            qber_std.append(np.std(qbers))
        
        # Plot results
        plt.figure(figsize=(10, 6))
        plt.errorbar(interception_rates * 100, np.array(qber_values) * 100, 
                     yerr=np.array(qber_std) * 100, 
                     marker='o', capsize=5, linewidth=2, markersize=8,
                     label='Simulated QBER')
        
        # Theoretical line: QBER ≈ 0.25 * interception_rate
        theoretical = 0.25 * interception_rates * 100
        plt.plot(interception_rates * 100, theoretical, 'r--', 
                 linewidth=2, label='Theoretical (25% limit)')
        
        # Security threshold
        plt.axhline(y=11, color='orange', linestyle=':', linewidth=2, 
                    label='Security Threshold (11%)')
        
        plt.xlabel('Eve Interception Rate (%)', fontsize=12, fontweight='bold')
        plt.ylabel('Quantum Bit Error Rate - QBER (%)', fontsize=12, fontweight='bold')
        plt.title('BB84 Protocol: QBER vs Eavesdropper Interception Rate\n' + 
                  f'(Averaged over {n_trials} trials, {n_qubits} qubits each)',
                  fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=11)
        plt.tight_layout()
        plt.savefig('bb84_qber_vs_interception.png', dpi=300, bbox_inches='tight')
        print("[SUCCESS] Saved: bb84_qber_vs_interception.png")
        plt.show()
    
    @staticmethod
    def plot_basis_matching_distribution(n_simulations: int = 100, n_qubits: int = 100):
        """
        Plot 2: Sifted Key Length Distribution
        
        Shows the statistical distribution of basis matching (should be ~50% of n_qubits).
        """
        print("\n" + "="*60)
        print("VISUALIZATION 2: Sifted Key Length Distribution")
        print("="*60)
        
        sifted_lengths = []
        
        for _ in range(n_simulations):
            sim = EnhancedBB84Protocol(n_qubits=n_qubits, interception_rate=0.0)
            result = sim.executeSim()
            sifted_lengths.append(result['sifted_length'])
        
        plt.figure(figsize=(10, 6))
        plt.hist(sifted_lengths, bins=20, edgecolor='black', alpha=0.7, color='skyblue')
        
        # Theoretical expectation: 50% of qubits
        expected = n_qubits * 0.5
        plt.axvline(x=expected, color='red', linestyle='--', linewidth=2, 
                    label=f'Expected (50%): {expected:.0f}')
        plt.axvline(x=np.mean(sifted_lengths), color='green', linestyle='-', linewidth=2,
                    label=f'Actual Mean: {np.mean(sifted_lengths):.1f}')
        
        plt.xlabel('Sifted Key Length (bits)', fontsize=12, fontweight='bold')
        plt.ylabel('Frequency', fontsize=12, fontweight='bold')
        plt.title(f'Distribution of Sifted Key Lengths\n({n_simulations} simulations, {n_qubits} qubits each)',
                  fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig('bb84_sifted_key_distribution.png', dpi=300, bbox_inches='tight')
        print("[SUCCESS] Saved: bb84_sifted_key_distribution.png")
        plt.show()
    
    @staticmethod
    def plot_basis_choice_heatmap():
        """
        Plot 3: Basis Choice Heatmap (Single Simulation)
        
        Visualizes Alice's and Bob's basis choices across the transmission.
        """
        print("\n" + "="*60)
        print("VISUALIZATION 3: Basis Choice Heatmap")
        print("="*60)
        
        # Run a single detailed simulation
        sim = EnhancedBB84Protocol(n_qubits=100, interception_rate=0.5)
        result = sim.executeSim()
        
        # Create basis comparison matrix
        alice_bases = np.array(result['alice_bases'])
        bob_bases = np.array(result['bob_bases'])
        
        # Reshape for heatmap (10x10 grid)
        grid_size = 10
        alice_grid = alice_bases[:100].reshape(grid_size, grid_size)
        bob_grid = bob_bases[:100].reshape(grid_size, grid_size)
        
        # Create match/mismatch grid
        match_grid = (alice_grid == bob_grid).astype(int)
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        # Alice's bases
        sns.heatmap(alice_grid, ax=axes[0], cmap='RdYlGn', cbar_kws={'label': '0=Z, 1=X'},
                    linewidths=0.5, linecolor='gray', square=True)
        axes[0].set_title("Alice's Basis Choices", fontweight='bold')
        axes[0].set_xlabel('Qubit Column')
        axes[0].set_ylabel('Qubit Row')
        
        # Bob's bases
        sns.heatmap(bob_grid, ax=axes[1], cmap='RdYlGn', cbar_kws={'label': '0=Z, 1=X'},
                    linewidths=0.5, linecolor='gray', square=True)
        axes[1].set_title("Bob's Basis Choices", fontweight='bold')
        axes[1].set_xlabel('Qubit Column')
        axes[1].set_ylabel('Qubit Row')
        
        # Match/mismatch
        sns.heatmap(match_grid, ax=axes[2], cmap='coolwarm', cbar_kws={'label': '0=Mismatch, 1=Match'},
                    linewidths=0.5, linecolor='gray', square=True)
        axes[2].set_title("Basis Agreement\n(Match = Kept in Sifted Key)", fontweight='bold')
        axes[2].set_xlabel('Qubit Column')
        axes[2].set_ylabel('Qubit Row')
        
        plt.suptitle('BB84 Basis Selection Analysis (100 qubits, 50% Eve interception)', 
                     fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig('bb84_basis_heatmap.png', dpi=300, bbox_inches='tight')
        print("[SUCCESS] Saved: bb84_basis_heatmap.png")
        plt.show()
    
    @staticmethod
    def plot_noise_model_comparison(n_qubits: int = 200):
        """
        Plot 4: Noise Model Comparison
        
        Compares QBER for different quantum noise models at varying strengths.
        """
        print("\n" + "="*60)
        print("VISUALIZATION 4: Noise Model Comparison")
        print("="*60)
        
        noise_types = ['depolarizing', 'bitflip', 'amplitude_damping', 'phase_damping']
        noise_strengths = np.linspace(0.01, 0.15, 8)
        
        plt.figure(figsize=(12, 7))
        
        for noise_type in noise_types:
            qber_values = []
            
            for strength in noise_strengths:
                sim = EnhancedBB84Protocol(
                    n_qubits=n_qubits,
                    interception_rate=0.0,  # No Eve, only noise
                    noise_type=noise_type,
                    noise_strength=strength
                )
                result = sim.executeSim()
                qber_values.append(result['qber'])
            
            plt.plot(noise_strengths * 100, np.array(qber_values) * 100, 
                     marker='o', linewidth=2, markersize=6, label=noise_type.replace('_', ' ').title())
        
        # Security threshold
        plt.axhline(y=11, color='red', linestyle='--', linewidth=2, 
                    label='Security Threshold (11%)', alpha=0.7)
        
        plt.xlabel('Noise Strength Parameter (%)', fontsize=12, fontweight='bold')
        plt.ylabel('Quantum Bit Error Rate - QBER (%)', fontsize=12, fontweight='bold')
        plt.title(f'BB84 QBER vs Noise Model Type\n(No eavesdropper, {n_qubits} qubits)',
                  fontsize=14, fontweight='bold')
        plt.legend(fontsize=10, loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('bb84_noise_comparison.png', dpi=300, bbox_inches='tight')
        print("[SUCCESS] Saved: bb84_noise_comparison.png")
        plt.show()
    
    @staticmethod
    def plot_security_threshold_analysis(n_trials: int = 50, n_qubits: int = 150):
        """
        Plot 5: Security Threshold Visualization
        
        Shows multiple simulation runs and highlights which fall above/below 11% threshold.
        """
        print("\n" + "="*60)
        print("VISUALIZATION 5: Security Threshold Analysis")
        print("="*60)
        
        interception_rates = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for rate in interception_rates:
            qber_samples = []
            
            for _ in range(n_trials):
                sim = EnhancedBB84Protocol(n_qubits=n_qubits, interception_rate=rate)
                result = sim.executeSim()
                qber_samples.append(result['qber'] * 100)
            
            # Color code based on security threshold
            colors = ['green' if q < 11 else 'red' for q in qber_samples]
            x_positions = [rate * 100] * n_trials
            
            ax.scatter(x_positions, qber_samples, alpha=0.6, s=30, c=colors)
        
        # Security threshold line
        ax.axhline(y=11, color='orange', linestyle='--', linewidth=3, 
                   label='Security Threshold (11%)', zorder=5)
        
        ax.set_xlabel('Eve Interception Rate (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('QBER (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'BB84 Security Threshold Analysis\n' + 
                     f'({n_trials} trials per rate, {n_qubits} qubits)\n' +
                     'Green = Secure | Red = Insecure',
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11)
        plt.tight_layout()
        plt.savefig('bb84_security_threshold.png', dpi=300, bbox_inches='tight')
        print("[SUCCESS] Saved: bb84_security_threshold.png")
        plt.show()


# =============================================================================
# INTERACTIVE PARAMETER SELECTION SYSTEM
# =============================================================================

def interactive_simulation():
    """
    Interactive command-line interface for configuring and running BB84 simulations.
    """
    print("\n" + "="*70)
    print(" "*15 + "BB84 QUANTUM KEY DISTRIBUTION SIMULATOR")
    print("="*70)
    print("\nWelcome! This tool simulates the BB84 QKD protocol with configurable")
    print("parameters including eavesdropper presence, noise models, and QBER targets.\n")
    
    # Parameter 1: Number of qubits
    while True:
        try:
            n_qubits = int(input("Enter number of qubits to transmit [100-1000, default=200]: ") or "200")
            if 100 <= n_qubits <= 1000:
                break
            print("  [WARNING] Please enter a value between 100 and 1000")
        except ValueError:
            print("  [WARNING] Invalid input. Please enter an integer.")
    
    # Parameter 2: Interception rate
    print("\n" + "-"*70)
    print("Eve's Interception Rate:")
    print("  0.0 = Secure channel (no eavesdropping)")
    print("  0.5 = Eve intercepts 50% of qubits")
    print("  1.0 = Full eavesdropping attack")
    while True:
        try:
            interception_rate = float(input("Enter interception rate [0.0-1.0, default=0.0]: ") or "0.0")
            if 0.0 <= interception_rate <= 1.0:
                break
            print("  [WARNING] Please enter a value between 0.0 and 1.0")
        except ValueError:
            print("  [WARNING] Invalid input. Please enter a decimal number.")
    
    # Parameter 3: Target QBER
    print("\n" + "-"*70)
    print("Target Artificial QBER:")
    print("  0.0 = No artificial errors (only Eve + noise)")
    print("  0.05 = 5% artificial error rate")
    print("  0.11 = 11% (security threshold)")
    while True:
        try:
            target_qber = float(input("Enter target QBER [0.0-0.30, default=0.0]: ") or "0.0")
            if 0.0 <= target_qber <= 0.30:
                break
            print("  [WARNING] Please enter a value between 0.0 and 0.30")
        except ValueError:
            print("  [WARNING] Invalid input. Please enter a decimal number.")
    
    # Parameter 4: Noise model
    print("\n" + "-"*70)
    print("Available Noise Models:")
    print("  1. none             - Ideal quantum channel")
    print("  2. depolarizing     - Uniform Pauli noise (X, Y, Z)")
    print("  3. bitflip          - Bit-flip errors (X gate)")
    print("  4. phaseflip        - Phase errors (Z gate)")
    print("  5. amplitude_damping - Photon loss / energy dissipation")
    print("  6. phase_damping    - Decoherence without energy loss")
    
    noise_map = {
        '1': 'none', '2': 'depolarizing', '3': 'bitflip',
        '4': 'phaseflip', '5': 'amplitude_damping', '6': 'phase_damping'
    }
    
    while True:
        choice = input("Select noise model [1-6, default=1]: ") or "1"
        if choice in noise_map:
            noise_type = noise_map[choice]
            break
        print("  [WARNING] Invalid choice. Please enter a number between 1 and 6.")
    
    # Parameter 5: Noise strength (if applicable)
    noise_strength = 0.0
    if noise_type != 'none':
        print("\n" + "-"*70)
        print("Noise Strength Parameter:")
        print("  0.01 = 1% noise (weak)")
        print("  0.05 = 5% noise (moderate)")
        print("  0.10 = 10% noise (strong)")
        while True:
            try:
                noise_strength = float(input("Enter noise strength [0.0-0.20, default=0.05]: ") or "0.05")
                if 0.0 <= noise_strength <= 0.20:
                    break
                print("  [WARNING] Please enter a value between 0.0 and 0.20")
            except ValueError:
                print("  [WARNING] Invalid input. Please enter a decimal number.")
    
    # Run simulation
    print("\n" + "="*70)
    print("RUNNING SIMULATION...")
    print("="*70)
    
    sim = EnhancedBB84Protocol(
        n_qubits=n_qubits,
        interception_rate=interception_rate,
        target_qber=target_qber,
        noise_type=noise_type,
        noise_strength=noise_strength
    )
    
    result = sim.executeSim()
    
    # Visualization option
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    print("\nWould you like to generate visualizations?")
    print("  1. QBER vs Interception Rate")
    print("  2. Sifted Key Distribution")
    print("  3. Basis Choice Heatmap")
    print("  4. Noise Model Comparison")
    print("  5. Security Threshold Analysis")
    print("  6. Generate ALL visualizations")
    print("  0. Skip visualizations")
    
    viz_choice = input("\nEnter your choice [0-6]: ") or "0"
    
    viz = BB84Visualizer()
    
    if viz_choice == '1':
        viz.plot_qber_vs_interception()
    elif viz_choice == '2':
        viz.plot_basis_matching_distribution()
    elif viz_choice == '3':
        viz.plot_basis_choice_heatmap()
    elif viz_choice == '4':
        viz.plot_noise_model_comparison()
    elif viz_choice == '5':
        viz.plot_security_threshold_analysis()
    elif viz_choice == '6':
        print("\nGenerating all visualizations...")
        viz.plot_qber_vs_interception(n_trials=15)
        viz.plot_basis_matching_distribution(n_simulations=80)
        viz.plot_basis_choice_heatmap()
        viz.plot_noise_model_comparison()
        viz.plot_security_threshold_analysis(n_trials=30)
        print("\n[SUCCESS] All visualizations generated and saved!")
    
    print("\n" + "="*70)
    print("Thank you for using the BB84 Simulator!")
    print("="*70 + "\n")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Option 1: Run interactive mode
    interactive_simulation()
    
    # Option 2: Run predefined scenarios (comment out interactive mode above)
    # print("\n" + "="*70)
    # print("SCENARIO 1: Secure Channel (No Eve, No Noise)")
    # print("="*70)
    # sim1 = EnhancedBB84Protocol(n_qubits=200, interception_rate=0.0)
    # sim1.executeSim()
    
    # print("\n" + "="*70)
    # print("SCENARIO 2: 50% Eavesdropper")
    # print("="*70)
    # sim2 = EnhancedBB84Protocol(n_qubits=200, interception_rate=0.5)
    # sim2.executeSim()
    
    # print("\n" + "="*70)
    # print("SCENARIO 3: Depolarizing Noise (5% strength)")
    # print("="*70)
    # sim3 = EnhancedBB84Protocol(n_qubits=200, noise_type='depolarizing', noise_strength=0.05)
    # sim3.executeSim()
    
    # Generate visualizations
    # viz = BB84Visualizer()
    # viz.plot_qber_vs_interception()
    # viz.plot_basis_matching_distribution()
    # viz.plot_basis_choice_heatmap()
    # viz.plot_noise_model_comparison()
    # viz.plot_security_threshold_analysis()
