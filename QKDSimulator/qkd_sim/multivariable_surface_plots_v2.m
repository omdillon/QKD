% multivariable_surface_plots_v2.m
% Experiments 5 & 6 (v.2): BB84 and B92 QBER surface plots.
% Restricted parameter ranges, finer grid (31x41), threshold at z-axis midpoint.
%   Approach A - transparent threshold plane overlaid on the surface
%   Approach B - bicolour split colormap (blue/orange below, red above threshold)
%
% v.2 CSVs generated from:
%   configs/exp5_bb84_surface_v2.yaml  (noise 0-0.14, eve 0-0.60, 31x41 grid)
%   configs/exp6_b92_surface_v2.yaml   (noise 0-0.06, eve 0-0.30, 31x41 grid)

clear; clc; close all;

% -------------------------------------------------------------------------
% style constants
% -------------------------------------------------------------------------
FONT      = 'Times New Roman';
SZ_TITLE  = 20;
SZ_LABEL  = 18;
SZ_TICK   = 16;
SZ_LEGEND = 12;

C_BB84   = [0.055 0.212 0.373];
C_B92    = [1.000 0.584 0.000];
C_THRESH = [1.000 0.000 0.000];

THRESH_BB84 = 11;    % percent
THRESH_B92  = 6.5;   % percent

% z-axis limits — threshold at midpoint
ZLIM_BB84 = [0, 2 * THRESH_BB84];
ZLIM_B92  = [0, 2 * THRESH_B92];

% -------------------------------------------------------------------------
% data paths
% -------------------------------------------------------------------------
bb84_csv = 'C:\Users\dillo\OneDrive\Documents\NCL\Year 3\QKD\QKDSimulator\results\sim runs v.5 - final experiments\exp5_bb84_surface_v2\bb84_surface_qber.csv';
b92_csv  = 'C:\Users\dillo\OneDrive\Documents\NCL\Year 3\QKD\QKDSimulator\results\sim runs v.5 - final experiments\exp6_b92_surface_v2\b92_surface_qber.csv';

% =========================================================================
% BB84  (Experiment 5 v.2)
% Grid: 31 noise steps (0-0.14) x 41 eve steps (0-0.60)
% =========================================================================
noise_vals_bb84 = linspace(0, 0.14, 31);
eve_vals_bb84   = linspace(0, 0.60, 41);
[Eve_bb84, Noise_bb84] = meshgrid(eve_vals_bb84, noise_vals_bb84);

if ~isfile(bb84_csv)
    warning('BB84 v.2 CSV not found: %s\nRun exp5_bb84_surface_v2.yaml first.', bb84_csv);
