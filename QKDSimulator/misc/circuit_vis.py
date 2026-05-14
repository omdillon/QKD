"""
E91 quantum circuit diagram — Qiskit mpl backend with channel overlay.
Run directly to produce e91_circuit.png.
"""
import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, ClassicalRegister, Gate

_BLUE  = '#1B4D9E'
_RED   = '#D93B3B'
_GREY  = '#6E6E6E'
_WHITE = '#FFFFFF'

QISKIT_STYLE = {
    'displaycolor': {
        'h':       (_BLUE, _WHITE),
        'cx':      (_BLUE, _WHITE),
        'x':       (_BLUE, _WHITE),
        'z':       (_BLUE, _WHITE),
        'id':      (_BLUE, _WHITE),
        'ry':      (_RED,  _WHITE),
        'measure': (_GREY, _WHITE),
    },
    'fontsize':    8,
    'subfontsize': 6,
}

CHANNEL_BG = '#D6E8FA'
ALICE_COL  = '#D93B3B'
BOB_COL    = '#22a043'
SOURCE_COL = '#1B4D9E'


def _find_barrier_xs(ax):
    """Deduplicated x-centres of Qiskit barrier rectangles."""
    from matplotlib.patches import Rectangle as Rect
    ylim = ax.get_ylim()
    span = abs(ylim[1] - ylim[0])
    xs = []
    for p in ax.patches:
        if not isinstance(p, Rect):
            continue
        bb = p.get_bbox()
        if abs(bb.height) > span * 0.20 and 0 < abs(bb.width) < 0.7:
            xs.append(bb.x0 + bb.width / 2)
    xs.sort()
    merged = []
    for x in xs:
        if not merged or x - merged[-1] > 0.4:
            merged.append(x)
    return merged


def _find_qubit_wire_ys(ax):
    """Y-coordinates of the two longest horizontal lines (qubit wires)."""
    xlim = ax.get_xlim()
    circuit_width = xlim[1] - xlim[0]
    candidates = []
    for line in ax.lines:
        xd, yd = line.get_xdata(), line.get_ydata()
        if len(xd) >= 2 and len(set(yd)) == 1:
            span = max(xd) - min(xd)
            if span > circuit_width * 0.35:
                candidates.append((float(yd[0]), span))
    candidates.sort(key=lambda t: t[1], reverse=True)
    ys = sorted({t[0] for t in candidates[:2]}, reverse=True)
    return ys


def _label_box(ax, x, y, text, color, fontsize=12):
    ax.text(x, y, text,
            ha='center', va='center',
            color=_WHITE, fontsize=fontsize, fontweight='bold',
            fontfamily='Times New Roman',
            bbox=dict(boxstyle='round,pad=0.4',
                      facecolor=color, edgecolor=_WHITE, lw=1.5),
            zorder=9, clip_on=False)


def _add_overlay(ax, x_bar1, x_bar2):
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_top, y_bot = max(ylim), min(ylim)

    # channel shaded box
    ax.add_patch(Rectangle(
        (x_bar1, y_bot + 0.05), x_bar2 - x_bar1, y_top - y_bot - 0.1,
        facecolor=CHANNEL_BG, alpha=0.9, zorder=0, clip_on=False,
    ))

    # wavy line between qubit wires
    wire_ys = _find_qubit_wire_ys(ax)
    if len(wire_ys) >= 2:
        wave_cy = (wire_ys[0] + wire_ys[1]) / 2
    else:
        wave_cy = y_bot + (y_top - y_bot) * 0.60

    wx = np.linspace(x_bar1 + 0.10, x_bar2 - 0.22, 250)
    wy = wave_cy + 0.10 * np.sin(
        2 * np.pi * (wx - x_bar1) / (x_bar2 - x_bar1) * 3.5)
    ax.plot(wx, wy, color='#4477AA', lw=2.0, alpha=0.85, zorder=3)
    ax.annotate('', xy=(wx[-1] + 0.13, wy[-1]), xytext=(wx[-1], wy[-1]),
                arrowprops=dict(arrowstyle='->', color='#4477AA', lw=1.6),
                zorder=4)

    src_x  = (xlim[0] + x_bar1) / 2
    meas_x = (x_bar2  + xlim[1]) / 2

    _label_box(ax, src_x,  y_top + 0.6, 'Entanglement Source', SOURCE_COL)
    _label_box(ax, meas_x, y_top + 0.6, 'Alice (Measure)',      ALICE_COL)
    _label_box(ax, meas_x, y_bot - 0.6, 'Bob (Measure)',        BOB_COL)

    ax.text((x_bar1 + x_bar2) / 2, y_bot - 0.6,
            'Quantum Channel\n(noise applied here)',
            ha='center', va='center', fontsize=9, fontstyle='italic',
            color='#2255AA', fontfamily='Times New Roman',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF4FD',
                      edgecolor='#6688BB', lw=1.0),
            zorder=9, clip_on=False)

    ax.set_ylim(y_bot - 1.5, y_top + 1.2)


def main():
    q  = QuantumRegister(2, 'q')
    c0 = ClassicalRegister(1, 'c_0')
    c1 = ClassicalRegister(1, 'c_1')

    # use Gate with label so Qiskit doesn't render the param name separately
    ry_a = Gate('ry', 1, [], label='RY(θ_a)')
    ry_b = Gate('ry', 1, [], label='RY(θ_b)')

    qc = QuantumCircuit(q, c0, c1)
    qc.h(0)
    qc.cx(0, 1)
    qc.x(0)
    qc.z(0)
    qc.barrier()
    qc.id(0)   # channel noise — Alice's qubit  (both topology)
    qc.id(1)   # channel noise — Bob's qubit    (both topology)
    qc.barrier()
    qc.append(ry_a, [0])
    qc.append(ry_b, [1])
    qc.measure(q[0], c0[0])
    qc.measure(q[1], c1[0])

    fig = qc.draw(
        output='mpl',
        style=QISKIT_STYLE,
        fold=-1,
        scale=1.8,
        initial_state=False,
        plot_barriers=True,
    )
    ax = fig.axes[0]

    barriers = _find_barrier_xs(ax)
    print(f'Barriers at x = {barriers}')

    if len(barriers) >= 2:
        x_bar1, x_bar2 = barriers[0], barriers[1]
    else:
        xl, xr = ax.get_xlim()
        w = xr - xl
        x_bar1 = xl + w * 0.46
        x_bar2 = xl + w * 0.60
        print('Warning: fallback barrier positions used.')

    _add_overlay(ax, x_bar1, x_bar2)

    out = 'e91_circuit.png'
    fig.savefig(out, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f'Saved: {out}')


if __name__ == '__main__':
    main()
