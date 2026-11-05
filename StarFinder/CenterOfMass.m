clear
close all


img_labels = [1     1     0     0     2     2     0     0; ...
    1     0     0     0     2     2     0     0; ...
    0     3     3     3     0     0     0     4; ...
    3     3     3     3     0     0     4     4; ...
    3     3     3     0     5     0     0     4; ...
    3     3     0     5     5     0     4     4; ...
    0     0     0     5     5     0     0     4; ...
    0     0     0     0     0     0     4     4; ...
    0     6     0     6     0     6     0     0; ...
    0     6     0     6     0     6     0     6; ...
    6     6     6     6     6     6     6     6; ...
    6     6     6     6     6     6     6     6; ...
    0     6     0     6     0     6     0     0]; ...


% imagesc(flip(img_labels, 1))
imagesc(img_labels)
img_labels

len_y = size(img_labels, 1);
len_x = size(img_labels, 2);

binary_mask = zeros(size(img_labels));
for i = 1:len_y
    for j = 1:len_x
        
        if img_labels(i,j) > 0
            binary_mask1(i,j) = i;
            binary_mask2(i,j) = j;
        end

    end
end

x = binary_mask1(:);
y = binary_mask2(:);

hold on
scatter(y,x, 'cyan','filled')
set(gca, 'DataAspectRatio', [1,1,1])
grid on


x_grid = repmat(1:len_x, len_y, 1);
y_grid = repmat((1:len_y)', 1, len_x);
I_grid = double(img_labels>0); % Replace this with the true monochrome intensity image

for i = 1:max(img_labels(:))

    label_idx = img_labels==i;

    x_val = x_grid(label_idx);
    y_val = y_grid(label_idx);
    weights = I_grid(label_idx);

    x_center = sum(x_val .* weights) ./ sum(weights) ;
    y_center = sum(y_val .* weights) ./ sum(weights) ;

    scatter(x_center, y_center, 'red', 'filled')

    
    x_spread = mean((x_center - x_val).^2);


end


I  =  ones(size(img_labels));
tic
S = star_stats(img_labels, I)
toc


function S = star_stats(L, I, opts)
%STAR_STATS Fast per-object centroid, shape and quality parameters.
%   S = STAR_STATS(L, I) measures every object in the label image L using
%   intensity-weighted image moments of I. No fitting and no loop over
%   objects: all sums are done in one pass with ACCUMARRAY, so the cost
%   scales with the number of labelled pixels, not the number of objects.
%
%   L    label image, 0 = background, 1..N = objects (e.g. from bwlabel)
%   I    background-subtracted image, same size as L
%   opts optional struct:
%        .saturation  saturation level in units of I, i.e. raw saturation
%                     minus local background (default Inf = never)
%        .bg_sigma    background RMS per pixel, for SNR (default NaN)
%        .gain        e-/ADU, for SNR (default 1)
%
%   S is a struct of N-by-1 column vectors (use struct2table(S) for a table):
%     label       object label
%     npix        number of pixels in the object
%     flux        sum of I over the object
%     peak        brightest pixel value
%     x, y        intensity-weighted centroid (x = column, y = row)
%     a, b        RMS size along major / minor axis [px]
%     theta       major-axis angle [deg] from +x towards +y (rows), i.e.
%                 clockwise on screen with imagesc's default axis ij
%     roundness   b/a, 1 = perfectly round
%     ellipticity 1 - b/a
%     fwhm        Gaussian-equivalent FWHM = 2.3548*sqrt(a*b) [px]
%     peak_frac   peak/flux: ~1 for hot pixels and cosmic rays,
%                 small for extended objects
%     peak_offset distance between brightest pixel and centroid [px];
%                 large values hint at blends or double stars
%     saturated   true if any pixel reaches opts.saturation
%     edge        true if the object touches the image border
%     snr         flux / sqrt(flux/gain + npix*bg_sigma^2)

if nargin < 3, opts = struct(); end
if ~isfield(opts, 'saturation'), opts.saturation = Inf; end
if ~isfield(opts, 'bg_sigma'),   opts.bg_sigma   = NaN; end
if ~isfield(opts, 'gain'),       opts.gain       = 1;   end

[ny, nx] = size(L);
idx = find(L > 0);
lab = double(L(idx));
raw = double(I(idx));
w   = max(raw, 0);                 % negative pixels would break the moments
[y, x] = ind2sub([ny, nx], idx); % get indices to the pixels having a label 
N   = max([lab; 0]);

acc = @(v) accumarray(lab, v, [N, 1]);

% zeroth and first moments
npix = acc(ones(size(lab)));
flux = acc(w);
xc   = acc(w .* x) ./ flux;
yc   = acc(w .* y) ./ flux;

% central second moments (two-pass, numerically safe for large images)
dx  = x - xc(lab);
dy  = y - yc(lab);
mxx = acc(w .* dx.^2)    ./ flux;
myy = acc(w .* dy.^2)    ./ flux;
mxy = acc(w .* dx .* dy) ./ flux;

% eigenvalues of the 2x2 covariance matrix, in closed form
mid   = (mxx + myy) / 2;
dev   = sqrt(((mxx - myy) / 2).^2 + mxy.^2);
a     = sqrt(mid + dev);
b     = sqrt(max(mid - dev, 0));
theta = 0.5 * atan2(2 * mxy, mxx - myy) * 180 / pi;

% brightest pixel of each object (one sort instead of a loop)
[~, order]  = sort(w, 'descend');
[ul, first] = unique(lab(order), 'first');
pk   = order(first);
peak = nan(N, 1); xpk = nan(N, 1); ypk = nan(N, 1);
peak(ul) = raw(pk); xpk(ul) = x(pk); ypk(ul) = y(pk);

S.label       = (1:N)';
S.npix        = npix;
S.flux        = flux;
S.peak        = peak;
S.x           = xc;
S.y           = yc;
S.a           = a;
S.b           = b;
S.theta       = theta;
S.roundness   = b ./ a;
S.ellipticity = 1 - b ./ a;
S.fwhm        = 2.3548 * sqrt(a .* b);
S.peak_frac   = peak ./ flux;
S.peak_offset = hypot(xc - xpk, yc - ypk);
S.saturated   = acc(double(raw >= opts.saturation)) > 0;
S.edge        = acc(double(x == 1 | x == nx | y == 1 | y == ny)) > 0;
S.snr         = flux ./ sqrt(flux / opts.gain + npix * opts.bg_sigma^2);
end











