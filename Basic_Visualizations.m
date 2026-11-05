clear
close all

% Location on earth
longitude = 46 * pi/180;

declination = -46 * pi/180;
right_acension = 0 * pi/180;


% FoV of a micro fourd thirds sensor 17mm x 13.2mm combined with lense of 150mm focal length
a_v = 4.9625 .* pi/180; % vertical field of view
a_h = 6.6008 .* pi/180; % horizontal field of view

a_v = 24.4000 .* pi/180; % vertical field of view
a_h = 18.4508 .* pi/180; % horizontal field of view

% a_v = 10 / 60 .* pi/180; % vertical field of view
% a_h = 10 / 60 .* pi/180; % horizontal field of view

% % % Human FoV
% a_v = 130 * pi/180; % vertical field of view
% a_h = 120 * pi/180; % horizontal field of view

phi = 2 * pi/180;


R_2D = @(phi) [cos(phi), -sin(phi); sin(phi), cos(phi)];
R_3D_x = @(phi) [1, 0, 0; 0, cos(phi), -sin(phi); 0, sin(phi), cos(phi)];
R_3D_y = @(phi) [cos(phi), 0, sin(phi); 0, 1, 0; -sin(phi), 0, cos(phi)];
R_3D_z = @(phi) [cos(phi), -sin(phi), 0; sin(phi), cos(phi), 0; 0, 0 ,1];


r_equator = 4;
r_breite = cos(longitude) * r_equator;
hight_breite = sin(longitude) * r_equator;

view_vec_ori = [r_breite; 0; hight_breite];
view_vec_dir = [300; 0; tan(longitude) * 300];


u = view_vec_dir ./ norm(view_vec_dir);

% Built rotation matrix with the vector u as rotation axis
K = [    0, -u(3),  u(2);
      u(3),     0, -u(1);
     -u(2),  u(1),    0];

R_3D_u = @(phi) eye(3) + sin(phi).*K + (1 - cos(phi))*K*K; 


% Field of view constraints
fov_vec_NW = R_3D_y(a_v/2)  * R_3D_z(a_h/2)  * view_vec_dir;
fov_vec_NE = R_3D_y(a_v/2)  * R_3D_z(-a_h/2) * view_vec_dir;
fov_vec_SW = R_3D_y(-a_v/2) * R_3D_z(a_h/2)  * view_vec_dir;
fov_vec_SE = R_3D_y(-a_v/2) * R_3D_z(-a_h/2) * view_vec_dir;

% Final ausrichtung
view_vec_dir = R_3D_y(-declination) * view_vec_dir;
fov_vec_NW   = R_3D_y(-declination) * fov_vec_NW;
fov_vec_NE   = R_3D_y(-declination) * fov_vec_NE;
fov_vec_SW   = R_3D_y(-declination) * fov_vec_SW;
fov_vec_SE   = R_3D_y(-declination) * fov_vec_SE;


view_vec_dir = R_3D_z(right_acension) * view_vec_dir;
fov_vec_NW   = R_3D_z(right_acension) * fov_vec_NW;
fov_vec_NE   = R_3D_z(right_acension) * fov_vec_NE;
fov_vec_SW   = R_3D_z(right_acension) * fov_vec_SW;
fov_vec_SE   = R_3D_z(right_acension) * fov_vec_SE;

% Create Canvas
res = 200;
zero = zeros(1, res);
x_ring = linspace(-r_equator, r_equator, res);
y_ring_up = sqrt(r_equator.^2 - x_ring.^2);
y_ring_lo = -sqrt(r_equator.^2 - x_ring.^2);

breite_x = cos(longitude).*x_ring;
breite_y_up = cos(longitude).*y_ring_up;
breite_y_lo = cos(longitude).*y_ring_lo;
breite_z = repmat(hight_breite, 1, res);



hold on
grid on

addSphereGridZ(r_equator, 10, 'all')

plot3(x_ring, y_ring_up, zero, 'LineWidth', 2, 'Color', 'k', 'HandleVisibility','off')
plot3(x_ring, y_ring_lo, zero, 'LineWidth', 2, 'Color', 'k', 'HandleVisibility','off')


