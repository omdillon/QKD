import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

class BB84Protocol:
    """  
    attributes:
    - n_qubits: number of qubits to be sent
    - backend_sim: qiskit AER simulator for noise environments
    - interception_rate: probability that Eve intercepts a qubit (0.0 to 1.0)
        0.0 = no eavesdropping (secure channel)
        1.0 = full eavesdropping (insecure channel)
    """

    def __init__(self, n_qubits=100, interception_rate=0.0):
        """
        arguments:
        - n_qubits: Total number of bits/qubits to transmit
        - interception_rate:
            0.0 = No Eavesdropping (Secure Channel)
            1.0 = Full Eavesdropping (Insecure Channel)
        """
        self.n_qubits = n_qubits
        self.interception_rate = interception_rate
        self.backend_sim = AerSimulator()
        
        # protocol data storage
        self.alice_bits = []      # Alices raw random bits (0 or 1)
        self.alice_bases = []     # Alices bases (0=Z-basis/Standard, 1=X-basis/Hadamard)
        self.bob_bases = []       # Bobs bases (0=Z-basis, 1=X-basis)
        self.bob_results = []     # Bobs measurement results
        self.eve_presence = []    # Track which qubits Eve intercepted

    def alicePreparation(self):
        """
        random bit/base generation, qubit prep by ALice
        output: QuantumCircuit objects representing the photon stream
        """
        print(f"\n--- Step 1: Alice prepares {self.n_qubits} qubits ---")
        
        # generates random bits and bases for Alice
        # randint(2) generates 0 or 1
        self.alice_bits = np.random.randint(2, size=self.n_qubits)
        self.alice_bases = np.random.randint(2, size=self.n_qubits)
        
        qubit_stream = []
        
        for i in range(self.n_qubits):

            # 1 qubit, 1 classical bit for measurement
            qc = QuantumCircuit(1, 1) 
            
            # encode the bit
            # if bit is 1, apply X gate to flip |0> to |1>
            if self.alice_bits[i] == 1:
                # .x = X gate, arg = qubit to be proessed
                qc.x(0) 
            
            # encode the basis
            # if basis is 1 (Hadamard/X-basis), apply H gate
            # if basis is 0 (Standard/Z-basis), do nothing (leave as Z)
            if self.alice_bases[i] == 1:
                # .h = H gate,  arg = qubit to be proessed
                qc.h(0)
            
            # add the updated bits to the stream
            qubit_stream.append(qc)
            
        return qubit_stream

    def quantumChannel(self, qubit_stream):
        """
        channel simulation, adds the concept of an eavesdropper to the channel 
        if Eve is present, qubits are intercepted, measured, and resent based on interception_rate
        """
        print(f"\n--- Step 2: Transmission (Eve interception rate: {self.interception_rate}) ---")
        
        intercepted_stream = []
        # track interception for analysis
        self.eve_presence = [False] * self.n_qubits 
        
        for i, qc in enumerate(qubit_stream):
            # determine if Eve intercepts this specific qubit
            if np.random.rand() < self.interception_rate:
                self.eve_presence[i] = True
                
                # Eve chooses a random basis to measure
                eve_basis = np.random.randint(2)
                
                # applying basis change if Eve chooses Hadamard base (1)
                if eve_basis == 1:
                    qc.h(0)
                
                # Eve measures the qubit
                qc.measure(0, 0)
                
                # run the simulation to collapse the state as Eve physically measures it before Bob
                instance = self.backend_sim.run(qc, shots=1, memory=True)
                result = instance.result().get_memory()[0] # '0' or '1'
                
                # Eve attempts to resend the qubit she measured by creating a new one, as the original was destroyed in measurement
                new_qc = QuantumCircuit(1, 1)
                
                if result == '1':
                    new_qc.x(0)
                
                #EEve encodes it back in the basis she chose for measurement
                if eve_basis == 1:
                    new_qc.h(0)
                    
                intercepted_stream.append(new_qc)

            else:
                # qubit passes onto channel untouched if Eve did not choose to measure
                intercepted_stream.append(qc)
                
        return intercepted_stream

    def bobMeasurement(self, incoming_stream):
        """
        Bob chooses random bases and measures the incoming qubits
        """
        print(f"\n--- Step 3: Bob measures qubits ---")
        self.bob_bases = np.random.randint(2, size=self.n_qubits)
        self.bob_results = []
        
        for i, qc in enumerate(incoming_stream):
            
            # Bob applies his basis choice
            if self.bob_bases[i] == 1:
                qc.h(0)
            
            # Bob measures
            qc.measure(0, 0)
            
            # execute the circuit
            # the real system would not be re-run if previously Eve ran it, Qiskit simulations require circuit objects to be appended
            # if Eve collapsed the channel earlier, this system replaced the circuit object with, new_qc

            # instance of the AER simulation
            instance = self.backend_sim.run(qc, shots=1, memory=True)
            measured_bit = int(instance.result().get_memory()[0])
            self.bob_results.append(measured_bit)

    def postProcessing(self):
        """
        sifting phase: Alice and Bob publicly compare bases, but not bits
        the bits where bases are matched are kept
        the QBER is calculated from this matching process
        """
        print(f"\n--- Step 4: Sifting and QBER Calculation ---")
        
        sifted_key_alice = []
        sifted_key_bob = []
        match_indices = []
        
        for i in range(self.n_qubits):

            # onlt matched bit bases are kept
            if self.alice_bases[i] == self.bob_bases[i]:
                sifted_key_alice.append(self.alice_bits[i])
                sifted_key_bob.append(self.bob_results[i])
                match_indices.append(i)
                
        # QBER calculation
        # errors occur when bases match, but bits do not, due to Eve's measurement
        errors = 0
        total_sifted = len(sifted_key_alice)
        
        if total_sifted == 0:
            print("No bases matched (Unlikely with sufficient qubits)")
            return
            
        for k in range(total_sifted):
            if sifted_key_alice[k] != sifted_key_bob[k]:
                errors += 1
        
        qber = errors / total_sifted
        
        print(f"Total Qubits Sent: {self.n_qubits}")
        print(f"Sifted Key Length: {total_sifted} (approx 50% of sent)")
        print(f"Errors found:      {errors}")
        print(f"Calculated QBER:   {qber:.4f} ({qber*100:.2f}%)")
        
        # theoretical max safe QBER is ~11% if exceeded, assume eavesdropper
        if qber > 0.11:
            print("\n[ALERT] High QBER detected! Channel is insecure. Communication aborted.")
        else:
            print("\n[SUCCESS] QBER is within safety limits. Key exchange successful.")

    def executeSim(self):
        """
        Orchestrates the full protocol steps.
        """
        qubits = self.alicePreparation()
        qubits = self.quantumChannel(qubits)
        self.bobMeasurement(qubits)
        self.postProcessing()

# --- Execution Examples ---

print("==========================================")
print("SCENARIO 1: Secure Channel (No Eve)")
print("==========================================")
sim_secure = BB84Protocol(n_qubits=100, interception_rate=0.0)
sim_secure.executeSim()

print("\n==========================================")
print("SCENARIO 2: Eavesdropper Present (50% Interception)")
print("==========================================")
# Eve tries to listen to half the conversation
sim_hacked = BB84Protocol(n_qubits=100, interception_rate=0.5) 
sim_hacked.executeSim()

print("\n==========================================")
print("SCENARIO 3: Aggressive Eavesdropper (100% Interception)")
print("==========================================")
# Eve intercepts everything
sim_full_hack = BB84Protocol(n_qubits=100, interception_rate=1.0)
sim_full_hack.executeSim()
