% multivariable_surface_plots_v3.m
% Experiments 5 & 6 (v.3): BB84 and B92 QBER surface plots.
% One variant per protocol:
%   Standard - gradient colormap + translucent threshold plane, raw data
%
% v.3 CSVs generated from:
%   configs/exp5_bb84_surface_v3.yaml (noise 0-0.30, eve 0-0.60, 31x41 grid)
%   configs/exp6_b92_surface_v3.yaml (noise 0-0.15, eve 0-0.30, 31x41 grid)

clear; clc; close all;

% -------------------------------------------------------------------------
% style constants
% -------------------------------------------------------------------------
FONT      = 'Times New Roman';
SZ_TITLE  = 20;
SZ_LABEL  = 18;
SZ_TICK   = 16;
SZ_LEGEND = 12;

THRESH_BB84 = 11;    % percent
THRESH_B92  = 6.5;   % percent

% z-axis limits
ZLIM_BB84 = [0, 2 * THRESH_BB84];   % [0, 22]
ZLIM_B92  = [0, 2 * THRESH_B92];    % [0, 13]

% Threshold plane colours - contrasting with both surface colour ranges
C_PLANE_BB84 = [1.00, 0.80, 0.00];   % golden yellow  (contrasts blue and red)
C_PLANE_B92  = [0.65, 0.00, 0.90];   % bright violet  (contrasts teal and red)

% constrain axes so 3D tick labels don't bleed into colorbar
AX_POS = [0.07, 0.08, 0.70, 0.82];    % [left, bottom, width, height] normalised
CB_POS = [0.84, 0.14, 0.022, 0.66];   % colorbar fixed well right of axes

BORDER_PX = 42;   % white border width

% -------------------------------------------------------------------------
% Data paths (v.3 results)
% -------------------------------------------------------------------------
bb84_csv = 'C:\Users\dillo\OneDrive\Documents\NCL\Year 3\QKD\QKDSimulator\results\sim runs v.5 - complete experiments\exp5_bb84_surface_v3\bb84_surface_qber.csv';
b92_csv  = 'C:\Users\dillo\OneDrive\Documents\NCL\Year 3\QKD\QKDSimulator\results\sim runs v.5 - complete experiments\exp6_b92_surface_v3\b92_surface_qber.csv';

% =========================================================================
% BB84  (Experiment 5 v.3)
% Grid: 31 noise steps (0-0.30) x 41 eve steps (0-0.60)
% =========================================================================
noise_vals_bb84 = linspace(0, 0.30, 31);
eve_vals_bb84   = linspace(0, 0.60, 41);
[Eve_bb84, Noise_bb84] = meshgrid(eve_vals_bb84, noise_vals_bb84);   % 31x41

if ~isfile(bb84_csv)
    warning('BB84 v.3 CSV not found: %s\nRun exp5_bb84_surface_v3.yaml first.', bb84_csv);
