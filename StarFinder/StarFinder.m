clear
close all


% img = imread('..\DSS_Outputs\Andromeda_200926_Home_&_Simplon.jpg');
img = imread('..\DSS_Outputs\Altair_KleinerGürtel.jpg');



img = double(img);


img = mean(img, 3);


imagesc(img)


mask = img > 210;


img_bright = img .* mask;

% % 
% imagesc(img_bright)

hold on
 imagesc(img_bright)




pixel_count_x = size(img, 1);
pixel_count_y = size(img, 2);

















