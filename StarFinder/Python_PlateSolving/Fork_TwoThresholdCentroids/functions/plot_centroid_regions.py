"""
Diagnostic plots for the two-threshold centroid step: pixel-exact outlines of the low-threshold (centroid)
and high-threshold (detection) regions, with the centroids computed from each region.

Main function: plot_centroid_regions(...)
Inputs:
    img_intensity        : 2D float64, background-subtracted intensity [counts]
    noise_map            : 2D float64, background noise sigma per pixel [counts]
    img_labels_high      : 2D int32, labels of the detection mask (e.g. > 12 sigma)
    img_labels_low       : 2D int32, labels of the centroid mask (e.g. > 3 sigma)
    x_low, y_low         : 1D float64, centroids from star_stats_two_threshold [px]
    is_blended           : 1D bool, True where star_stats_two_threshold fell back to the high-threshold region
    x_high, y_high       : 1D float64, centroids from star_stats on the high-threshold regions only [px]
                           (same star order as x_low / y_low: both iterate over high labels with > 3 pixels)
    kappa_low, kappa_high: float, the two thresholds in units of sigma [-] (only used for labels)
    n_cutouts            : int, number of zoomed star cutouts in the second figure
Returns: (fig_overview, fig_cutouts)
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

# Colors stepped for a dark (night sky) background; checked for color-vision-deficiency separation (OKLab dE >= 26)
COLOR_LOW  = '#3987e5'   # blue   : centroid region (low threshold) and its centroid
COLOR_HIGH = '#d95926'   # orange : detection region (high threshold) and its centroid
COLOR_FLAG = '#ffffff'   # white  : ring around blended stars


def mask_outline_segments(mask, offset_x=0, offset_y=0):
    """Pixel-edge outline of a 2D bool mask as line segments [[(x0, y0), (x1, y1)], ...] in pixel coordinates."""
    padded = np.pad(mask, 1, constant_values=False)
    # Horizontal edges: index r compares image rows r-1 and r -> edge at y = r - 0.5
    rows, cols = np.nonzero(padded[1:, 1:-1] != padded[:-1, 1:-1])
    y = rows - 0.5 + offset_y
    x = cols + offset_x
    horizontal = np.stack([np.stack([x - 0.5, y], 1), np.stack([x + 0.5, y], 1)], 1)
    # Vertical edges: index c compares image columns c-1 and c -> edge at x = c - 0.5
    rows, cols = np.nonzero(padded[1:-1, 1:] != padded[1:-1, :-1])
    x = cols - 0.5 + offset_x
    y = rows + offset_y
    vertical = np.stack([np.stack([x, y - 0.5], 1), np.stack([x, y + 0.5], 1)], 1)
    return np.concatenate([horizontal, vertical]).astype(float)


def _draw_regions_and_centroids(ax, mask_low_used, mask_high, offset_x, offset_y,
                                x_low, y_low, x_high, y_high, is_blended, line_scale, marker_size):
    ax.add_collection(LineCollection(mask_outline_segments(mask_low_used, offset_x, offset_y),
                                     colors=COLOR_LOW, linewidths=1.2 * line_scale))
    ax.add_collection(LineCollection(mask_outline_segments(mask_high, offset_x, offset_y),
                                     colors=COLOR_HIGH, linewidths=1.6 * line_scale))
    ax.plot(x_high, y_high, 'x', color=COLOR_HIGH, ms=marker_size, mew=2, ls='none')
    ax.plot(x_low, y_low, '+', color=COLOR_LOW, ms=1.3 * marker_size, mew=2, ls='none')
    ax.plot(x_low[is_blended], y_low[is_blended], 'o', mfc='none', mec=COLOR_FLAG,
            ms=3 * marker_size, mew=1.2, ls='none')


def _legend_handles(kappa_low, kappa_high):
    return [
        Line2D([], [], color=COLOR_LOW,  lw=1.5, label=f'{kappa_low:g}σ region (centroid)'),
        Line2D([], [], color=COLOR_HIGH, lw=1.5, label=f'{kappa_high:g}σ region (detection, incl. rejected ≤3 px objects)'),
        Line2D([], [], color=COLOR_LOW,  marker='+', ms=10, mew=2, ls='none', label=f'centroid from {kappa_low:g}σ region'),
        Line2D([], [], color=COLOR_HIGH, marker='x', ms=8,  mew=2, ls='none', label=f'centroid from {kappa_high:g}σ region'),
        Line2D([], [], color='0.4', marker='o', mfc='none', ms=12, mew=1.2, ls='none',
               label=f'blended: uses {kappa_high:g}σ region'),
    ]


def plot_centroid_regions(img_intensity, noise_map, img_labels_high, img_labels_low,
                          x_low, y_low, is_blended, x_high, y_high,
                          kappa_low=3.0, kappa_high=12.0, n_cutouts=12):

    signal_to_noise = img_intensity / noise_map                                  # [-] display in units of sigma
    display_norm    = mcolors.AsinhNorm(linear_width=3.0, vmin=-3.0,
                                        vmax=np.percentile(signal_to_noise, 99.99))  # linear around the noise, compressed for bright stars

    # Only the low-threshold regions that contain a detection are used; the many pure-noise 3 sigma pixels are hidden
    used_low_labels = np.unique(img_labels_low[img_labels_high > 0])
    mask_low_used   = np.isin(img_labels_low, used_low_labels[used_low_labels > 0])
    mask_high       = img_labels_high > 0

    shift = np.hypot(x_low - x_high, y_low - y_high)                             # [px] centroid change between the two regions

    # ============================================
    # FIGURE 1: FULL FRAME (zoom in with the toolbar)
    # ============================================
    fig_overview, ax = plt.subplots(figsize=(16, 10))
    image = ax.imshow(signal_to_noise, cmap='gray', norm=display_norm, interpolation='nearest')
    _draw_regions_and_centroids(ax, mask_low_used, mask_high, 0, 0,
                                x_low, y_low, x_high, y_high, is_blended, line_scale=0.6, marker_size=4)
    fig_overview.colorbar(image, ax=ax, label='signal / noise [σ]  (asinh stretch)', shrink=0.8)
    ax.set_title(f'{len(x_low)} stars: {kappa_low:g}σ centroid regions vs {kappa_high:g}σ detection regions'
                 f'  |  centroid shift median {np.median(shift[~is_blended]):.3f} px, max {shift[~is_blended].max():.3f} px'
                 f'  |  {is_blended.sum()} blended')
    ax.legend(handles=_legend_handles(kappa_low, kappa_high), loc='upper right', framealpha=0.9)
    fig_overview.tight_layout()

    # ============================================
    # FIGURE 2: ZOOMED CUTOUTS
    # Selection: all blended stars, then largest centroid shift, then faintest and brightest (by peak S/N)
    # ============================================
    n_stars    = len(x_low)
    peak_snr   = signal_to_noise[np.clip(np.round(y_high).astype(int), 0, signal_to_noise.shape[0] - 1),
                                 np.clip(np.round(x_high).astype(int), 0, signal_to_noise.shape[1] - 1)]
    candidates = list(np.flatnonzero(is_blended))
    n_rest     = max(n_cutouts - len(candidates), 0)
    candidates += list(np.argsort(-shift * ~is_blended)[: (n_rest + 1) // 2])
    candidates += list(np.argsort(peak_snr)[: n_rest // 4 + 1])
    candidates += list(np.argsort(-peak_snr)[: n_rest // 4 + 1])
    selection  = list(dict.fromkeys(int(k) for k in candidates))[:min(n_cutouts, n_stars)]   # unique, keep order

    n_cols = 4
    n_rows = int(np.ceil(len(selection) / n_cols))
    fig_cutouts, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 4 * n_rows + 0.8), squeeze=False)
    len_y, len_x = signal_to_noise.shape

    for ax, k in zip(axes.flat, selection):
        # Cutout around the star's low-threshold region, at least 21 x 21 px
        label_low = img_labels_low[int(round(y_high[k])), int(round(x_high[k]))]
        if label_low > 0:
            rows, cols = np.nonzero(img_labels_low == label_low)
            half = max(10, int(0.6 * max(np.ptp(rows), np.ptp(cols))) + 4)
        else:
            half = 10
        center_x, center_y = int(round(x_high[k])), int(round(y_high[k]))
        x0, x1 = max(center_x - half, 0), min(center_x + half + 1, len_x)
        y0, y1 = max(center_y - half, 0), min(center_y + half + 1, len_y)

        ax.imshow(signal_to_noise[y0:y1, x0:x1], cmap='gray', norm=display_norm, interpolation='nearest',
                  extent=(x0 - 0.5, x1 - 0.5, y1 - 0.5, y0 - 0.5))
        _draw_regions_and_centroids(ax, mask_low_used[y0:y1, x0:x1], mask_high[y0:y1, x0:x1], x0, y0,
                                    x_low, y_low, x_high, y_high, is_blended, line_scale=1.0, marker_size=9)
        ax.set_xlim(x0 - 0.5, x1 - 0.5)
        ax.set_ylim(y1 - 0.5, y0 - 0.5)
        tag = 'BLENDED' if is_blended[k] else f'shift {shift[k]:.3f} px'
        ax.set_title(f'star {k}  ({x_low[k]:.1f}, {y_low[k]:.1f})\npeak {peak_snr[k]:.0f}σ  |  {tag}', fontsize=9)
        ax.tick_params(labelsize=7)

    for ax in axes.flat[len(selection):]:
        ax.set_visible(False)

    fig_cutouts.legend(handles=_legend_handles(kappa_low, kappa_high), loc='lower center', ncol=5, frameon=False)
    fig_cutouts.suptitle('Selected stars: blended, largest centroid shift, faintest, brightest')
    fig_cutouts.tight_layout(rect=(0, 0.05, 1, 1))

    return fig_overview, fig_cutouts
