% multivariable_surface_plots_v4.m
% Experiments 5 & 6 (v.4): BB84 and B92 surface plots — three plot types per protocol.
% Six plots per protocol (12 total):
%   1. QBER surface             — raw
%   2. QBER surface             — Gaussian smoothed
%   3. Mutual Information       — raw  (two surfaces: I(A;B) and I(A;E))
%   4. Mutual Information       — Gaussian smoothed
%   5. Secure Key Rate surface  — raw
%   6. Secure Key Rate surface  — Gaussian smoothed
%
% v.4 CSVs generated from:
%   configs/exp5_bb84_surface_v4.yaml (noise 0-0.30, eve 0-0.60, 31x41 grid)
%   configs/exp6_b92_surface_v4.yaml  (noise 0-0.15, eve 0-0.30, 31x41 grid)

clear; clc; close all;

% -------------------------------------------------------------------------
% Style constants
% -------------------------------------------------------------------------
FONT      = 'Times New Roman';
SZ_TITLE  = 20;
SZ_LABEL  = 18;
SZ_TICK   = 16;
SZ_LEGEND = 12;

THRESH_BB84 = 11;    % percent
THRESH_B92  = 6.5;   % percent

% Threshold plane colours (QBER plots only — carried over from v.3)
C_PLANE_BB84 = [1.00, 0.80, 0.00];   % golden yellow
C_PLANE_B92  = [0.65, 0.00, 0.90];   % bright violet

% QBER z-axis limits (percent)
ZLIM_BB84_QBER = [0, 2 * THRESH_BB84];   % [0, 22]
ZLIM_B92_QBER  = [0, 2 * THRESH_B92];    % [0, 13]

% MI and SKR z-axis limits (bits per qubit)
ZLIM_BB84_MI  = [0, 0.55];
ZLIM_B92_MI   = [0, 0.30];
ZLIM_BB84_SKR = [0, 0.55];
ZLIM_B92_SKR  = [0, 0.30];

% Mutual Information surface colours (flat, no gradient)
C_IAB = [0.10, 0.40, 0.70];   % blue  — Alice-Bob (secure channel)
C_IAE = [0.82, 0.15, 0.10];   % red   — Alice-Eve (eavesdropper)

% Axis and colorbar positions
AX_POS = [0.07, 0.08, 0.70, 0.82];
CB_POS = [0.84, 0.14, 0.022, 0.66];

BORDER_PX = 42;

% -------------------------------------------------------------------------
% Data paths (v.4 results)
% -------------------------------------------------------------------------
bb84_csv = 'C:\Users\dillo\OneDrive\Documents\NCL\Year 3\QKD\QKDSimulator\results\sim runs v.5 - complete experiments\exp5_bb84_surface_v4\bb84_surface_v4.csv';
b92_csv  = 'C:\Users\dillo\OneDrive\Documents\NCL\Year 3\QKD\QKDSimulator\results\sim runs v.5 - complete experiments\exp6_b92_surface_v4\b92_surface_v4.csv';

% =========================================================================
% BB84  (Experiment 5 v.4)
% Grid: 31 noise steps (0-0.30) x 41 eve steps (0-0.60)
% =========================================================================
noise_vals_bb84 = linspace(0, 0.30, 31);
eve_vals_bb84   = linspace(0, 0.60, 41);
[Eve_bb84, Noise_bb84] = meshgrid(eve_vals_bb84, noise_vals_bb84);   % 31x41

if ~isfile(bb84_csv)
    warning('BB84 v.4 CSV not found: %s\nRun exp5_bb84_surface_v4.yaml first.', bb84_csv);
