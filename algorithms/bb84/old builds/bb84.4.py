import numpy as np
from art import text2art
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, pauli_error, amplitude_damping_error, phase_damping_error
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Tuple, List
from tqdm import tqdm  # Progress bar library

# console art width
global console_width
console_width = 85

class EnhancedBB84Protocol:
    """
    Enhanced BB84 Quantum Key Distribution Protocol Simulation
    
    Features:
    - Configurable QBER (target artificial error rate)
    - Multiple realistic noise models (Depolarizing, Bit-flip, Phase-damping, Amplitude-damping)
    - Eavesdropper (Eve) simulation with variable interception rates
    - Distance-dependent photon loss modelling (fiber attenuation)
    - Secure key rate calculation (Devetak-Winter bound)
    - Comprehensive data visualisation
    
    Attributes:
        n_qubits (int): Number of qubits to transmit
        interception_rate (float): Probability Eve intercepts a qubit [0.0-1.0]
        target_qber (float): Artificial QBER to inject (simulates channel imperfections)
        noise_type (str): Type of quantum noise model to apply
        noise_strength (float): Strength parameter for the noise model
        distance_km (float): Fiber optic distance in kilometers
        verbose (bool): Enable detailed console output
    """

    def __init__(self,
                 n_qubits: int = 100,
                 interception_rate: float = 0.0,
                 target_qber: float = 0.0,
                 noise_type: str = 'none',
                 noise_strength: float = 0.01,
                 distance_km: float = 25.0,
                 verbose: bool = True):
        """
        Initialise the enhanced BB84 simulation.
        
        Args:
            n_qubits: Total number of bits/qubits to transmit
            interception_rate: Eve's interception probability [0.0 = secure, 1.0 = full eavesdrop]
            target_qber: Artificial error rate to inject [0.0-1.0]
                        NOTE: Only used if noise_type='none' (represents detector/timing errors)
                        If noise model is active, it already provides realistic errors
            noise_type: Quantum noise model ['none', 'depolarizing', 'bitflip', 'phaseflip',
                                              'amplitude_damping', 'phase_damping']
            noise_strength: Noise parameter intensity [0.0-1.0]
            distance_km: Fiber optic channel distance in km (default 25km)
            verbose: Enable detailed console output (default True)
        """
        self.n_qubits = n_qubits
        self.interception_rate = interception_rate
        self.target_qber = target_qber
        self.noise_type = noise_type
        self.noise_strength = noise_strength
        self.distance_km = distance_km
        self.verbose = verbose
        
        # Calculate fiber transmission efficiency
        # Standard single-mode fiber: ~0.2 dB/km at 1550nm (telecom C-band)
        self.attenuation_db_per_km = 0.2
        total_loss_db = self.attenuation_db_per_km * self.distance_km
        self.transmission_efficiency = 10 ** (-total_loss_db / 10)
        
        # Initialize backend with optional noise model
        self.backend_sim = self._configure_backend()
        
        # Protocol data storage
        self.alice_bits = []
        self.alice_bases = []
        self.bob_bases = []
        self.bob_results = []
        self.eve_presence = []
        self.sifted_key_alice = []
        self.sifted_key_bob = []
        self.match_indices = []
        self.calculated_qber = 0.0
        self.secure_key_rate = 0.0
        self.photons_lost = 0  # Track photon loss
        
    def _configure_backend(self) -> AerSimulator:
        """
        Configure the Qiskit Aer backend with the specified noise model.
        
        Returns:
            AerSimulator with appropriate noise configuration
        """
        noise_model = NoiseModel()
        
        if self.noise_type == 'none':
            return AerSimulator()
        
        elif self.noise_type == 'depolarizing':
            error = depolarizing_error(self.noise_strength, 1)
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            if self.verbose:
                print(f"[Noise Model] Depolarizing channel with strength {self.noise_strength}")
            
        elif self.noise_type == 'bitflip':
            error = pauli_error([('X', self.noise_strength), ('I', 1 - self.noise_strength)])
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            if self.verbose:
                print(f"[Noise Model] Bit-flip channel with strength {self.noise_strength}")
            
        elif self.noise_type == 'phaseflip':
            error = pauli_error([('Z', self.noise_strength), ('I', 1 - self.noise_strength)])
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            if self.verbose:
                print(f"[Noise Model] Phase-flip channel with strength {self.noise_strength}")
            
        elif self.noise_type == 'amplitude_damping':
            error = amplitude_damping_error(self.noise_strength)
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            if self.verbose:
                print(f"[Noise Model] Amplitude damping with strength {self.noise_strength}")
            
        elif self.noise_type == 'phase_damping':
            error = phase_damping_error(self.noise_strength)
            noise_model.add_all_qubit_quantum_error(error, ['x', 'h', 'id'])
            if self.verbose:
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
        if self.verbose:
            print(f"\n{'='*console_width}")
            print(f"STEP 1: Alice prepares {self.n_qubits} qubits")
            print(f"{'='*console_width}")
        
        self.alice_bits = np.random.randint(2, size=self.n_qubits)
        self.alice_bases = np.random.randint(2, size=self.n_qubits)
        
        qubit_stream = []
        
        for i in range(self.n_qubits):
            qc = QuantumCircuit(1, 1)
            
            if self.alice_bits[i] == 1:
                qc.x(0)
            
            if self.alice_bases[i] == 1:
                qc.h(0)
            
            qubit_stream.append(qc)
        
        if self.verbose:
            print(f"[SUCCESS] Encoded {self.n_qubits} qubits")
            print(f"  Sample bits:  {self.alice_bits[:10]}")
            print(f"  Sample bases: {self.alice_bases[:10]} (0=Z, 1=X)")
        
        return qubit_stream

    def quantumChannel(self, qubit_stream: List[QuantumCircuit]) -> List[QuantumCircuit]:
        """
        Simulate the quantum channel with eavesdropper (Eve), noise, and photon loss.
        
        Eve's Attack Strategy (Intercept-Resend):
        1. Intercepts photon with probability `interception_rate`
        2. Randomly chooses a measurement basis (no knowledge of Alice's choice)
        3. Measures the qubit (collapses superposition)
        4. Prepares a fresh qubit in the measured state
        5. Resends to Bob
        
        Photon Loss:
        - Models exponential fiber attenuation at 1550nm wavelength
        - Typical loss: 0.2 dB/km in standard single-mode fiber
        - Lost photons are marked as None (no detection at Bob's end)
        
        This attack introduces errors due to basis mismatch, creating detectable QBER.
        
        Returns:
            List of QuantumCircuit objects after channel transmission (or None for lost photons)
        """
        if self.verbose:
            print(f"\n{'='*console_width}")
            print(f"STEP 2: Quantum Channel Transmission")
            print(f"{'='*console_width}")
            print(f"Channel distance:      {self.distance_km} km")
            print(f"Fiber attenuation:     {self.attenuation_db_per_km} dB/km")
            print(f"Transmission efficiency: {self.transmission_efficiency*100:.2f}%")
            print(f"Eve interception rate: {self.interception_rate*100:.1f}%")
            print(f"Noise model:           {self.noise_type} (strength: {self.noise_strength})")
        
        intercepted_stream = []
        self.eve_presence = [False] * self.n_qubits
        self.photons_lost = 0
        eve_count = 0
        
        for i, qc in enumerate(qubit_stream):
            # First: Model photon loss due to fiber attenuation
            if np.random.rand() > self.transmission_efficiency:
                # Photon lost in fiber - Bob receives nothing
                intercepted_stream.append(None)
                self.photons_lost += 1
                continue
            
            # Photon survived transmission - now check for Eve's interception
            if np.random.rand() < self.interception_rate:
                self.eve_presence[i] = True
                eve_count += 1
                
                eve_basis = np.random.randint(2)
                
                if eve_basis == 1:
                    qc.h(0)
                
                qc.measure(0, 0)
                
                instance = self.backend_sim.run(qc, shots=1, memory=True)
                result = instance.result().get_memory()[0]
                
                new_qc = QuantumCircuit(1, 1)
                
                if result == '1':
                    new_qc.x(0)
                
                if eve_basis == 1:
                    new_qc.h(0)
                
                intercepted_stream.append(new_qc)
            else:
                intercepted_stream.append(qc)
        
        if self.verbose:
            print(f"[SUCCESS] Transmission complete")
            print(f"  Photons lost:         {self.photons_lost}/{self.n_qubits} ({self.photons_lost/self.n_qubits*100:.1f}%)")
            print(f"  Eve intercepted:      {eve_count}/{self.n_qubits} ({eve_count/self.n_qubits*100:.1f}%)")
            print(f"  Photons received:     {self.n_qubits - self.photons_lost}/{self.n_qubits}")
        
        return intercepted_stream

    def bobMeasurement(self, incoming_stream: List[QuantumCircuit]):
        """
        Bob receives qubits and measures them using randomly chosen bases.
        
        Bob has no knowledge of:
        - Alice's bit values
        - Alice's basis choices
        - Whether Eve intercepted
        - Which photons were lost (he only knows he didn't detect some)
        
        He simply chooses random bases and measures, then later compares bases with Alice.
        For lost photons (None), Bob records no result.
        """
        if self.verbose:
            print(f"\n{'='*console_width}")
            print(f"STEP 3: Bob measures incoming qubits")
            print(f"{'='*console_width}")
        
        self.bob_bases = np.random.randint(2, size=self.n_qubits)
        self.bob_results = []
        
        for i, qc in enumerate(incoming_stream):
            if qc is None:
                # Photon was lost - Bob detects nothing
                self.bob_results.append(None)
                continue
            
            if self.bob_bases[i] == 1:
                qc.h(0)
            
            qc.measure(0, 0)
            
            instance = self.backend_sim.run(qc, shots=1, memory=True)
            measured_bit = int(instance.result().get_memory()[0])
            self.bob_results.append(measured_bit)
        
        successful_detections = sum(1 for r in self.bob_results if r is not None)
        
        if self.verbose:
            print(f"[SUCCESS] Bob measurement complete")
            print(f"  Successful detections: {successful_detections}/{self.n_qubits}")
            print(f"  Sample results: {[r for r in self.bob_results[:15] if r is not None][:10]}")
            print(f"  Sample bases:   {self.bob_bases[:10]} (0=Z, 1=X)")

    def injectArtificialErrors(self):
        """
        Inject additional artificial errors to achieve target QBER.
        
        CRITICAL CHANGE: This method now ONLY applies when noise_type='none'
        to avoid double-counting errors from quantum noise models.
        
        Purpose:
        - Simulates classical imperfections (detector noise, timing jitter, dark counts)
        - Only used when no quantum noise model is active
        - If quantum noise model is active, it already provides realistic errors
        
        Strategy:
        - Calculate how many errors are needed to reach target_qber
        - Randomly flip bits in Bob's results among the sifted key positions
        - Only apply to positions where bases matched (the sifted key)
        """
        # CRITICAL FIX: Only inject artificial errors if no quantum noise model is active
        if self.target_qber <= 0 or self.noise_type != 'none':
            if self.verbose and self.target_qber > 0 and self.noise_type != 'none':
                print(f"\n[Artificial Error Injection]")
                print(f"  Skipping: Quantum noise model '{self.noise_type}' already provides errors")
                print(f"  (Avoiding double-counting)")
            return
        
        if self.verbose:
            print(f"\n[Artificial Error Injection]")
            print(f"Target QBER: {self.target_qber*100:.2f}%")
        
        current_errors = sum(1 for k in range(len(self.sifted_key_alice)) 
                            if self.sifted_key_alice[k] != self.sifted_key_bob[k])
        current_qber = current_errors / len(self.sifted_key_alice) if len(self.sifted_key_alice) > 0 else 0
        
        target_errors = int(self.target_qber * len(self.sifted_key_alice))
        additional_errors_needed = max(0, target_errors - current_errors)
        
        if additional_errors_needed > 0:
            matching_positions = [i for i in range(len(self.sifted_key_alice))
                                 if self.sifted_key_alice[i] == self.sifted_key_bob[i]]
            
            if len(matching_positions) >= additional_errors_needed:
                positions_to_flip = np.random.choice(matching_positions, 
                                                     size=additional_errors_needed, 
                                                     replace=False)
                
                for pos in positions_to_flip:
                    self.sifted_key_bob[pos] = 1 - self.sifted_key_bob[pos]
                
                if self.verbose:
                    print(f"[SUCCESS] Injected {additional_errors_needed} classical errors")
                    print(f"  (Simulating detector imperfections, timing jitter, dark counts)")
            else:
                if self.verbose:
                    print(f"[WARNING] Not enough matching positions to inject all errors")
        else:
            if self.verbose:
                print(f"[INFO] Current QBER ({current_qber*100:.2f}%) already meets or exceeds target")

    def calculate_secure_key_rate(self) -> float:
        """
        Calculate the final secure key rate using the Devetak-Winter bound.
        
        This accounts for:
        1. Information leaked during error correction (quantified by error correction efficiency)
        2. Information Eve might have gained (quantified by QBER via privacy amplification)
        
        Formula:
        R_secure = n_sifted * [1 - f_EC * h(QBER) - h(QBER)]
        
        Where:
        - n_sifted: length of sifted key
        - f_EC: error correction efficiency (typically 1.1-1.22, we use 1.16)
        - h(x): binary entropy function = -x*log2(x) - (1-x)*log2(1-x)
        - QBER: quantum bit error rate
        
        Returns:
            Secure key rate in bits (can be 0 if QBER too high)
        """
        def binary_entropy(x):
            """Binary entropy function for Shannon information theory."""
            if x == 0 or x == 1:
                return 0
            if x < 0 or x > 1:
                return 0
            return -x * np.log2(x) - (1 - x) * np.log2(1 - x)
        
        # Error correction efficiency (realistic value for CASCADE or LDPC codes)
        f_EC = 1.16
        
        # Calculate secure key rate
        n_sifted = len(self.sifted_key_alice)
        QBER = self.calculated_qber
        
        # Devetak-Winter bound for secure key rate
        secure_rate = n_sifted * (1 - f_EC * binary_entropy(QBER) - binary_entropy(QBER))
        
        # Can't have negative secure key
        self.secure_key_rate = max(0, secure_rate)
        
        return self.secure_key_rate

    def postProcessing(self) -> Tuple[float, int, int]:
        """
        Sifting Phase and QBER Calculation.
        
        Classical Communication (Public Channel):
        1. Alice and Bob announce their basis choices (but NOT bit values)
        2. They discard all positions where bases didn't match OR photons were lost
        3. The remaining bits form the "sifted key"
        4. They sacrifice a random subset to calculate QBER
        5. If QBER > 11%, they abort (eavesdropper detected)
        6. Calculate final secure key rate using Devetak-Winter bound
        
        Returns:
            Tuple of (qber, total_sifted, errors)
        """
        if self.verbose:
            print(f"\n{'='*console_width}")
            print(f"STEP 4: Sifting and QBER Calculation")
            print(f"{'='*console_width}")
        
        self.sifted_key_alice = []
        self.sifted_key_bob = []
        self.match_indices = []
        
        for i in range(self.n_qubits):
            # Only keep if bases matched AND Bob detected the photon
            if self.alice_bases[i] == self.bob_bases[i] and self.bob_results[i] is not None:
                self.sifted_key_alice.append(self.alice_bits[i])
                self.sifted_key_bob.append(self.bob_results[i])
                self.match_indices.append(i)
        
        total_sifted = len(self.sifted_key_alice)
        
        if total_sifted == 0:
            if self.verbose:
                print("[ERROR] No bases matched or all photons lost!")
            return 0.0, 0, 0
        
        # Inject artificial errors ONLY if noise_type='none' (to avoid double-counting)
        self.injectArtificialErrors()
        
        errors = sum(1 for k in range(total_sifted) 
                    if self.sifted_key_alice[k] != self.sifted_key_bob[k])
        
        qber = errors / total_sifted
        self.calculated_qber = qber
        
        # Calculate secure key rate
        secure_key_bits = self.calculate_secure_key_rate()
        
        if self.verbose:
            print(f"\n[Protocol Statistics]")
            print(f"  Total qubits sent:     {self.n_qubits}")
            print(f"  Photons lost:          {self.photons_lost} ({self.photons_lost/self.n_qubits*100:.1f}%)")
            print(f"  Photons received:      {self.n_qubits - self.photons_lost}")
            print(f"  Basis match rate:      {total_sifted/(self.n_qubits - self.photons_lost)*100:.1f}% of received")
            print(f"  Sifted key length:     {total_sifted} bits")
            print(f"  Errors detected:       {errors}")
            print(f"  Calculated QBER:       {qber:.4f} ({qber*100:.2f}%)")
            
            SECURITY_THRESHOLD = 0.11
            print(f"\n[Security Analysis]")
            print(f"  Safety threshold:      {SECURITY_THRESHOLD*100:.0f}%")
            
            if qber > SECURITY_THRESHOLD:
                print(f"  Status:                INSECURE - QBER too high!")
                print(f"  Recommendation:        Abort key exchange. Possible eavesdropper detected.")
                print(f"  Secure key bits:       0 (protocol aborted)")
            else:
                print(f"  Status:                SECURE - QBER within safe limits")
                print(f"  Secure key bits:       {secure_key_bits:.0f} bits")
                print(f"  Key rate efficiency:   {secure_key_bits/total_sifted*100:.1f}% of sifted key")
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
        
        return {
            'qber': qber,
            'sifted_length': sifted_length,
            'errors': errors,
            'eve_interceptions': sum(self.eve_presence),
            'photons_lost': self.photons_lost,
            'transmission_efficiency': self.transmission_efficiency,
            'secure_key_rate': self.secure_key_rate,
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
    def plot_qber_vs_interception(n_trials: int = 20, n_qubits: int = 200, distance_km: float = 25):
        """
        Plot 1: QBER vs Eve's Interception Rate
        
        Demonstrates the theoretical 25% QBER limit when Eve intercepts 100%.
        This is the signature of quantum eavesdropping in BB84.
        """
        print("\n" + "="*console_width)
        print("VISUALIZATION 1: QBER vs Interception Rate")
        print("="*console_width)
        
        interception_rates = np.linspace(0, 1, 11)
        qber_values = []
        qber_std = []
        
        for rate in tqdm(interception_rates, desc="Processing interception rates", unit="rate"):
            qbers = []
            for _ in tqdm(range(n_trials), desc=f"  Rate {rate*100:.0f}%", leave=False, unit="trial"):
                sim = EnhancedBB84Protocol(
                    n_qubits=n_qubits, 
                    interception_rate=rate,
                    distance_km=distance_km,
                    verbose=False
                )
                result = sim.executeSim()
                qbers.append(result['qber'])
            
            qber_values.append(np.mean(qbers))
            qber_std.append(np.std(qbers))
        
        print("Rendering plot...")
        
        plt.figure(figsize=(10, 6))
        plt.errorbar(interception_rates * 100, np.array(qber_values) * 100, 
                     yerr=np.array(qber_std) * 100, 
                     marker='o', capsize=5, linewidth=2, markersize=8,
                     label='Simulated QBER')
        
        theoretical = 0.25 * interception_rates * 100
        plt.plot(interception_rates * 100, theoretical, 'r--', 
                 linewidth=2, label='Theoretical (25% limit)')
        
        plt.axhline(y=11, color='orange', linestyle=':', linewidth=2, 
                    label='Security Threshold (11%)')
        
        plt.xlabel('Eve Interception Rate (%)', fontsize=12, fontweight='bold')
        plt.ylabel('Quantum Bit Error Rate - QBER (%)', fontsize=12, fontweight='bold')
        plt.title(f'BB84 Protocol: QBER vs Eavesdropper Interception Rate\n' + 
                  f'(Distance: {distance_km}km, {n_trials} trials, {n_qubits} qubits each)',
                  fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=11)
        plt.tight_layout()
        # REMOVED: plt.savefig() - No auto-save
        print("[SUCCESS] Plot rendered (not auto-saved)")
        plt.show()
    
    @staticmethod
    def plot_basis_matching_distribution(n_simulations: int = 100, n_qubits: int = 100, distance_km: float = 25):
        """
        Plot 2: Sifted Key Length Distribution
        
        Shows the statistical distribution of basis matching (should be ~50% of received photons).
        """
        print("\n" + "="*console_width)
        print("VISUALIZATION 2: Sifted Key Length Distribution")
        print("="*console_width)
        
        sifted_lengths = []
        
        for _ in tqdm(range(n_simulations), desc="Running simulations", unit="sim"):
            sim = EnhancedBB84Protocol(
                n_qubits=n_qubits, 
                interception_rate=0.0,
                distance_km=distance_km,
                verbose=False
            )
            result = sim.executeSim()
            sifted_lengths.append(result['sifted_length'])
        
        print("Rendering plot...")
        
        plt.figure(figsize=(10, 6))
        plt.hist(sifted_lengths, bins=20, edgecolor='black', alpha=0.7, color='skyblue')
        
        sim_temp = EnhancedBB84Protocol(n_qubits=n_qubits, distance_km=distance_km, verbose=False)
        expected = n_qubits * sim_temp.transmission_efficiency * 0.5
        
        plt.axvline(x=expected, color='red', linestyle='--', linewidth=2, 
                    label=f'Expected (with loss): {expected:.0f}')
        plt.axvline(x=np.mean(sifted_lengths), color='green', linestyle='-', linewidth=2,
                    label=f'Actual Mean: {np.mean(sifted_lengths):.1f}')
        
        plt.xlabel('Sifted Key Length (bits)', fontsize=12, fontweight='bold')
        plt.ylabel('Frequency', fontsize=12, fontweight='bold')
        plt.title(f'Distribution of Sifted Key Lengths\n({n_simulations} simulations, {n_qubits} qubits, {distance_km}km distance)',
                  fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        # REMOVED: plt.savefig() - No auto-save
        print("[SUCCESS] Plot rendered (not auto-saved)")
        plt.show()
    
    @staticmethod
    def plot_basis_choice_heatmap(distance_km: float = 25):
        """
        Plot 3: Basis Choice Heatmap (Single Simulation)
        
        Visualizes Alice's and Bob's basis choices across the transmission.
        """
        print("\n" + "="*console_width)
        print("VISUALIZATION 3: Basis Choice Heatmap")
        print("="*console_width)
        print("Running simulation...")
        
        sim = EnhancedBB84Protocol(
            n_qubits=100, 
            interception_rate=0.5,
            distance_km=distance_km,
            verbose=False
        )
        result = sim.executeSim()
        
        print("Rendering heatmaps...")
        
        alice_bases = np.array(result['alice_bases'])
        bob_bases = np.array(result['bob_bases'])
        
        grid_size = 10
        alice_grid = alice_bases[:100].reshape(grid_size, grid_size)
        bob_grid = bob_bases[:100].reshape(grid_size, grid_size)
        
        match_grid = (alice_grid == bob_grid).astype(int)
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        sns.heatmap(alice_grid, ax=axes[0], cmap='RdYlGn', cbar_kws={'label': '0=Z, 1=X'},
                    linewidths=0.5, linecolor='gray', square=True)
        axes[0].set_title("Alice's Basis Choices", fontweight='bold')
        axes[0].set_xlabel('Qubit Column')
        axes[0].set_ylabel('Qubit Row')
        
        sns.heatmap(bob_grid, ax=axes[1], cmap='RdYlGn', cbar_kws={'label': '0=Z, 1=X'},
                    linewidths=0.5, linecolor='gray', square=True)
        axes[1].set_title("Bob's Basis Choices", fontweight='bold')
        axes[1].set_xlabel('Qubit Column')
        axes[1].set_ylabel('Qubit Row')
        
        sns.heatmap(match_grid, ax=axes[2], cmap='coolwarm', cbar_kws={'label': '0=Mismatch, 1=Match'},
                    linewidths=0.5, linecolor='gray', square=True)
        axes[2].set_title("Basis Agreement\n(Match = Kept in Sifted Key)", fontweight='bold')
        axes[2].set_xlabel('Qubit Column')
        axes[2].set_ylabel('Qubit Row')
        
        plt.suptitle(f'BB84 Basis Selection Analysis (100 qubits, {distance_km}km, 50% Eve interception)', 
                     fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        # REMOVED: plt.savefig() - No auto-save
        print("[SUCCESS] Plot rendered (not auto-saved)")
        plt.show()
    
    @staticmethod
    def plot_noise_model_comparison(n_qubits: int = 200, distance_km: float = 25):
        """
        Plot 4: Noise Model Comparison
        
        Compares QBER for different quantum noise models at varying strengths.
        """
        print("\n" + "="*console_width)
        print("VISUALIZATION 4: Noise Model Comparison")
        print("="*console_width)
        
        noise_types = ['depolarizing', 'bitflip', 'amplitude_damping', 'phase_damping']
        noise_strengths = np.linspace(0.01, 0.15, 8)
        
        plt.figure(figsize=(12, 7))
        
        for noise_type in tqdm(noise_types, desc="Testing noise models", unit="model"):
            qber_values = []
            
            for strength in tqdm(noise_strengths, desc=f"  {noise_type}", leave=False, unit="strength"):
                sim = EnhancedBB84Protocol(
                    n_qubits=n_qubits,
                    interception_rate=0.0,
                    noise_type=noise_type,
                    noise_strength=strength,
                    distance_km=distance_km,
                    verbose=False
                )
                result = sim.executeSim()
                qber_values.append(result['qber'])
            
            plt.plot(noise_strengths * 100, np.array(qber_values) * 100, 
                     marker='o', linewidth=2, markersize=6, label=noise_type.replace('_', ' ').title())
        
        print("Rendering plot...")
        
        plt.axhline(y=11, color='red', linestyle='--', linewidth=2, 
                    label='Security Threshold (11%)', alpha=0.7)
        
        plt.xlabel('Noise Strength Parameter (%)', fontsize=12, fontweight='bold')
        plt.ylabel('Quantum Bit Error Rate - QBER (%)', fontsize=12, fontweight='bold')
        plt.title(f'BB84 QBER vs Noise Model Type\n(Distance: {distance_km}km, No eavesdropper, {n_qubits} qubits)',
                  fontsize=14, fontweight='bold')
        plt.legend(fontsize=10, loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        # REMOVED: plt.savefig() - No auto-save
        print("[SUCCESS] Plot rendered (not auto-saved)")
        plt.show()
    
    @staticmethod
    def plot_security_threshold_analysis(n_trials: int = 50, n_qubits: int = 150, distance_km: float = 25):
        """
        Plot 5: Security Threshold Visualization
        
        Shows multiple simulation runs and highlights which fall above/below 11% threshold.
        """
        print("\n" + "="*console_width)
        print("VISUALIZATION 5: Security Threshold Analysis")
        print("="*console_width)
        
        interception_rates = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for rate in tqdm(interception_rates, desc="Testing interception rates", unit="rate"):
            qber_samples = []
            
            for _ in tqdm(range(n_trials), desc=f"  Rate {rate*100:.0f}%", leave=False, unit="trial"):
                sim = EnhancedBB84Protocol(
                    n_qubits=n_qubits, 
                    interception_rate=rate,
                    distance_km=distance_km,
                    verbose=False
                )
                result = sim.executeSim()
                qber_samples.append(result['qber'] * 100)
            
            colors = ['green' if q < 11 else 'red' for q in qber_samples]
            x_positions = [rate * 100] * n_trials
            
            ax.scatter(x_positions, qber_samples, alpha=0.6, s=30, c=colors)
        
        print("Rendering plot...")
        
        ax.axhline(y=11, color='orange', linestyle='--', linewidth=3, 
                   label='Security Threshold (11%)', zorder=5)
        
        ax.set_xlabel('Eve Interception Rate (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('QBER (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'BB84 Security Threshold Analysis\n' + 
                     f'(Distance: {distance_km}km, {n_trials} trials per rate, {n_qubits} qubits)\n' +
                     'Green = Secure | Red = Insecure',
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11)
        plt.tight_layout()
        # REMOVED: plt.savefig() - No auto-save
        print("[SUCCESS] Plot rendered (not auto-saved)")
        plt.show()
    
    @staticmethod
    def plot_distance_vs_key_rate(distances_km: List[float] = None, n_qubits: int = 1000, n_trials: int = 10):
        """
        Plot 6: NEW - Secure Key Rate vs Distance
        
        Shows how distance affects the final usable key rate due to photon loss.
        This is critical for understanding QKD system limitations.
        """
        print("\n" + "="*console_width)
        print("VISUALIZATION 6: Secure Key Rate vs Distance")
        print("="*console_width)
        
        if distances_km is None:
            distances_km = np.linspace(0, 100, 11)  # 0 to 100 km
        
        key_rates = []
        key_rates_std = []
        
        for distance in tqdm(distances_km, desc="Testing distances", unit="km"):
            rates = []
            for _ in tqdm(range(n_trials), desc=f"  {distance:.0f}km", leave=False, unit="trial"):
                sim = EnhancedBB84Protocol(
                    n_qubits=n_qubits,
                    interception_rate=0.0,  # No Eve for this analysis
                    distance_km=distance,
                    verbose=False
                )
                result = sim.executeSim()
                rates.append(result['secure_key_rate'])
            
            key_rates.append(np.mean(rates))
            key_rates_std.append(np.std(rates))
        
        print("Rendering plot...")
        
        plt.figure(figsize=(10, 6))
        plt.errorbar(distances_km, key_rates, yerr=key_rates_std,
                     marker='o', capsize=5, linewidth=2, markersize=8,
                     color='blue', label='Simulated Key Rate')
        
        plt.xlabel('Channel Distance (km)', fontsize=12, fontweight='bold')
        plt.ylabel('Secure Key Rate (bits)', fontsize=12, fontweight='bold')
        plt.title(f'BB84 Secure Key Rate vs Fiber Distance\n' +
                  f'({n_qubits} qubits transmitted, {n_trials} trials per distance)',
                  fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=11)
        plt.tight_layout()
        # REMOVED: plt.savefig() - No auto-save
        print("[SUCCESS] Plot rendered (not auto-saved)")
        plt.show()


# =============================================================================
# INTERACTIVE PARAMETER SELECTION SYSTEM
# =============================================================================

def interactive_simulation():
    """
    Interactive command-line interface for configuring and running BB84 simulations.
    """
    print("\n" + "="*console_width)
    print(text2art("BB84 Simulator", font="smslant"))
    print("="*console_width)
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
    
    # Parameter 2: Distance
    print("\n" + "-"*console_width)
    print("Fiber Optic Channel Distance:")
    print("  0 km   = No loss (ideal channel)")
    print("  25 km  = Urban QKD network")
    print("  50 km  = Metropolitan area")
    print("  100 km = Long-distance (challenging)")
    while True:
        try:
            distance_km = float(input("Enter fiber distance in km [0-150, default=25]: ") or "25")
            if 0 <= distance_km <= 150:
                break
            print("  [WARNING] Please enter a value between 0 and 150")
        except ValueError:
            print("  [WARNING] Invalid input. Please enter a number.")
    
    # Parameter 3: Interception rate
    print("\n" + "-"*console_width)
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
    
    # Parameter 4: Noise model (moved before target QBER)
    print("\n" + "-"*console_width)
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
        print("\n" + "-"*console_width)
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
    
    # Parameter 6: Target QBER (only if noise_type='none')
    target_qber = 0.0
    if noise_type == 'none':
        print("\n" + "-"*console_width)
        print("Target Artificial QBER (classical errors only):")
        print("  NOTE: Simulates detector noise, timing jitter, dark counts")
        print("  0.0 = No artificial errors (only Eve + photon loss)")
        print("  0.05 = 5% classical error rate")
        print("  0.11 = 11% (security threshold)")
        while True:
            try:
                target_qber = float(input("Enter target QBER [0.0-0.30, default=0.0]: ") or "0.0")
                if 0.0 <= target_qber <= 0.30:
                    break
                print("  [WARNING] Please enter a value between 0.0 and 0.30")
            except ValueError:
                print("  [WARNING] Invalid input. Please enter a decimal number.")
    else:
        print("\n[NOTE] Target QBER disabled (quantum noise model provides realistic errors)")
    
    # Run simulation
    print("\n" + "="*console_width)
    print("RUNNING SIMULATION...")
    print("="*console_width)
    
    sim = EnhancedBB84Protocol(
        n_qubits=n_qubits,
        interception_rate=interception_rate,
        target_qber=target_qber,
        noise_type=noise_type,
        noise_strength=noise_strength,
        distance_km=distance_km,
        verbose=True
    )
    
    result = sim.executeSim()
    
    # Visualization menu loop
    viz = BB84Visualizer()
    
    while True:
        print("\n" + "="*console_width)
        print("VISUALIZATION MENU")
        print("="*console_width)
        print("\nAvailable visualizations:")
        print("  1. QBER vs Interception Rate")
        print("  2. Sifted Key Distribution")
        print("  3. Basis Choice Heatmap")
        print("  4. Noise Model Comparison")
        print("  5. Security Threshold Analysis")
        print("  6. Secure Key Rate vs Distance")
        print("  7. Generate ALL visualizations")
        print("  0. Exit program")
        
        viz_choice = input("\nEnter your choice [0-7]: ") or "0"
        
        if viz_choice == '0':
            break
        elif viz_choice == '1':
            viz.plot_qber_vs_interception(distance_km=distance_km)
        elif viz_choice == '2':
            viz.plot_basis_matching_distribution(distance_km=distance_km)
        elif viz_choice == '3':
            viz.plot_basis_choice_heatmap(distance_km=distance_km)
        elif viz_choice == '4':
            viz.plot_noise_model_comparison(distance_km=distance_km)
        elif viz_choice == '5':
            viz.plot_security_threshold_analysis(distance_km=distance_km)
        elif viz_choice == '6':
            viz.plot_distance_vs_key_rate()
        elif viz_choice == '7':
            print("\nGenerating all visualizations...")
            viz.plot_qber_vs_interception(n_trials=15, distance_km=distance_km)
            viz.plot_basis_matching_distribution(n_simulations=80, distance_km=distance_km)
            viz.plot_basis_choice_heatmap(distance_km=distance_km)
            viz.plot_noise_model_comparison(distance_km=distance_km)
            viz.plot_security_threshold_analysis(n_trials=30, distance_km=distance_km)
            viz.plot_distance_vs_key_rate()
            print("\n[SUCCESS] All visualizations rendered!")
        else:
            print("  [WARNING] Invalid choice. Please enter a number between 0 and 7.")
    
    print("\n" + "="*console_width)
    print(text2art("EXITING"))
    print("="*console_width + "\n")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Run interactive mode
    interactive_simulation()
