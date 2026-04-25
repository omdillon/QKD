# Configuration Reference

All config files use flat YAML (no nesting). Copy `template.yaml` and uncomment the parameters you need.

## Modes

| Mode | Description |
|------|-------------|
| `single` | Run one protocol trial, print results |
| `sweep` | Sweep noise strength, plot QBER + key rate |
| `eve_sweep` | Sweep Eve interception rate |
| `protocol_comparison` | Same noise sweep across BB84/B92/E91 |

## Parameters

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `mode` | string | `single` | Execution mode (required) |
| `protocol` | string | `bb84` | Protocol: `bb84`, `b92`, `e91` |
| `protocols` | list | — | Protocol list for `protocol_comparison` mode |
| `n_qubits` | int | `256` | Qubits per trial |
| `n_trials` | int | `30` | Independent trials per parameter point |
| `noise_type` | string | `none` | Noise model (see below) |
| `noise_strength` | float | `0.0` | Fixed noise strength (single mode) |
| `noise_min` | float | `0.0` | Sweep start |
| `noise_max` | float | `0.30` | Sweep end |
| `noise_steps` | int | `21` | Number of sweep points |
| `eve_rate` | float | `null` | Eve interception rate (null = no Eve) |
| `eve_min` | float | `0.0` | Eve sweep start |
| `eve_max` | float | `1.0` | Eve sweep end |
| `eve_steps` | int | `11` | Eve sweep points |
| `e91_channel_topology` | string | `both` | `both` or `bob` (E91 only) |
| `output_dir` | string | `./results` | Plot output directory |
| `save_plots` | bool | `true` | Save plots to disk |
| `show_plots` | bool | `false` | Display plots interactively |

## Noise Types

`none`, `depolarizing`, `bitflip`, `phaseflip`, `amplitude_damping`, `phase_damping`
