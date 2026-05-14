% exp 5 & 6 (v.5): BB84 and B92 surface plots - three plot types each
% plots:
% 1. QBER surface 
% 2. Mutual Information (two surfaces: I(A;B) and I(A;E))
% 3. Secure Key Rate surface
%
% CSVs:
% configs/exp5_bb84_surface_v5.yaml (noise 0-0.30, eve 0-0.60, 51x57 grid, 40 trials/point)
% configs/exp6_b92_surface_v5.yaml (noise 0-0.15, eve 0-0.30, 51x57 grid, 40 trials/point)

clear; clc; close all;

% -------------------------------------------------------------------------
% style defs
% -------------------------------------------------------------------------
FONT      = 'Times New Roman';
SZ_TITLE  = 20;
SZ_LABEL  = 18;
SZ_TICK   = 16;
SZ_LEGEND = 12;

% percentage scale
THRESH_BB84 = 11; 
THRESH_B92  = 6.5;

% threshold plane colours
C_PLANE_BB84 = [1.00, 0.80, 0.00]; % yellow
C_PLANE_B92  = [0.65, 0.00, 0.90]; % purple

% z-axis limits
ZLIM_BB84_QBER = [0, 2 * THRESH_BB84]; % [0, 22]
ZLIM_B92_QBER  = [0, 2 * THRESH_B92]; % [0, 13]

% bits per 100 qubits for MI & SKR
ZLIM_BB84_MI  = [0, 55];
ZLIM_B92_MI   = [0, 30];
ZLIM_BB84_SKR = [0, 50];
ZLIM_B92_SKR  = [0, 25];

% viewpoint angles
VIEW_BB84_QBER = [30, 30];
VIEW_BB84_MI   = [30, 30];
VIEW_BB84_SKR  = [80, 20];
VIEW_B92_QBER  = [30, 30];
VIEW_B92_MI    = [30, 30];
VIEW_B92_SKR   = [80, 20];

% MI surface colours
C_IAB_BB84 = [0.10, 0.40, 0.70]; % blue - I(A;B) BB84
C_IAB_B92  = [0.15, 0.72, 0.65]; % teal - I(A;B) B92
C_IAE      = [0.82, 0.15, 0.10]; % red - I(A;E) for both protocols

% axis and colorbar positions
AX_POS = [0.12, 0.10, 0.65, 0.78];
CB_POS = [0.84, 0.14, 0.022, 0.66];

BORDER_PX = 10;

% -------------------------------------------------------------------------
% CSV file paths
% -------------------------------------------------------------------------
bb84_csv = 'C:\Users\dillo\OneDrive\Documents\NCL\Year 3\QKD\QKDSimulator\results\sim runs v.6 - FINAL\exp5_bb84_surface_v5\bb84_surface_v5.csv';
b92_csv  = 'C:\Users\dillo\OneDrive\Documents\NCL\Year 3\QKD\QKDSimulator\results\sim runs v.6 - FINAL\exp6_b92_surface_v5\b92_surface_v5.csv';

% =========================================================================
% BB84  exp 5
% grid: 51 noise steps (0%-30%) x 57 eve steps (0%-60%)
% =========================================================================
noise_vals_bb84 = linspace(0, 30, 51);
eve_vals_bb84   = linspace(0, 60, 57);
[Eve_bb84, Noise_bb84] = meshgrid(eve_vals_bb84, noise_vals_bb84); % 51x57 grid


T_bb84 = readtable(bb84_csv);

% reshape each column into 51x57 (noise x eve) matrices
Z_bb84_qber = reshape(T_bb84.qber_mean, 57, 51)' * 100; % percent
Z_bb84_iab  = reshape(T_bb84.iab_mean,  57, 51)' * 100; % bits/100 qubits
Z_bb84_iae  = reshape(T_bb84.iae_mean,  57, 51)' * 100; % bits/100 qubits
Z_bb84_skr  = reshape(T_bb84.skr_mean,  57, 51)' * 100; % bits/100 qubits

% clamp zlim 
Z_bb84_qber = min(Z_bb84_qber, ZLIM_BB84_QBER(2));