else
    T_bb84 = readtable(bb84_csv);
    Z_bb84 = reshape(T_bb84.qber_mean, 41, 31)' * 100;   % 31x41, percent
    Z_bb84 = min(Z_bb84, ZLIM_BB84(2));   % clamp to zlim ceiling to prevent face-clipping artefacts

    % Gradient colormap: dark blue -> sky blue -> coral -> dark crimson
    key_colors_bb84 = [0.02, 0.04, 0.25;
                       0.15, 0.65, 1.00;
                       1.00, 0.40, 0.30;
                       0.70, 0.00, 0.00];
    cmap_bb84 = interp1(linspace(0,1,4), key_colors_bb84, linspace(0,1,256));

    % BB84 Standard (gradient + plane, raw data) 
    fig_bb84 = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax = axes(fig_bb84);
    s_data = surf(ax, Eve_bb84, Noise_bb84, Z_bb84, 'EdgeColor', 'none');
    colormap(ax, cmap_bb84);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_BB84); clim(ax, ZLIM_BB84);
    cb.Ticks = linspace(ZLIM_BB84(1), ZLIM_BB84(2), 5);
    hold(ax, 'on');
    s_plane = surf(ax, Eve_bb84, Noise_bb84, THRESH_BB84 * ones(size(Z_bb84)), ...
        'FaceAlpha', 0.25, 'FaceColor', C_PLANE_BB84, 'EdgeColor', 'none');
    xlabel(ax, 'Eve Interception Rate', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',        'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'QBER (%)',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'BB84 Protocol - Depolarising Channel - QBER Surface', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_data, s_plane], ...
        {'QBER Surface', sprintf('Security Threshold (%.0f%%)', THRESH_BB84)}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northwest', ...
        'Box', 'on', 'BackgroundAlpha', 0.8);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3;
    view(ax, [30 30]);
    drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(bb84_csv), 'exp5_bb84_surface_qber_v3.png');
    exportgraphics(fig_bb84, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    rotate3d(fig_bb84, 'on');
    fprintf('Saved: %s\n', out);
end

% =========================================================================
% B92  (Experiment 6 v.3)
% Grid: 31 noise steps (0-0.15) x 41 eve steps (0-0.30)
% =========================================================================
noise_vals_b92 = linspace(0, 0.15, 31);
eve_vals_b92   = linspace(0, 0.30, 41);
[Eve_b92, Noise_b92] = meshgrid(eve_vals_b92, noise_vals_b92);   % 31x41

if ~isfile(b92_csv)
    warning('B92 v.3 CSV not found: %s\nRun exp6_b92_surface_v3.yaml first.', b92_csv);
else
    T_b92 = readtable(b92_csv);
    Z_b92 = reshape(T_b92.qber_mean, 41, 31)' * 100;   % 31x41, percent
    Z_b92 = min(Z_b92, ZLIM_B92(2));    % clamp to zlim ceiling to prevent face-clipping artefacts

    % Gradient colormap: dark teal -> bright mint -> coral -> dark crimson
    key_colors_b92 = [0.00, 0.30, 0.35;
                      0.25, 0.88, 0.72;
                      1.00, 0.40, 0.30;
                      0.70, 0.00, 0.00];
    cmap_b92 = interp1(linspace(0,1,4), key_colors_b92, linspace(0,1,256));

    % B92 Standard (gradient + plane, raw data) 
    fig_b92 = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax = axes(fig_b92);
    s_data = surf(ax, Eve_b92, Noise_b92, Z_b92, 'EdgeColor', 'none');
    colormap(ax, cmap_b92);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_B92); clim(ax, ZLIM_B92);
    cb.Ticks = linspace(ZLIM_B92(1), ZLIM_B92(2), 5);
    hold(ax, 'on');
    s_plane = surf(ax, Eve_b92, Noise_b92, THRESH_B92 * ones(size(Z_b92)), ...
        'FaceAlpha', 0.25, 'FaceColor', C_PLANE_B92, 'EdgeColor', 'none');
    xlabel(ax, 'Eve Interception Rate', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',        'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'QBER (%)',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'B92 Protocol - Depolarising Channel - QBER Surface', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_data, s_plane], ...
        {'QBER Surface', sprintf('Security Threshold (%.1f%%)', THRESH_B92)}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northwest', ...
        'Box', 'on', 'BackgroundAlpha', 0.8);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3;
    view(ax, [30 30]);
    drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(b92_csv), 'exp6_b92_surface_qber_v3.png');
    exportgraphics(fig_b92, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    rotate3d(fig_b92, 'on');
    fprintf('Saved: %s\n', out);
end

% -------------------------------------------------------------------------
% pad PNGs with a white border
% -------------------------------------------------------------------------
function add_white_border(path, border_px)
    img = imread(path);
    [h, w, c] = size(img);
    img2 = uint8(255 * ones(h + 2*border_px, w + 2*border_px, c));
    img2(border_px+1:border_px+h, border_px+1:border_px+w, :) = img;
    imwrite(img2, path);
end
