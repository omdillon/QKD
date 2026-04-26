<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# analyse the system code that is currently in place, and make a report that compiles the list of changes to be in order to export the relevant data to extract for these plots. also suggest if there may be any bottle necks, currenlty the system outputs the plots in matlab but I can simply edit it to compile the data file.

Based on the system architecture shown in the uploaded files, extracting the required CSV data for your 3D plot is entirely feasible and aligns well with your current design patterns. The codebase is highly modular, separating configuration (`config.py`), execution logic (`benchmark.py`), protocol definition (`base.py`, `bb84.py`, etc.), and visualisation (`plotter.py`).

Here is a report outlining the required changes, expected bottlenecks, and an implementation strategy to extract the 3D surface data.

## System Code Analysis \& Implementation Strategy

Currently, the `BenchmarkRunner` in `benchmark.py` supports 1D parameter sweeps (`run_noise_sweep` and `run_eve_sweep`). It returns a `BenchmarkData` dataclass containing arrays of means and standard deviations, which are then passed to `QKDPlotter` via `main.py`.[^1][^2]

To generate the 2D parameter sweep over both Noise Strength and Eve Interception Rate, you will need to add a new execution mode and a new method to `BenchmarkRunner` to handle nested loops.

### Required Changes

#### 1. Update `config.py`

Add a new mode to `VALID_MODES` to support the 2D sweep.

- **Change:** Add `'surfacesweep'` to the `VALID_MODES` tuple.
- **Why:** The configuration loader strictly validates the `mode` parameter. It must be updated to accept the new configuration file type.[^3]


#### 2. Update `benchmark.py`

Create a new method to execute the nested parameter sweep.

- **Change:** Add `run_surface_sweep(self, protocol_class, noisetype, strengths, eve_rates, n_trials, n_qubits, ...)` to the `BenchmarkRunner` class.[^2]
- **Logic:** This method should initialize a 2D numpy array (e.g., `qber_results = np.zeros((len(strengths), len(eve_rates)))`). It will require a nested loop: the outer loop iterates over `strengths`, the inner loop iterates over `eve_rates`, and inside that, the protocol is instantiated and run `n_trials` times.[^2]
- **Return Type:** It should return a dictionary or a new `SurfaceBenchmarkData` dataclass, as the current `BenchmarkData` dataclass only expects 1D arrays for `parameter_values`.[^2]


#### 3. Update `main.py`

Add the routing logic to execute the new mode and handle CSV export.

- **Change:** Add `elif config.mode == 'surfacesweep': run_surface_sweep(config)` inside the `main()` function execution block.[^1]
- **Change:** Implement the `run_surface_sweep(config)` function in `main.py`. This function will call the new `BenchmarkRunner` method.[^1]
- **CSV Export Logic:** Instead of passing the output to `QKDPlotter` (since you intend to plot in MATLAB), add a block of pandas or pure CSV export code directly at the end of `run_surface_sweep(config)`. It should flatten the 2D arrays into a standard 3-column CSV format (Noise Strength, Eve Rate, Mean QBER).


#### 4. Create a new YAML Configuration File

- **Change:** Create `configs/bb84_surface.yaml`.
- **Content:** Set `mode: 'surfacesweep'`, `protocol: 'bb84'`, `noise_type: 'depolarizing'`, and define the min/max/steps for both noise (0 to 0.3, 30 steps) and eve (0 to 1.0, 25 steps). Set `n_trials: 20` and `n_qubits: 1000`.


### Potential Bottlenecks \& Simulator Constraints

**1. Qiskit Aer Simulator Overhead (The Primary Bottleneck)**
The current `EveInterceptor` creates intercept-resend circuits dynamically for every single protocol run by copying circuits and inserting measurement gates mid-flight. For a 30x25 grid with 20 trials, your code will invoke `protocol.run()` 15,000 times.[^4][^2]
Each time, `EveInterceptor.intercept()` calls `self.eve_backend.run(measure_circuits, shots=1)`. This means Qiskit's AerSimulator will be instantiated and torn down 15,000 times. While Qiskit Aer is fast for quantum execution, the *Python-level overhead* of submitting 15,000 individual 1-shot jobs will cause a significant time bottleneck.[^4]

*Mitigation:* Before running the full 30x25 sweep, test it on a 5x5 grid with 5 trials to gauge the execution time. If it is too slow, you may need to reduce your grid resolution to 20x20 or reduce the trials from 20 to 10. The Central Limit Theorem holds relatively well even at 10 trials if `n_qubits` is high (1000).[^5]

**2. Memory Consumption**
The system currently tracks raw data arrays for all operations (e.g., `sifted_key_alice`, `bob_results`) inside the `QKDResult` dataclass. For 15,000 runs at 1000 qubits each, keeping all 15,000 `QKDResult` objects in memory simultaneously would crash standard RAM limits.[^6]
*Mitigation:* Your `benchmark.py` handles this correctly by extracting the float `result.qber` and immediately discarding the heavy `QKDResult` object in each loop iteration. Ensure your new `run_surface_sweep` method strictly follows this pattern and only stores the final float averages in its 2D arrays, not the raw circuit outputs.[^2]