plot3(breite_x, breite_y_up, breite_z, 'LineWidth', 2, 'Color', 'k', 'HandleVisibility','off')
plot3(breite_x, breite_y_lo, breite_z, 'LineWidth', 2, 'Color', 'k', 'HandleVisibility','off')


pole = plot3([0,0], [0,0], [5,-5], 'LineWidth', 2,  'Color', 'b', 'LineStyle', '-.');

tracker = scatter3(view_vec_ori(1), view_vec_ori(2), hight_breite, 400,  'filled', 'MarkerEdgeColor', 'k', 'MarkerFaceColor', [0.7,0,0.8], 'Marker', 'hexagram');
observer = scatter3(view_vec_ori(1), view_vec_ori(2), hight_breite, 100, 'filled', 'MarkerEdgeColor', 'k', 'MarkerFaceColor', 'y');
scatter3(0, 0, 0, 100, 'filled', 'MarkerEdgeColor', 'k', 'MarkerFaceColor', 'g', 'LineWidth', 3);


zenith = plot3([view_vec_ori(1); view_vec_ori(1)*100], ...
    [view_vec_ori(2); view_vec_ori(2)*100], ...
    [view_vec_ori(3); view_vec_ori(3)*100], 'LineWidth', 2, 'Color', 'g');


viewline = plot3([view_vec_ori(1); view_vec_ori(1) + view_vec_dir(1)], ...
    [view_vec_ori(2); view_vec_ori(2) + view_vec_dir(2)], ...
    [view_vec_ori(3); view_vec_ori(3) + view_vec_dir(3)], 'LineWidth', 2, 'Color', 'r', 'LineStyle', '-.');

viewline_NW = plot3([view_vec_ori(1); view_vec_ori(1) + fov_vec_NW(1)], ...
                    [view_vec_ori(2); view_vec_ori(2) + fov_vec_NW(2)], ...
                    [view_vec_ori(3); view_vec_ori(3) + fov_vec_NW(3)], 'LineWidth', 2, 'Color', 'm');


viewline_NE = plot3([view_vec_ori(1); view_vec_ori(1) + fov_vec_NE(1)], ...
                    [view_vec_ori(2); view_vec_ori(2) + fov_vec_NE(2)], ...
                    [view_vec_ori(3); view_vec_ori(3) + fov_vec_NE(3)], 'LineWidth', 2, 'Color', 'm');

viewline_SW = plot3([view_vec_ori(1); view_vec_ori(1) + fov_vec_SW(1)], ...
                    [view_vec_ori(2); view_vec_ori(2) + fov_vec_SW(2)], ...
                    [view_vec_ori(3); view_vec_ori(3) + fov_vec_SW(3)], 'LineWidth', 2, 'Color', 'm');

viewline_SE = plot3([view_vec_ori(1); view_vec_ori(1) + fov_vec_SE(1)], ...
                    [view_vec_ori(2); view_vec_ori(2) + fov_vec_SE(2)], ...
                    [view_vec_ori(3); view_vec_ori(3) + fov_vec_SE(3)], 'LineWidth', 2, 'Color', 'm');



view([-80, 15])

xlim([-10,10])
ylim([-10,10])
zlim([-10,10])

set(gca, 'DataAspectRatio', [1,1,1])


n_iter = 500;

angle = 0;