% gradient colormaps
key_colors_bb84 = [
                0.02, 0.04, 0.25;
                0.15, 0.65, 1.00;
                1.00, 0.40, 0.30;
                0.70, 0.00, 0.00
                ];
cmap_bb84     = interp1(linspace(0,1,4), key_colors_bb84, linspace(0,1,256));
cmap_bb84_skr = flipud(cmap_bb84); % inverted so low SKR = red, high SKR = blue

% ------------------------------------------------------------------
% plot 1: BB84 QBER
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
s_plane = surf(ax, Eve_bb84, Noise_bb84, THRESH_BB84 * ones(size(Z_bb84_qber)),'FaceAlpha', 0.25, 'FaceColor', C_PLANE_BB84, 'EdgeColor', 'none');


xlabel(ax, {'Eve Interception', 'Rate (%)'}, 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
ylabel(ax, 'Noise Strength (%)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
zlabel(ax, 'QBER (%)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
title(ax, {'BB84 Protocol - Depolarising Channel - QBER Surface', '(500 qubits, 40 trials per point)'},'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');


legend(ax, [s_data, s_plane], {'QBER Surface', sprintf('Security Threshold (%.0f%%)', THRESH_BB84)}, 'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northwest', 'Box', 'on', 'BackgroundAlpha', 0.8);

set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, VIEW_BB84_QBER);
ax.Position = AX_POS; cb.Position = CB_POS;
drawnow;
out = fullfile(fileparts(bb84_csv), 'exp5_bb84_qber_v5.png');
exportgraphics(fig, out, 'Resolution', 300, 'Padding', 'tight');
add_white_border(out, BORDER_PX);
rotate3d(fig, 'on');
fprintf('saved: %s\n', out);

% ------------------------------------------------------------------
% plot 2: BB84 MI
% ------------------------------------------------------------------
fig = figure('Position', [100 100 1200 750], 'Color', 'white');
ax  = axes(fig);
s_iab = surf(ax, Eve_bb84, Noise_bb84, Z_bb84_iab);
s_iab.FaceColor = C_IAB_BB84; s_iab.FaceAlpha = 0.65; s_iab.EdgeAlpha = 0.15;
hold(ax, 'on');
s_iae = surf(ax, Eve_bb84, Noise_bb84, Z_bb84_iae);
s_iae.FaceColor = C_IAE; s_iae.FaceAlpha = 0.65; s_iae.EdgeAlpha = 0.15;

xlabel(ax, {'Eve Interception', 'Rate (%)'}, 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
ylabel(ax, 'Noise Strength (%)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
zlabel(ax, 'Mutual Information (bits/100 qubits)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
title(ax, {'BB84 Protocol - Depolarising Channel - Mutual Information Surfaces', '(500 qubits, 40 trials per point)'}, 'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');

legend(ax, [s_iab, s_iae], {'I(A;B)  Alice-Bob', 'I(A;E)  Alice-Eve'}, 'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northeast', 'Box', 'on', 'BackgroundAlpha', 0.8);
zlim(ax, ZLIM_BB84_MI);
set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, VIEW_BB84_MI);
ax.Position = [0.12, 0.10, 0.82, 0.78];   % wider, no colorbar
drawnow;
out = fullfile(fileparts(bb84_csv), 'exp5_bb84_mutual_info_v5.png');
exportgraphics(fig, out, 'Resolution', 300, 'Padding', 'tight');
add_white_border(out, BORDER_PX);
rotate3d(fig, 'on');
fprintf('saved: %s\n', out);

% ------------------------------------------------------------------
% plot 3: BB84 SKR
% ------------------------------------------------------------------
fig = figure('Position', [100 100 1200 750], 'Color', 'white');
ax  = axes(fig);
surf(ax, Eve_bb84, Noise_bb84, Z_bb84_skr, 'EdgeColor', 'none');
colormap(ax, cmap_bb84_skr);
cb = colorbar(ax);

cb.Label.String = 'Secure Key Rate (bits/100 qubits)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
zlim(ax, ZLIM_BB84_SKR); clim(ax, ZLIM_BB84_SKR);

cb.Ticks = linspace(ZLIM_BB84_SKR(1), ZLIM_BB84_SKR(2), 5);
xlabel(ax, {'Eve Interception', 'Rate (%)'},'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
ylabel(ax, 'Noise Strength (%)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
zlabel(ax, 'Secure Key Rate (bits/100 qubits)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
title(ax, {'BB84 Protocol - Depolarising Channel - Secure Key Rate Surface', '(500 qubits, 40 trials per point)'}, 'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);

grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, VIEW_BB84_SKR);
ax.Position = AX_POS; cb.Position = CB_POS;
drawnow;
out = fullfile(fileparts(bb84_csv), 'exp5_bb84_skr_v5.png');
exportgraphics(fig, out, 'Resolution', 300, 'Padding', 'tight');
add_white_border(out, BORDER_PX);
rotate3d(fig, 'on');
fprintf('saved: %s\n', out);


% =========================================================================
% B92  exp 6
% grid: 51 noise steps (0%-15%) x 57 eve steps (0%-30%)
% =========================================================================
noise_vals_b92 = linspace(0, 15, 51);
eve_vals_b92   = linspace(0, 30, 57);
[Eve_b92, Noise_b92] = meshgrid(eve_vals_b92, noise_vals_b92); % 51x57 grid


T_b92 = readtable(b92_csv);

Z_b92_qber = reshape(T_b92.qber_mean, 57, 51)' * 100;
Z_b92_iab = reshape(T_b92.iab_mean,  57, 51)' * 100;
Z_b92_iae = reshape(T_b92.iae_mean,  57, 51)' * 100;
Z_b92_skr = reshape(T_b92.skr_mean,  57, 51)' * 100;

Z_b92_qber = min(Z_b92_qber, ZLIM_B92_QBER(2));

key_colors_b92 = [
                0.00, 0.30, 0.35;
                0.25, 0.88, 0.72;
                1.00, 0.40, 0.30;
                0.70, 0.00, 0.00];

cmap_b92 = interp1(linspace(0,1,4), key_colors_b92, linspace(0,1,256));
cmap_b92_skr = flipud(cmap_b92);

% ------------------------------------------------------------------
% plot 1: B92 QBER
% ------------------------------------------------------------------
fig = figure('Position', [100 100 1200 750], 'Color', 'white');
ax = axes(fig);
s_data = surf(ax, Eve_b92, Noise_b92, Z_b92_qber, 'EdgeColor', 'none');
colormap(ax, cmap_b92);
cb = colorbar(ax);

cb.Label.String = 'QBER (%)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
zlim(ax, ZLIM_B92_QBER); clim(ax, ZLIM_B92_QBER);
cb.Ticks = linspace(ZLIM_B92_QBER(1), ZLIM_B92_QBER(2), 5);
hold(ax, 'on');

s_plane = surf(ax, Eve_b92, Noise_b92, THRESH_B92 * ones(size(Z_b92_qber)),'FaceAlpha', 0.25, 'FaceColor', C_PLANE_B92, 'EdgeColor', 'none');
xlabel(ax, {'Eve Interception', 'Rate (%)'}, 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
ylabel(ax, 'Noise Strength (%)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
zlabel(ax, 'QBER (%)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
title(ax, {'B92 Protocol - Depolarising Channel - QBER Surface', '(500 qubits, 40 trials per point)'}, 'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
legend(ax, [s_data, s_plane], {'QBER Surface', sprintf('Security Threshold (%.1f%%)', THRESH_B92)}, 'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northwest', 'Box', 'on', 'BackgroundAlpha', 0.8);

set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, VIEW_B92_QBER);
ax.Position = AX_POS; cb.Position = CB_POS;
drawnow;
out = fullfile(fileparts(b92_csv), 'exp6_b92_qber_v5.png');
exportgraphics(fig, out, 'Resolution', 300, 'Padding', 'tight');
add_white_border(out, BORDER_PX);
rotate3d(fig, 'on');
fprintf('saved: %s\n', out);

% ------------------------------------------------------------------
% plot 2: B92 MI
% ------------------------------------------------------------------
fig = figure('Position', [100 100 1200 750], 'Color', 'white');
ax  = axes(fig);
s_iab = surf(ax, Eve_b92, Noise_b92, Z_b92_iab);
s_iab.FaceColor = C_IAB_B92; s_iab.FaceAlpha = 0.65; s_iab.EdgeAlpha = 0.15;
hold(ax, 'on');

s_iae = surf(ax, Eve_b92, Noise_b92, Z_b92_iae);
s_iae.FaceColor = C_IAE; s_iae.FaceAlpha = 0.65; s_iae.EdgeAlpha = 0.15;
xlabel(ax, {'Eve Interception', 'Rate (%)'}, 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
ylabel(ax, 'Noise Strength (%)','FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
zlabel(ax, 'Mutual Information (bits/100 qubits)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
title(ax, {'B92 Protocol - Depolarising Channel - Mutual Information Surfaces','(500 qubits, 40 trials per point)'}, 'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
legend(ax, [s_iab, s_iae], {'I(A;B)  Alice-Bob', 'I(A;E)  Alice-Eve'}, 'FontName', FONT, 'FontSize', SZ_LEGEND, 'Location', 'northeast', 'Box', 'on', 'BackgroundAlpha', 0.8);
zlim(ax, ZLIM_B92_MI);

set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, VIEW_B92_MI);
ax.Position = [0.12, 0.10, 0.82, 0.78]; % wider, no colorbar
drawnow;
out = fullfile(fileparts(b92_csv), 'exp6_b92_mutual_info_v5.png');
exportgraphics(fig, out, 'Resolution', 300, 'Padding', 'tight');
add_white_border(out, BORDER_PX);
rotate3d(fig, 'on');
fprintf('saved: %s\n', out);

% ------------------------------------------------------------------
% plot 3: B92 SKR
% ------------------------------------------------------------------
fig = figure('Position', [100 100 1200 750], 'Color', 'white');
ax  = axes(fig);
surf(ax, Eve_b92, Noise_b92, Z_b92_skr, 'EdgeColor', 'none');
colormap(ax, cmap_b92_skr);
cb = colorbar(ax);

cb.Label.String = 'Secure Key Rate (bits/100 qubits)'; cb.Label.FontName = FONT; cb.Label.FontSize = SZ_LABEL;
zlim(ax, ZLIM_B92_SKR); clim(ax, ZLIM_B92_SKR);
cb.Ticks = linspace(ZLIM_B92_SKR(1), ZLIM_B92_SKR(2), 5);
xlabel(ax, {'Eve Interception', 'Rate (%)'},'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
ylabel(ax, 'Noise Strength (%)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
zlabel(ax, 'Secure Key Rate (bits/100 qubits)', 'FontName', FONT, 'FontSize', SZ_LABEL, 'FontWeight', 'bold');
title(ax, {'B92 Protocol - Depolarising Channel - Secure Key Rate Surface', '(500 qubits, 40 trials per point)'}, 'FontName', FONT, 'FontSize', SZ_TITLE, 'FontWeight', 'bold');
set(ax, 'FontName', FONT, 'FontSize', SZ_TICK);
grid(ax, 'on'); ax.GridAlpha = 0.3; view(ax, VIEW_B92_SKR);
ax.Position = AX_POS; cb.Position = CB_POS;
drawnow;

out = fullfile(fileparts(b92_csv), 'exp6_b92_skr_v5.png');
exportgraphics(fig, out, 'Resolution', 300, 'Padding', 'tight');
add_white_border(out, BORDER_PX);
rotate3d(fig, 'on');
fprintf('saved: %s\n', out);

% -------------------------------------------------------------------------
% PNG padding to prevent axis label cropping
% -------------------------------------------------------------------------
function add_white_border(path, border_px)
    img  = imread(path);
    [h, w, c] = size(img);
    img2 = uint8(255 * ones(h + 2*border_px, w + 2*border_px, c));
    img2(border_px+1:border_px+h, border_px+1:border_px+w, :) = img;
    imwrite(img2, path);
end
