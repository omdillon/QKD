"""stylesheet constants for the system"""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class PlotStyle:

    # fonts
    font_family: str = "Times New Roman"
    font_size_base: int = 14
    font_size_axis_label: int = 18
    font_size_title: int = 20
    font_size_tick: int = 16
    font_size_legend: int = 12
    font_weight_title: str = "bold"
    font_weight_axis_label: str = "bold"

    # matplotlib base style
    mpl_style: str = "seaborn-v0_8-whitegrid"

    # DPI and export quality seettings
    display_dpi: int = 100
    save_dpi: int = 300
    save_bbox: str = "tight"
    save_facecolor: str = "white"
    save_edgecolor: str = "none"

    # noise model colours
    noise_colours: Dict[str, str] = field(default_factory=lambda: {'none': '#0e365f','depolarizing': '#dd1634'})
    default_colour: str = '#0e365f'

    # noise model markers
    noise_markers: Dict[str, str] = field(default_factory=lambda: {'none': 'o','depolarizing': 's'})
    default_marker: str = 'o'

    # protocol performance curve colours
    protocol_colours: Dict[str, str] = field(default_factory=lambda: {'BB84': '#0e365f','B92':  '#22a043','E91':  '#ff9500'})
    protocol_markers: Dict[str, str] = field(default_factory=lambda: {'BB84': 's','B92':  '^','E91':  'D'})

    # figure sizes 
    figsize_single: Tuple[float, float] = (10, 6)
    figsize_comparison: Tuple[float, float] = (12, 7)

    # errorbar styling
    errorbar_capsize: float = 4
    errorbar_capthick: float = 1.5
    errorbar_linewidth: float = 2
    errorbar_markersize: float = 7
    errorbar_alpha: float = 0.9

    # theory lines (old system only)
    theory_linestyle: str = ":"
    theory_linewidth: float = 2
    theory_alpha: float = 0.7

    # security threshold lines
    threshold_colour: str = "#ff0000"
    threshold_linestyle_horizontal: str = "--"
    threshold_linestyle_vertical: str = ":"
    threshold_linewidth: float = 1.5
    threshold_alpha_horizontal: float = 0.7
    threshold_alpha_vertical: float = 0.6

    # grid and legend settings
    grid_alpha: float = 0.3
    legend_framealpha: float = 0.8
    legend_loc_qber: str = "upper left"
    legend_loc_keyrate: str = "upper center"


    # title padding
    title_pad: int = 15

    # param accessor method
    def get_rcparams(self) -> dict:
        return {
            'font.family': 'serif',
            'font.serif': [self.font_family],
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