for i = 1:n_iter

    angle = angle + phi;

    % Rotate the earth with the observer
    view_vec_ori_current = R_3D_z(angle)*view_vec_ori;
    view_vec_dir_current = R_3D_z(angle)*view_vec_dir;

    fov_vec_NW = R_3D_z(phi)*fov_vec_NW;
    fov_vec_NE = R_3D_z(phi)*fov_vec_NE;
    fov_vec_SW = R_3D_z(phi)*fov_vec_SW;
    fov_vec_SE = R_3D_z(phi)*fov_vec_SE;

    % Simulate tracker by rotating th evector backwards
    view_vec_tracked_dir = R_3D_z(-angle)*view_vec_dir_current;

    tracked_fov_vec_NW = R_3D_z(-angle)*fov_vec_NW;
    tracked_fov_vec_NE = R_3D_z(-angle)*fov_vec_NE;
    tracked_fov_vec_SW = R_3D_z(-angle)*fov_vec_SW;
    tracked_fov_vec_SE = R_3D_z(-angle)*fov_vec_SE;

    % Plotting
    v_x = view_vec_ori_current(1);
    v_y = view_vec_ori_current(2);
    v_z = view_vec_ori_current(3);

    observer.XData = v_x;
    observer.YData = v_y;
    observer.ZData = v_z;

    tracker.XData = v_x;
    tracker.YData = v_y;
    tracker.ZData = v_z;

    zenith.XData = [v_x; v_x + view_vec_ori_current(1)*100];
    zenith.YData = [v_y; v_y + view_vec_ori_current(2)*100];
    zenith.ZData = [v_z; v_z + view_vec_ori_current(3)*100];

    viewline.XData = [v_x; v_x + view_vec_tracked_dir(1)];
    viewline.YData = [v_y; v_y + view_vec_tracked_dir(2)];
    viewline.ZData = [v_z; v_z + view_vec_tracked_dir(3)];


    % viewline_NW.XData = [v_x; v_x + fov_vec_NW(1)];
    % viewline_NW.YData = [v_y; v_y + fov_vec_NW(2)];
    % viewline_NW.ZData = [v_z; v_z + fov_vec_NW(3)];
    % viewline_NE.XData = [v_x; v_x + fov_vec_NE(1)];
    % viewline_NE.YData = [v_y; v_y + fov_vec_NE(2)];
    % viewline_NE.ZData = [v_z; v_z + fov_vec_NE(3)];
    % viewline_SW.XData = [v_x; v_x + fov_vec_SW(1)];
    % viewline_SW.YData = [v_y; v_y + fov_vec_SW(2)];
    % viewline_SW.ZData = [v_z; v_z + fov_vec_SW(3)];
    % viewline_SE.XData = [v_x; v_x + fov_vec_SE(1)];
    % viewline_SE.YData = [v_y; v_y + fov_vec_SE(2)];
    % viewline_SE.ZData = [v_z; v_z + fov_vec_SE(3)];


    viewline_NW.XData = [v_x; v_x + tracked_fov_vec_NW(1)];
    viewline_NW.YData = [v_y; v_y + tracked_fov_vec_NW(2)];
    viewline_NW.ZData = [v_z; v_z + tracked_fov_vec_NW(3)];
    viewline_NE.XData = [v_x; v_x + tracked_fov_vec_NE(1)];
    viewline_NE.YData = [v_y; v_y + tracked_fov_vec_NE(2)];
    viewline_NE.ZData = [v_z; v_z + tracked_fov_vec_NE(3)];
    viewline_SW.XData = [v_x; v_x + tracked_fov_vec_SW(1)];
    viewline_SW.YData = [v_y; v_y + tracked_fov_vec_SW(2)];
    viewline_SW.ZData = [v_z; v_z + tracked_fov_vec_SW(3)];
    viewline_SE.XData = [v_x; v_x + tracked_fov_vec_SE(1)];
    viewline_SE.YData = [v_y; v_y + tracked_fov_vec_SE(2)];
    viewline_SE.ZData = [v_z; v_z + tracked_fov_vec_SE(3)];


    % viewline.XData = [view_vec_ori_current(1); view_vec_ori_current(1) + (view_vec_dir_current(1) - view_vec_tracked_dir(1))];
    % viewline.YData = [view_vec_ori_current(2); view_vec_ori_current(2) + (view_vec_dir_current(2) - view_vec_tracked_dir(2))];

    drawnow
    pause(1/30)


end





function addSphereGridZ(r_equator, delta, dim)