else
    T_bb84 = readtable(bb84_csv);
    Z_bb84 = reshape(T_bb84.qber_mean, 41, 31)' * 100;   % 31x41, percent

    % Approach A
    fig_bb84_A = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax = axes(fig_bb84_A);
    s_data = surf(ax, Eve_bb84, Noise_bb84, Z_bb84, 'EdgeColor', 'none');
    colormap(ax, parula);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_BB84); clim(ax, ZLIM_BB84);
    cb.Ticks = linspace(ZLIM_BB84(1), ZLIM_BB84(2), 5);
    hold(ax, 'on');
    s_plane = surf(ax, Eve_bb84, Noise_bb84, THRESH_BB84 * ones(size(Z_bb84)), ...
        'FaceAlpha', 0.25, 'FaceColor', C_THRESH, 'EdgeColor', 'none');
    xlabel(ax, 'Eve Interception Rate', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',        'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'QBER (%)',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'BB84 Protocol - Depolarising Channel - QBER Surface', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_data, s_plane], ...
        {'QBER Surface', sprintf('Security Threshold (%.0f%%)', THRESH_BB84)}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Box', 'on', 'BackgroundAlpha', 0.8);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3;
    view(ax, [-45 30]);
    out_A = fullfile(fileparts(bb84_csv), 'exp5_bb84_surface_qber_v2_approach_A.png');
    exportgraphics(fig_bb84_A, out_A, 'Resolution', 300);
    fprintf('Saved: %s\n', out_A);

    % Approach B
    fig_bb84_B = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax = axes(fig_bb84_B);
    surf(ax, Eve_bb84, Noise_bb84, Z_bb84, 'EdgeColor', 'none');
    n_below = 128; n_above = 128;
    cmap_below = [linspace(0.05, 0.53, n_below)', linspace(0.21, 0.81, n_below)', linspace(0.37, 0.98, n_below)'];
    cmap_above = [linspace(1.00, 1.00, n_above)', linspace(0.60, 0.00, n_above)', linspace(0.60, 0.00, n_above)'];
    colormap(ax, [cmap_below; cmap_above]);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_BB84); clim(ax, ZLIM_BB84);
    hold(ax, 'on');
    plot3(ax, [0 0.60 0.60 0 0], [0 0 0.14 0.14 0], repmat(THRESH_BB84, 1, 5), ...
        '--', 'Color', [C_THRESH 0.7], 'LineWidth', 1.5);
    xlabel(ax, 'Eve Interception Rate', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',        'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'QBER (%)',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'BB84 Protocol - Depolarising Channel - QBER Surface', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3;
    view(ax, [-45 30]);
    out_B = fullfile(fileparts(bb84_csv), 'exp5_bb84_surface_qber_v2_approach_B.png');
    exportgraphics(fig_bb84_B, out_B, 'Resolution', 300);
    fprintf('Saved: %s\n', out_B);
end

% =========================================================================
% B92  (Experiment 6 v.2)
% Grid: 31 noise steps (0-0.06) x 41 eve steps (0-0.30)
% =========================================================================
noise_vals_b92 = linspace(0, 0.06, 31);
eve_vals_b92   = linspace(0, 0.30, 41);
[Eve_b92, Noise_b92] = meshgrid(eve_vals_b92, noise_vals_b92);

if ~isfile(b92_csv)
    warning('B92 v.2 CSV not found: %s\nRun exp6_b92_surface_v2.yaml first.', b92_csv);
else
    T_b92 = readtable(b92_csv);
    Z_b92 = reshape(T_b92.qber_mean, 41, 31)' * 100;   % 31x41, percent

    % Approach A
    fig_b92_A = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax = axes(fig_b92_A);
    s_data = surf(ax, Eve_b92, Noise_b92, Z_b92, 'EdgeColor', 'none');
    colormap(ax, parula);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_B92); clim(ax, ZLIM_B92);
    cb.Ticks = linspace(ZLIM_B92(1), ZLIM_B92(2), 5);
    hold(ax, 'on');
    s_plane = surf(ax, Eve_b92, Noise_b92, THRESH_B92 * ones(size(Z_b92)), ...
        'FaceAlpha', 0.25, 'FaceColor', C_THRESH, 'EdgeColor', 'none');
    xlabel(ax, 'Eve Interception Rate', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',        'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'QBER (%)',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'B92 Protocol - Depolarising Channel - QBER Surface', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_data, s_plane], ...
        {'QBER Surface', sprintf('Security Threshold (%.1f%%)', THRESH_B92)}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Box', 'on', 'BackgroundAlpha', 0.8);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3;
    view(ax, [-45 30]);
    out_A = fullfile(fileparts(b92_csv), 'exp6_b92_surface_qber_v2_approach_A.png');
    exportgraphics(fig_b92_A, out_A, 'Resolution', 300);
    fprintf('Saved: %s\n', out_A);

    % Approach B
    fig_b92_B = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax = axes(fig_b92_B);
    surf(ax, Eve_b92, Noise_b92, Z_b92, 'EdgeColor', 'none');
    n_below = 128; n_above = 128;
    cmap_below = [linspace(1.00, 1.00, n_below)', linspace(0.95, 0.58, n_below)', linspace(0.80, 0.00, n_below)'];
    cmap_above = [linspace(1.00, 1.00, n_above)', linspace(0.60, 0.00, n_above)', linspace(0.60, 0.00, n_above)'];
    colormap(ax, [cmap_below; cmap_above]);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_B92); clim(ax, ZLIM_B92);
    hold(ax, 'on');
    plot3(ax, [0 0.30 0.30 0 0], [0 0 0.06 0.06 0], repmat(THRESH_B92, 1, 5), ...
        '--', 'Color', [C_THRESH 0.7], 'LineWidth', 1.5);
    xlabel(ax, 'Eve Interception Rate', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',        'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'QBER (%)',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'B92 Protocol - Depolarising Channel - QBER Surface', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3;
    view(ax, [-45 30]);
    out_B = fullfile(fileparts(b92_csv), 'exp6_b92_surface_qber_v2_approach_B.png');
    exportgraphics(fig_b92_B, out_B, 'Resolution', 300);
    fprintf('Saved: %s\n', out_B);
end
