# config reference

## modes

| Mode | Description |
|------|-------------|
| `single` | Run one protocol trial, print results |
| `sweep` | Sweep noise strength, plot QBER + key rate |
| `eve_sweep` | Sweep Eve interception rate |
| `protocol_comparison` | Same noise sweep across BB84/B92/E91 |

## params

| key | type | default | description |
| `mode` | string | `single` | execution mode |
| `protocol` | string | `bb84` | protocol: `bb84`, `b92`, `e91` |
| `protocols` | list | - | protocol list for `protocol_comparison` mode |
| `n_qubits` | int | `256` | qubits per trial |
| `n_trials` | int | `30` | independent trials per parameter point |
| `noise_type` | string | `none` | noise model |
| `noise_strength` | float | `0.0` | fixed noise strength |
| `noise_min` | float | `0.0` | sweep start |
| `noise_max` | float | `0.30` | sweep end |
| `noise_steps` | int | `21` | number of sweep points |
| `eve_rate` | float | `null` (null = no ve) | eve interception rate |
| `eve_min` | float | `0.0` | eve sweep start |
| `eve_max` | float | `1.0` | eve sweep end |
| `eve_steps` | int | `11` | eve sweep points |
| `e91_channel_topology` | string | `both` | `both` or `bob` (enables attack selection on each arm of the EPR pair) |
| `output_dir` | string | `./results` | output directory |
| `save_plots` | bool | `true` | save plots |
| `show_plots` | bool | `false` | display plots interactively |

## noise Types

`none`, `depolarizing`, `bitflip`, `phaseflip`, `amplitude_damping`, `phase_damping`