else
    T_bb84 = readtable(bb84_csv);

    % Reshape each column into 31x41 (noise x eve) matrices
    Z_bb84_qber = reshape(T_bb84.qber_mean, 41, 31)' * 100;   % percent
    Z_bb84_iab  = reshape(T_bb84.iab_mean,  41, 31)';          % bits/qubit
    Z_bb84_iae  = reshape(T_bb84.iae_mean,  41, 31)';
    Z_bb84_skr  = reshape(T_bb84.skr_mean,  41, 31)';

    % Clamp QBER ceiling; SKR is already >= 0 by construction
    Z_bb84_qber = min(Z_bb84_qber, ZLIM_BB84_QBER(2));

    % Gaussian kernel (5x5) with edge replication — shared across all surfaces
    [kx, ky] = meshgrid(-2:2, -2:2);
    gkernel   = exp(-(kx.^2 + ky.^2) / 2);
    gkernel   = gkernel / sum(gkernel(:));

    % Smooth all four surfaces
    Z_bb84_qber_s = gauss_smooth(Z_bb84_qber, gkernel, ZLIM_BB84_QBER(2));
    Z_bb84_iab_s  = gauss_smooth(Z_bb84_iab,  gkernel, ZLIM_BB84_MI(2));
    Z_bb84_iae_s  = gauss_smooth(Z_bb84_iae,  gkernel, ZLIM_BB84_MI(2));
    Z_bb84_skr_s  = gauss_smooth(Z_bb84_skr,  gkernel, ZLIM_BB84_SKR(2));

    % Gradient colormaps
    key_colors_bb84 = [0.02, 0.04, 0.25;
                       0.15, 0.65, 1.00;
                       1.00, 0.40, 0.30;
                       0.70, 0.00, 0.00];
    cmap_bb84     = interp1(linspace(0,1,4), key_colors_bb84, linspace(0,1,256));
    cmap_bb84_skr = flipud(cmap_bb84);   % inverted: low SKR = red, high SKR = blue

    % ------------------------------------------------------------------
    % Plot 1: BB84 QBER — raw
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax  = axes(fig);
    s_data  = surf(ax, Eve_bb84, Noise_bb84, Z_bb84_qber, 'EdgeColor', 'none');
    colormap(ax, cmap_bb84);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_BB84_QBER); clim(ax, ZLIM_BB84_QBER);
    cb.Ticks = linspace(ZLIM_BB84_QBER(1), ZLIM_BB84_QBER(2), 5);
    hold(ax, 'on');
    s_plane = surf(ax, Eve_bb84, Noise_bb84, THRESH_BB84 * ones(size(Z_bb84_qber)), ...
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
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(bb84_csv), 'exp5_bb84_qber_v4.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    rotate3d(fig, 'on');
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 2: BB84 QBER — Gaussian smoothed
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white', 'Visible', 'off');
    ax  = axes(fig);
    s_data  = surf(ax, Eve_bb84, Noise_bb84, Z_bb84_qber_s, 'EdgeColor', 'none');
    colormap(ax, cmap_bb84);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_BB84_QBER); clim(ax, ZLIM_BB84_QBER);
    cb.Ticks = linspace(ZLIM_BB84_QBER(1), ZLIM_BB84_QBER(2), 5);
    hold(ax, 'on');
    s_plane = surf(ax, Eve_bb84, Noise_bb84, THRESH_BB84 * ones(size(Z_bb84_qber_s)), ...
        'FaceAlpha', 0.25, 'FaceColor', C_PLANE_BB84, 'EdgeColor', 'none');
    xlabel(ax, 'Eve Interception Rate', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',        'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'QBER (%)',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'BB84 Protocol - Depolarising Channel - QBER Surface', ...
               '(500 qubits, 20 trials per point, Gaussian smoothed)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_data, s_plane], ...
        {'QBER Surface', sprintf('Security Threshold (%.0f%%)', THRESH_BB84)}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northwest', ...
        'Box', 'on', 'BackgroundAlpha', 0.8);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(bb84_csv), 'exp5_bb84_qber_v4_gaussian.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    close(fig);
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 3: BB84 Mutual Information — raw
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax  = axes(fig);
    s_iab = surf(ax, Eve_bb84, Noise_bb84, Z_bb84_iab);
    s_iab.FaceColor = C_IAB; s_iab.FaceAlpha = 0.65; s_iab.EdgeAlpha = 0.15;
    hold(ax, 'on');
    s_iae = surf(ax, Eve_bb84, Noise_bb84, Z_bb84_iae);
    s_iae.FaceColor = C_IAE; s_iae.FaceAlpha = 0.65; s_iae.EdgeAlpha = 0.15;
    xlabel(ax, 'Eve Interception Rate',       'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'Mutual Information (bits/qubit)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'BB84 Protocol - Depolarising Channel - Mutual Information Surfaces', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_iab, s_iae], {'I(A;B)  Alice-Bob', 'I(A;E)  Alice-Eve'}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northeast', ...
        'Box', 'on', 'BackgroundAlpha', 0.8);
    zlim(ax, ZLIM_BB84_MI);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = [0.07, 0.08, 0.86, 0.82];   % wider — no colorbar
    out = fullfile(fileparts(bb84_csv), 'exp5_bb84_mutual_info_v4.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    rotate3d(fig, 'on');
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 4: BB84 Mutual Information — Gaussian smoothed
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white', 'Visible', 'off');
    ax  = axes(fig);
    s_iab = surf(ax, Eve_bb84, Noise_bb84, Z_bb84_iab_s);
    s_iab.FaceColor = C_IAB; s_iab.FaceAlpha = 0.65; s_iab.EdgeAlpha = 0.15;
    hold(ax, 'on');
    s_iae = surf(ax, Eve_bb84, Noise_bb84, Z_bb84_iae_s);
    s_iae.FaceColor = C_IAE; s_iae.FaceAlpha = 0.65; s_iae.EdgeAlpha = 0.15;
    xlabel(ax, 'Eve Interception Rate',       'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'Mutual Information (bits/qubit)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'BB84 Protocol - Depolarising Channel - Mutual Information Surfaces', ...
               '(500 qubits, 20 trials per point, Gaussian smoothed)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_iab, s_iae], {'I(A;B)  Alice-Bob', 'I(A;E)  Alice-Eve'}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northeast', ...
        'Box', 'on', 'BackgroundAlpha', 0.8);
    zlim(ax, ZLIM_BB84_MI);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = [0.07, 0.08, 0.86, 0.82];
    out = fullfile(fileparts(bb84_csv), 'exp5_bb84_mutual_info_v4_gaussian.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    close(fig);
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 5: BB84 Secure Key Rate — raw
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax  = axes(fig);
    surf(ax, Eve_bb84, Noise_bb84, Z_bb84_skr, 'EdgeColor', 'none');
    colormap(ax, cmap_bb84_skr);
    cb = colorbar(ax);
    cb.Label.String = 'Secure Key Rate (bits/qubit)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_BB84_SKR); clim(ax, ZLIM_BB84_SKR);
    cb.Ticks = linspace(ZLIM_BB84_SKR(1), ZLIM_BB84_SKR(2), 5);
    xlabel(ax, 'Eve Interception Rate',          'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',                 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'Secure Key Rate (bits/qubit)',    'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'BB84 Protocol - Depolarising Channel - Secure Key Rate Surface', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(bb84_csv), 'exp5_bb84_skr_v4.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    rotate3d(fig, 'on');
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 6: BB84 Secure Key Rate — Gaussian smoothed
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white', 'Visible', 'off');
    ax  = axes(fig);
    surf(ax, Eve_bb84, Noise_bb84, Z_bb84_skr_s, 'EdgeColor', 'none');
    colormap(ax, cmap_bb84_skr);
    cb = colorbar(ax);
    cb.Label.String = 'Secure Key Rate (bits/qubit)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_BB84_SKR); clim(ax, ZLIM_BB84_SKR);
    cb.Ticks = linspace(ZLIM_BB84_SKR(1), ZLIM_BB84_SKR(2), 5);
    xlabel(ax, 'Eve Interception Rate',          'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',                 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'Secure Key Rate (bits/qubit)',    'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'BB84 Protocol - Depolarising Channel - Secure Key Rate Surface', ...
               '(500 qubits, 20 trials per point, Gaussian smoothed)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(bb84_csv), 'exp5_bb84_skr_v4_gaussian.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    close(fig);
    fprintf('Saved: %s\n', out);
end

% =========================================================================
% B92  (Experiment 6 v.4)
% Grid: 31 noise steps (0-0.15) x 41 eve steps (0-0.30)
% =========================================================================
noise_vals_b92 = linspace(0, 0.15, 31);
eve_vals_b92   = linspace(0, 0.30, 41);
[Eve_b92, Noise_b92] = meshgrid(eve_vals_b92, noise_vals_b92);   % 31x41

if ~isfile(b92_csv)
    warning('B92 v.4 CSV not found: %s\nRun exp6_b92_surface_v4.yaml first.', b92_csv);
else
    T_b92 = readtable(b92_csv);

    Z_b92_qber = reshape(T_b92.qber_mean, 41, 31)' * 100;
    Z_b92_iab  = reshape(T_b92.iab_mean,  41, 31)';
    Z_b92_iae  = reshape(T_b92.iae_mean,  41, 31)';
    Z_b92_skr  = reshape(T_b92.skr_mean,  41, 31)';

    Z_b92_qber = min(Z_b92_qber, ZLIM_B92_QBER(2));

    [kx, ky] = meshgrid(-2:2, -2:2);
    gkernel   = exp(-(kx.^2 + ky.^2) / 2);
    gkernel   = gkernel / sum(gkernel(:));

    Z_b92_qber_s = gauss_smooth(Z_b92_qber, gkernel, ZLIM_B92_QBER(2));
    Z_b92_iab_s  = gauss_smooth(Z_b92_iab,  gkernel, ZLIM_B92_MI(2));
    Z_b92_iae_s  = gauss_smooth(Z_b92_iae,  gkernel, ZLIM_B92_MI(2));
    Z_b92_skr_s  = gauss_smooth(Z_b92_skr,  gkernel, ZLIM_B92_SKR(2));

    key_colors_b92 = [0.00, 0.30, 0.35;
                      0.25, 0.88, 0.72;
                      1.00, 0.40, 0.30;
                      0.70, 0.00, 0.00];
    cmap_b92     = interp1(linspace(0,1,4), key_colors_b92, linspace(0,1,256));
    cmap_b92_skr = flipud(cmap_b92);

    % ------------------------------------------------------------------
    % Plot 1: B92 QBER — raw
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax  = axes(fig);
    s_data  = surf(ax, Eve_b92, Noise_b92, Z_b92_qber, 'EdgeColor', 'none');
    colormap(ax, cmap_b92);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_B92_QBER); clim(ax, ZLIM_B92_QBER);
    cb.Ticks = linspace(ZLIM_B92_QBER(1), ZLIM_B92_QBER(2), 5);
    hold(ax, 'on');
    s_plane = surf(ax, Eve_b92, Noise_b92, THRESH_B92 * ones(size(Z_b92_qber)), ...
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
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(b92_csv), 'exp6_b92_qber_v4.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    rotate3d(fig, 'on');
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 2: B92 QBER — Gaussian smoothed
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white', 'Visible', 'off');
    ax  = axes(fig);
    s_data  = surf(ax, Eve_b92, Noise_b92, Z_b92_qber_s, 'EdgeColor', 'none');
    colormap(ax, cmap_b92);
    cb = colorbar(ax);
    cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_B92_QBER); clim(ax, ZLIM_B92_QBER);
    cb.Ticks = linspace(ZLIM_B92_QBER(1), ZLIM_B92_QBER(2), 5);
    hold(ax, 'on');
    s_plane = surf(ax, Eve_b92, Noise_b92, THRESH_B92 * ones(size(Z_b92_qber_s)), ...
        'FaceAlpha', 0.25, 'FaceColor', C_PLANE_B92, 'EdgeColor', 'none');
    xlabel(ax, 'Eve Interception Rate', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',        'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'QBER (%)',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'B92 Protocol - Depolarising Channel - QBER Surface', ...
               '(500 qubits, 20 trials per point, Gaussian smoothed)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_data, s_plane], ...
        {'QBER Surface', sprintf('Security Threshold (%.1f%%)', THRESH_B92)}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northwest', ...
        'Box', 'on', 'BackgroundAlpha', 0.8);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(b92_csv), 'exp6_b92_qber_v4_gaussian.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    close(fig);
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 3: B92 Mutual Information — raw
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax  = axes(fig);
    s_iab = surf(ax, Eve_b92, Noise_b92, Z_b92_iab);
    s_iab.FaceColor = C_IAB; s_iab.FaceAlpha = 0.65; s_iab.EdgeAlpha = 0.15;
    hold(ax, 'on');
    s_iae = surf(ax, Eve_b92, Noise_b92, Z_b92_iae);
    s_iae.FaceColor = C_IAE; s_iae.FaceAlpha = 0.65; s_iae.EdgeAlpha = 0.15;
    xlabel(ax, 'Eve Interception Rate',       'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'Mutual Information (bits/qubit)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'B92 Protocol - Depolarising Channel - Mutual Information Surfaces', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_iab, s_iae], {'I(A;B)  Alice-Bob', 'I(A;E)  Alice-Eve'}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northeast', ...
        'Box', 'on', 'BackgroundAlpha', 0.8);
    zlim(ax, ZLIM_B92_MI);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = [0.07, 0.08, 0.86, 0.82];
    out = fullfile(fileparts(b92_csv), 'exp6_b92_mutual_info_v4.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    rotate3d(fig, 'on');
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 4: B92 Mutual Information — Gaussian smoothed
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white', 'Visible', 'off');
    ax  = axes(fig);
    s_iab = surf(ax, Eve_b92, Noise_b92, Z_b92_iab_s);
    s_iab.FaceColor = C_IAB; s_iab.FaceAlpha = 0.65; s_iab.EdgeAlpha = 0.15;
    hold(ax, 'on');
    s_iae = surf(ax, Eve_b92, Noise_b92, Z_b92_iae_s);
    s_iae.FaceColor = C_IAE; s_iae.FaceAlpha = 0.65; s_iae.EdgeAlpha = 0.15;
    xlabel(ax, 'Eve Interception Rate',       'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',              'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'Mutual Information (bits/qubit)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'B92 Protocol - Depolarising Channel - Mutual Information Surfaces', ...
               '(500 qubits, 20 trials per point, Gaussian smoothed)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    legend(ax, [s_iab, s_iae], {'I(A;B)  Alice-Bob', 'I(A;E)  Alice-Eve'}, ...
        'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northeast', ...
        'Box', 'on', 'BackgroundAlpha', 0.8);
    zlim(ax, ZLIM_B92_MI);
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = [0.07, 0.08, 0.86, 0.82];
    out = fullfile(fileparts(b92_csv), 'exp6_b92_mutual_info_v4_gaussian.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    close(fig);
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 5: B92 Secure Key Rate — raw
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white');
    ax  = axes(fig);
    surf(ax, Eve_b92, Noise_b92, Z_b92_skr, 'EdgeColor', 'none');
    colormap(ax, cmap_b92_skr);
    cb = colorbar(ax);
    cb.Label.String = 'Secure Key Rate (bits/qubit)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_B92_SKR); clim(ax, ZLIM_B92_SKR);
    cb.Ticks = linspace(ZLIM_B92_SKR(1), ZLIM_B92_SKR(2), 5);
    xlabel(ax, 'Eve Interception Rate',          'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',                 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'Secure Key Rate (bits/qubit)',    'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'B92 Protocol - Depolarising Channel - Secure Key Rate Surface', ...
               '(500 qubits, 20 trials per point)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(b92_csv), 'exp6_b92_skr_v4.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    rotate3d(fig, 'on');
    fprintf('Saved: %s\n', out);

    % ------------------------------------------------------------------
    % Plot 6: B92 Secure Key Rate — Gaussian smoothed
    % ------------------------------------------------------------------
    fig = figure('Position', [100 100 1200 750], 'Color', 'white', 'Visible', 'off');
    ax  = axes(fig);
    surf(ax, Eve_b92, Noise_b92, Z_b92_skr_s, 'EdgeColor', 'none');
    colormap(ax, cmap_b92_skr);
    cb = colorbar(ax);
    cb.Label.String = 'Secure Key Rate (bits/qubit)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
    zlim(ax, ZLIM_B92_SKR); clim(ax, ZLIM_B92_SKR);
    cb.Ticks = linspace(ZLIM_B92_SKR(1), ZLIM_B92_SKR(2), 5);
    xlabel(ax, 'Eve Interception Rate',          'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    ylabel(ax, 'Noise Strength',                 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    zlabel(ax, 'Secure Key Rate (bits/qubit)',    'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
    title(ax, {'B92 Protocol - Depolarising Channel - Secure Key Rate Surface', ...
               '(500 qubits, 20 trials per point, Gaussian smoothed)'}, ...
        'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
    set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
    grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, [30 30]); drawnow;
    ax.Position = AX_POS; cb.Position = CB_POS;
    out = fullfile(fileparts(b92_csv), 'exp6_b92_skr_v4_gaussian.png');
    exportgraphics(fig, out, 'Resolution', 300);
    add_white_border(out, BORDER_PX);
    close(fig);
    fprintf('Saved: %s\n', out);
end

% -------------------------------------------------------------------------
% Helper: Gaussian smooth with edge replication and ceiling clamp
% -------------------------------------------------------------------------
function Z_out = gauss_smooth(Z, gkernel, ceiling)
    Z_pad = [repmat(Z(:,1), 1, 2), Z, repmat(Z(:,end), 1, 2)];
    Z_pad = [repmat(Z_pad(1,:), 2, 1); Z_pad; repmat(Z_pad(end,:), 2, 1)];
    Z_out = min(conv2(Z_pad, gkernel, 'valid'), ceiling);
end

% -------------------------------------------------------------------------
% Helper: pad PNG with a white border
% -------------------------------------------------------------------------
function add_white_border(path, border_px)
    img  = imread(path);
    [h, w, c] = size(img);
    img2 = uint8(255 * ones(h + 2*border_px, w + 2*border_px, c));
    img2(border_px+1:border_px+h, border_px+1:border_px+w, :) = img;
    imwrite(img2, path);
end
