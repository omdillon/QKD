"""
Central stylesheet for all QKD simulation plots.

Edit STYLE below to restyle every plot produced by QKDPlotter.

    from qkd_sim.STYLESHEET import STYLE
    STYLE.font_family = 'Arial'
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class PlotStyle:
    """All visual parameters for QKD plots."""

    # Fonts
    font_family: str = "DM Sans"
    font_size_base: int = 16
    font_size_axis_label: int = 20
    font_size_title: int = 22
    font_size_tick: int = 18
    font_size_legend: int = 14
    font_weight_title: str = "bold"
    font_weight_axis_label: str = "bold"

    # Matplotlib base style
    mpl_style: str = "seaborn-v0_8-whitegrid"

    # DPI and export
    display_dpi: int = 100
    save_dpi: int = 300
    save_bbox: str = "tight"
    save_facecolor: str = "white"
    save_edgecolor: str = "none"

    # Noise model colours
    noise_colours: Dict[str, str] = field(default_factory=lambda: {
        'none': '#0e365f',
        'depolarizing': '#dd1634',
        'bitflip': '#e8594d',
        'phaseflip': '#1a5c8a',
        'amplitude_damping': '#a01228',
        'phase_damping': '#2980b9',
    })
    default_colour: str = '#dd1634'

    # Noise model markers
    noise_markers: Dict[str, str] = field(default_factory=lambda: {
        'none': 'o',
        'depolarizing': 's',
        'bitflip': '^',
        'phaseflip': 'D',
        'amplitude_damping': 'v',
        'phase_damping': 'P',
    })
    default_marker: str = 'o'

    # Protocol colours (multi-protocol comparison)
    protocol_colours: Dict[str, str] = field(default_factory=lambda: {
        'BB84': '#dd1634',
        'B92':  '#1a5c8a',
        'E91':  '#22a043',
    })
    protocol_markers: Dict[str, str] = field(default_factory=lambda: {
        'BB84': 's',
        'B92':  '^',
        'E91':  'D',
    })

    # Figure sizes (width, height in inches)
    figsize_single: Tuple[float, float] = (10, 6)
    figsize_comparison: Tuple[float, float] = (12, 7)

    # Errorbar styling
    errorbar_capsize: float = 4
    errorbar_capthick: float = 1.5
    errorbar_linewidth: float = 2
    errorbar_markersize: float = 7
    errorbar_alpha: float = 0.9

    # Theory overlay lines
    theory_linestyle: str = ":"
    theory_linewidth: float = 2
    theory_alpha: float = 0.7

    # Security threshold lines
    threshold_colour: str = "#22e300"
    threshold_linestyle_horizontal: str = "--"
    threshold_linestyle_vertical: str = ":"
    threshold_linewidth: float = 1.5
    threshold_alpha_horizontal: float = 0.7
    threshold_alpha_vertical: float = 0.6

    # Grid and legend
    grid_alpha: float = 0.3
    legend_framealpha: float = 0.9
    legend_loc_qber: str = "upper left"
    legend_loc_keyrate: str = "center right"

    # Title padding
    title_pad: int = 15

    def get_rcparams(self) -> dict:
        """Return a dict suitable for plt.rcParams.update()."""
        return {
            'font.family': self.font_family,
            'font.size': self.font_size_base,
            'axes.labelsize': self.font_size_axis_label,
            'axes.titlesize': self.font_size_title,
            'xtick.labelsize': self.font_size_tick,
            'ytick.labelsize': self.font_size_tick,
            'legend.fontsize': self.font_size_legend,
            'figure.dpi': self.display_dpi,
            'savefig.dpi': self.save_dpi,
            'savefig.bbox': self.save_bbox,
        }


STYLE = PlotStyle()