R_3D_x = @(phi) [1, 0, 0; 0, cos(phi), -sin(phi); 0, sin(phi), cos(phi)];
R_3D_y = @(phi) [cos(phi), 0, sin(phi); 0, 1, 0; -sin(phi), 0, cos(phi)];
R_3D_z = @(phi) [cos(phi), -sin(phi), 0; sin(phi), cos(phi), 0; 0, 0 ,1];


res = 100;

min_angle = 10;

n = round((180 - 2*min_angle)./delta);

breitengrade = flip([0, linspace(-90 + min_angle, 90 - min_angle, n)]);


for i = 1:n

    r_i = cosd(breitengrade(i)) .* r_equator;
    height = sind(breitengrade(i)) .* r_equator;

    z_arr = height .* ones(1,res);

    x_ring = linspace(-r_i, r_i, res);
    y_ring_up = sqrt(r_i.^2 - x_ring.^2);
    y_ring_lo = -sqrt(r_i.^2 - x_ring.^2);

    if strcmp(dim, 'all') || strcmp(dim, 'z') 

        plot3(x_ring, y_ring_up, z_arr, 'LineWidth', 1, 'Color', [0.5, 0.5, 0.5], 'HandleVisibility','off')
        plot3(x_ring, y_ring_lo, z_arr, 'LineWidth', 1, 'Color', [0.5, 0.5, 0.5], 'HandleVisibility','off')

    end

    % v_up = [x_ring; y_ring_up; z_arr];
    % v_lo = [x_ring; y_ring_lo; z_arr];

    % if strcmp(dim, 'all') ||  strcmp(dim, 'y')
    % 
    %     v_up_y = R_3D_y(90 * pi/180)*v_up; 
    %     v_lo_y = R_3D_y(90 * pi/180)*v_lo; 
    % 
    %     plot3(v_up_y(1,:), v_up_y(2,:), v_up_y(3,:), 'LineWidth', 1, 'Color', [0.5, 0.5, 0.5], 'HandleVisibility','off')
    %     plot3(v_lo_y(1,:), v_lo_y(2,:), v_lo_y(3,:), 'LineWidth', 1, 'Color', [0.5, 0.5, 0.5], 'HandleVisibility','off')
    % 
    % end
    % 
    % if strcmp(dim, 'all') ||  strcmp(dim, 'x')
    % 
    %     v_up_x = R_3D_x(90 * pi/180)*v_up; 
    %     v_lo_x = R_3D_x(90 * pi/180)*v_lo; 
    % 
    %     plot3(v_up_x(1,:), v_up_x(2,:), v_up_x(3,:), 'LineWidth', 1, 'Color', [0.5, 0.5, 0.5], 'HandleVisibility','off')
    %     plot3(v_lo_x(1,:), v_lo_x(2,:), v_lo_x(3,:), 'LineWidth', 1, 'Color', [0.5, 0.5, 0.5], 'HandleVisibility','off')
    % end

end


z_arr = 0 .* ones(1,res);

x_ring = linspace(-r_equator, r_equator, res);
y_ring_up = sqrt(r_equator.^2 - x_ring.^2);
y_ring_lo = -sqrt(r_equator.^2 - x_ring.^2);

v_up = [x_ring; y_ring_up; z_arr];
v_lo = [x_ring; y_ring_lo; z_arr];

v_up_y = R_3D_y(90 * pi/180)*v_up;
v_lo_y = R_3D_y(90 * pi/180)*v_lo;

delta = 3*delta;

n = round(360 / delta);


for i = 1:n

    v_up_y = R_3D_z(delta * pi/180)*v_up_y ;
    v_lo_y = R_3D_z(delta * pi/180)*v_lo_y ;

    plot3(v_up_y(1,:), v_up_y(2,:), v_up_y(3,:), 'LineWidth', 1, 'Color', [0.5, 0.5, 0.5], 'HandleVisibility','off')
    plot3(v_lo_y(1,:), v_lo_y(2,:), v_lo_y(3,:), 'LineWidth', 1, 'Color', [0.5, 0.5, 0.5], 'HandleVisibility','off')

end



end
















