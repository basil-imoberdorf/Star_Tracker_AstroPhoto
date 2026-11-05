clear
close all



R = @(theta) [cosd(theta), -sind(theta); sind(theta), cosd(theta)];

n = 5;
k = 3;
factorial(n)./(factorial(k).*factorial(n-k))


t = [-2;5];

p = randn(2,10) + [2;3];


theta = 90;

q = R(theta)*p + t;


scatter(p(1,:), p(2,:), 'filled')
hold on
scatter(q(1,:), q(2,:), 'filled')


grid on



p_avg = mean(p, 2);
q_avg = mean(q, 2);


p_dash = p - p_avg;
q_dash = q - q_avg;


C = p_dash*q_dash';


[U, S, V] = svd(C);



d = sign(det(V*U'))
B = diag([1,d])


R_opt = V*B*U'
R(theta)


t_opt = q_avg - R_opt*p_avg
t



q_pred = R_opt*p + t_opt;




scatter(q_pred(1,:), q_pred(2,:))















