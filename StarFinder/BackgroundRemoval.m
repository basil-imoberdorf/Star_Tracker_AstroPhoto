clear
close all

canvas_width = 1200;
canvas_height = 3/4 * canvas_width; % Olympus Micro Four Thirds has an aspect ratio of 4:3

fig = figure('Position', [100, 100, canvas_width, canvas_height]);

% addpath('path-to-readraw')
addpath('C:\Users\basil\Documents\Astrophotographie\Scripts\read_raw_images-21.8.0')
readraw;
r = readraw('-4', '-d', '-j');
% dc = readraw();

img = imread('..\..\Plejaden_13092026\flats\_9138908.ORF');

% img = imread('..\..\Andromeda_14092026\lights\_9140564.ORF');


% % 1. Import-Optionen erstellen
% opts = rawreadOptions();
% 
% % 2. MATLAB anweisen, die Daten absolut unberührt zu lassen (reine ADC-Counts)
% opts.Unprocessed = true;
% 
% % 3. Bild einlesen - liefert eine einzige 2D-Matrix (Höhe x Breite)
% img_adc = rawread('..\..\Andromeda_14092026\lights\_9140564.ORF', opts);


red_channel   = img(:,:,1);
green_channel = img(:,:,2);
blue_channel  = img(:,:,3);

% histogram(img(:), 2^16) % Bin in 2^16 bins since the raw data is in uint16



hold on
hist_r = histogram(red_channel, 2^16);
hist_g = histogram(green_channel, 2^16);
hist_b = histogram(blue_channel, 2^16);
% hist_r.EdgeColor = 'none';

hist_r.FaceColor = 'r';
hist_g.FaceColor = 'g';
hist_b.FaceColor = 'b';

hist_r.EdgeAlpha = 0;
hist_g.EdgeAlpha = 0;
hist_b.EdgeAlpha = 0;

set(gca, 'YScale', 'log')

xlim([0, 2^16])

img(1:10,1:10,:)

class(img)

max(img,[],'all')


img = double(img);

class(img)

max(img,[],'all')


img_norm = img ./ 2^16;


max(img_norm,[],'all')


imshow(1 - double(img))






% imshow(img)

imagesc(mean(double(img),3))

set(gca, 'DataAspectRatio', [4, 3, 1])


% Step 1: Define the folder path and file pattern
myFolder = '..\TestData'; % Replace with your folder path
filePattern = fullfile(myFolder, '*.jpg'); % Change '*.jpg' to '*.png' or '*.tif' if needed

% Step 2: Get a list of all matching files
imageFiles = dir(filePattern);

n_img = length(imageFiles);

% Step 3: Loop through each file and read it
imagesCell = cell(length(imageFiles), 1); % Pre-allocate cell array for varying sizes
for k = 1:length(imageFiles)
    baseFileName = imageFiles(k).name;
    fullFileName = fullfile(myFolder, baseFileName);
    
    % Read the image
    imagesCell{k} = imread(fullFileName);
    
    % Optional: display progress or process image
    fprintf('Read image %s\n', baseFileName);
end







%%%%%%%%%%%%%%%%%%%%%%%%%
% Display four images
width = 1200; % pixel
figure('Position', [100, 100, width, 3/4*width])

x_pos = [0, 0, 0.5, 0.5];
y_pos = [0, 0.5, 0, 0.5];

for i = 1:4
    
    ax = axes('Position', [x_pos(i), y_pos(i), 0.5, 0.5]);
    % imshow(imagesCell{i})

    pooled_img = pool_rgb(imagesCell{1}, 'r');
    imshow(pooled_img)
end


%%%%%%%%%%%%%%%%%%%%%%%%%
% Display four images
width = 1200; % pixel
figure('Position', [100, 100, width, 3/4*width])

x_pos = [0, 0, 0.5, 0.5];
y_pos = [0, 0.5, 0, 0.5];

for i = 1:4
    
    ax = axes('Position', [x_pos(i), y_pos(i), 0.5, 0.5]);
    % imshow(imagesCell{i})

    pooled_img = pool_rgb(imagesCell{1}, 'g');
    imshow(pooled_img)
end


%%%%%%%%%%%%%%%%%%%%%%%%%
% Display four images
width = 1200; % pixel
figure('Position', [100, 100, width, 3/4*width])

x_pos = [0, 0, 0.5, 0.5];
y_pos = [0, 0.5, 0, 0.5];

for i = 1:4
    
    ax = axes('Position', [x_pos(i), y_pos(i), 0.5, 0.5]);
    % imshow(imagesCell{i})

    pooled_img = pool_rgb(imagesCell{1}, 'b');
    imshow(pooled_img)
end





%--------------------------------------------------------------------------
% Helper functions
%--------------------------------------------------------------------------
function pooled_img = pool_rgb(img, method)


    switch method
        case 'r'
            pooled_img = img(:,:,1);
        case 'g'
            pooled_img = img(:,:,2);
        case 'b'
            pooled_img = img(:,:,3);

        case 'avg'
            pooled_img = uint8(sum(img, 3) ./ 3);

        case 'max'
            pooled_img = max(img, [], 3);

        case 'weighted'


        case 'noise'


    end


end




%--------------------------------------------------------------------------
function remove_bg_global_thresh(img, thresh)








end


