% % 2D
% 
% clear
% close all
% 
% 
% breitengrad = 45 * pi/180;
% 
% 
% phi = 2 * pi/180;
% 
% 
% 
% R_2D = @(phi) [cos(phi), -sin(phi); sin(phi), cos(phi)];
% 
% 
% r = 4;
% 
% view_vec_ori = [r;0];
% view_vec_dir = [3;0];
% 
% 
% 
% % Create Canvas
% res = 200;
% x_ring = linspace(-r, r, res);
% y_ring_up = sqrt(r.^2 - x_ring.^2);
% y_ring_lo = -sqrt(r.^2 - x_ring.^2);
% 
% 
% hold on
% grid on
% plot(x_ring, y_ring_up, 'LineWidth', 2, 'Color', 'k', 'HandleVisibility','off')
% plot(x_ring, y_ring_lo, 'LineWidth', 2, 'Color', 'k', 'HandleVisibility','off')
% 
% plot(cos(breitengrad).*x_ring, cos(breitengrad).*y_ring_up, 'LineWidth', 2, 'Color', 'k', 'HandleVisibility','off')
% plot(cos(breitengrad).*x_ring, cos(breitengrad).*y_ring_lo, 'LineWidth', 2, 'Color', 'k', 'HandleVisibility','off')
% 
% 
% pole = scatter(0, 0, 100, 'filled', 'MarkerFaceColor', 'b');
% 
% tracker = scatter(view_vec_ori(1), view_vec_ori(2), 400, 'filled', 'MarkerEdgeColor', 'k', 'MarkerFaceColor', [0.7,0,0.8], 'Marker', 'hexagram');
% observer = scatter(view_vec_ori(1), view_vec_ori(2), 100, 'filled', 'MarkerEdgeColor', 'k', 'MarkerFaceColor', 'y');
% 
% 
% zenith = plot([view_vec_ori(1); view_vec_ori(1) + view_vec_dir(1)], [view_vec_ori(2); view_vec_ori(2) + view_vec_dir(2)], 'LineWidth', 2, 'Color', 'g');
% viewline = plot([view_vec_ori(1); view_vec_ori(1) + view_vec_dir(1)], [view_vec_ori(2); view_vec_ori(2) + view_vec_dir(2)], 'LineWidth', 2, 'Color', 'r');
% 
% 
% xlim([-10,10])
% ylim([-10,10])
% 
% set(gca, 'DataAspectRatio', [1,1,1])
% 
% 
% n_iter = 500;
% 
% angle = 0;
% 
% 
% for i = 1:n_iter
% 
%     angle = angle + phi;
% 
%     % Rotate the earth with the observer
%     view_vec_ori_current = R_2D(angle)*view_vec_ori;
%     view_vec_dir_current = R_2D(angle)*view_vec_dir;
% 
%     view_vec_tracked_dir = R_2D(-angle)*view_vec_dir_current;
% 
% 
%     observer.XData = view_vec_ori_current(1);
%     observer.YData = view_vec_ori_current(2);
% 
%     tracker.XData = view_vec_ori_current(1);
%     tracker.YData = view_vec_ori_current(2);
% 
%     zenith.XData = [view_vec_ori_current(1); view_vec_ori_current(1) + view_vec_dir_current(1)];
%     zenith.YData = [view_vec_ori_current(2); view_vec_ori_current(2) + view_vec_dir_current(2)];
% 
%     viewline.XData = [view_vec_ori_current(1); view_vec_ori_current(1) + view_vec_tracked_dir(1)];
%     viewline.YData = [view_vec_ori_current(2); view_vec_ori_current(2) + view_vec_tracked_dir(2)];
% 
%     % viewline.XData = [view_vec_ori_current(1); view_vec_ori_current(1) + (view_vec_dir_current(1) - view_vec_tracked_dir(1))];
%     % viewline.YData = [view_vec_ori_current(2); view_vec_ori_current(2) + (view_vec_dir_current(2) - view_vec_tracked_dir(2))];
% 
%     drawnow
%     pause(1/30)
% 
% 
% 
% end
% 
% 
% 
