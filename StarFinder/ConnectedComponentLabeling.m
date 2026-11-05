clear
close all


% 
% 
% img_width = 1200;
% img_height = 900;
% 
% 
% x_center = [img_width*0.2, img_width*0.4, img_width*0.7, img_width*0.5];
% y_center = [img_height*0.8, img_height*0.3, img_height*0.5, img_height*0.1];
% 
% r = [50, 20, 30, 30];
% 
% n_circ = length(r);
% 
% 
% img_mask = zeros(img_height, img_width);
% img = zeros(img_height, img_width, 3);
% 
% for i = 1: img_height
%     for j = 1:img_width
%         for k = 1:n_circ
%             if incircle(j, i, x_center(k), y_center(k), r(k))
%                 img_mask(i,j) = 1;
%             end
%         end
%     end
% end


img_mask = [1, 1, 0, 0, 1, 1, 0, 0;...
1, 0, 0, 0, 1, 1, 0, 0;...
0, 1, 1, 1, 0, 0, 0, 1;...
1, 1, 1, 1, 0, 0, 1, 1;...
1, 1, 1, 0, 0, 0, 0, 1;...
1, 1, 0, 1, 1, 0, 1, 1;...
0, 0, 0, 1, 0, 0, 0, 1;...
0, 0, 0, 0, 0, 0, 1, 1;...
0, 1, 0, 1, 0, 1, 0, 0;...
0, 1, 0, 1, 0, 1, 0, 1;...
1, 1, 1, 1, 1, 1, 1, 1;...
1, 1, 1, 1, 1, 1, 1, 1;...
0, 1, 0, 1, 0, 1, 0, 0];

img_width = size(img_mask, 2);
img_height = size(img_mask, 1);
% 
% img_mask = repmat(img_mask, 20, 20);

% imagesc(img_mask)
% set(gca, 'DataAspectRatio', [1,1,1])



% Connected Component Labeling Algorithm
len_x = size(img_mask, 2);
len_y = size(img_mask, 1);

img_ccl = zeros(size(img_mask));

parent = 1:ceil(len_y*len_x/2) + 1; % Worst case is checkerboard pattern where half the pixels get a new label
label_counter = 0;

first_pass = tic;
for i = 1:len_y
    for j = 1:len_x
        if img_mask(i, j)
            % Edge guard y-axis
            if i > 1
                top_label = img_ccl(i-1, j);
            else  
                top_label = 0; 
            end
            % Edge guard x-axis
            if j > 1
                left_label = img_ccl(i, j-1);
            else
                left_label = 0;
            end

            % Check if the pixel touches another above or to the left
            if top_label == 0 && left_label == 0
                % NEW LABEL: Incerease counter and apply label
                label_counter = label_counter + 1;
                img_ccl(i, j) = label_counter;

            elseif left_label==0
                img_ccl(i, j) = top_label;

            elseif top_label==0
                img_ccl(i, j) = left_label;

            elseif top_label == left_label
                % Both the above and the left pixel belong to the same object.
                img_ccl(i, j) = left_label;
            else
                % Two objects with different label touch so do the union operation to merge the objects
                img_ccl(i, j) = left_label;
                parent = Union(top_label, left_label, parent);
            end
        end
    end
end
toc(first_pass)
% img_ccl
% Truncate unused over-preallocated entries
parent = parent(1:label_counter);

% img_ccl


for i = 1:length(parent)
    roots(i) = Find(i, parent);
end

% % Prepare conversion map to have labels starting from 1 to number of labels
% % Resolve every provisional label to its root once
% second_pass = tic;
% root = zeros(1, label_counter);
% for k = 1:label_counter
%     root(k) = Find(k, parent);
% end
% 
% is_root = parent == 1:label_counter; % a root is its own parent
% map = zeros(1, label_counter);
% map(is_root) = 1:nnz(is_root); % fill the places where the roots are with the numbers from 1 to number of roots
% 
% 
% % Roots are labels that point to themselves -> number them 1..N
% is_root = parent == 1:label_counter;
% map = zeros(1, label_counter);
% map(is_root) = 1:nnz(is_root);
% final_label = map(root);          % provisional label -> final consecutive label
% 
% % Second pass (vectorized)
% fg = img_ccl > 0;
% img_ccl(fg) = final_label(img_ccl(fg));



% Second pass: Correct the labels
second_pass = tic;

% Roots are labels that point to themselves -> number them 1..N
is_root = parent == 1:label_counter;
map = zeros(1, label_counter);
map(is_root) = 1:nnz(is_root);

for i = 1:len_y
    for j = 1:len_x
        if img_ccl(i,j) ~= 0
            img_ccl(i,j) = map(Find(img_ccl(i,j), parent));
        end
    end
end
toc(second_pass)


total_time = toc(first_pass);

img_ccl

tic
L = ccl_uf(img_mask);
toc


imagesc(img_ccl)
colormap("colorcube")

% imagesc(img_ccl)
% colormap("colorcube")
% set(gca, 'DataAspectRatio', [1,1,1])



tic
img_ccl_matlab = bwlabel(img_mask, 4);
matlab_time = toc;

tic
img_ccl_me = ccl_v1(img_mask);
me_time = toc;


speedup_of_unionfind_vs_naivet = me_time / total_time
speedup_of_matlab_vs_my_unionfind = total_time/matlab_time
speedup_of_matlab_vs_my_naive_approach = me_time/matlab_time


% imagesc(img_ccl_me)
% colormap("colorcube")
% set(gca, 'DataAspectRatio', [1,1,1])

% Helper functions
function bool = incircle(x, y, a, b, r)

    bool = (x - a).^2 + (y - b).^2 < r.^2;

end




%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function root = Find(x, parent)
while parent(x) ~= x
    x = parent(x);
end
root = x;
end



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function parent = Union(a, b, parent)

root_a = Find(a, parent);
root_b = Find(b, parent);

if root_a > root_b
    parent(root_a) = root_b;
else
    parent(root_b) = root_a;
end
end

% function parent = Union(a, b, parent)
% parent(Find(a, parent)) = Find(b, parent);
% end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function img_ccl = ccl_v1(img_mask)

len_x = size(img_mask, 2);
len_y = size(img_mask, 1);

img_ccl = zeros(size(img_mask));


label_counter = 0;
connectivity_counter = 0;

first_pass = tic;
for i = 1:len_y
    for j = 1:len_x

        top_idx = max(i-1, 1);
        left_idx = max(j-1, 1);

        if img_mask(i, j)

            top_label  = img_ccl(top_idx, j);
            left_label = img_ccl(i, left_idx);

            % Check if touches something above or to the left
            if top_label == 0 && left_label == 0
                % NEW LABEL: Incerease counter and apply label
                label_counter = label_counter + 1;
                img_ccl(i, j) = label_counter;

            elseif top_label~=left_label
                % FUSION: Two objects meet at an edge: Propagate the left label

                if left_label==0
                    img_ccl(i, j) = top_label;
                else
                    img_ccl(i, j) = left_label;
                    if top_label > 0 % if both labels are non-zero we have a connection between pixels of the same label
                        connectivity_counter = connectivity_counter + 1;
                        connectivity_list(connectivity_counter, 1) = top_label;
                        connectivity_list(connectivity_counter, 2) = left_label;
                    end
                end
 
            else
                % UNION EXTENSION: Both the above and the left pixel belong to the same object. 
                img_ccl(i, j) = left_label;
            end
        end
    end
end
toc(first_pass)

% img_ccl
% connectivity_list


% Create list of connected segments to
conn_list = cell(size(connectivity_list, 1), 1); % pre-allocate enough, worst case all pairs are individuals
conn_counter = 1;
delete_idx = 1; % to delete the current treated coonnectivity pair since after a loop the whole connectivitiy has been established

connectivity_pass = tic;
while ~isempty(connectivity_list)

    % Initialize the chain of connected elements with the first pair remaining in the connectivity list
    conn_list{conn_counter} = connectivity_list(1, :); 

    sublist = connectivity_list(2:end, :);

    for j = 1:size(sublist, 1)
        
        chain_idx = ismember(sublist(j, :), conn_list{conn_counter});

        if sum(chain_idx) == 1

            conn_list{conn_counter} = [conn_list{conn_counter}, sublist(j, ~chain_idx)];

            % Add to the list of pairs to be deleted so it doesnt get treated in the next round
            delete_idx = [delete_idx; j+1];

        elseif sum(chain_idx) == 2 % If both numbers are the same we can remove the connection since its already accounted for
            delete_idx = [delete_idx; j+1];
        end

    end

    % Remove the duplicates
    connectivity_list(delete_idx, :) = [];
    delete_idx = 1; % reset the delete indices

    conn_counter = conn_counter + 1;

end
toc(connectivity_pass)

conn_list = conn_list(~cellfun(@isempty, conn_list)); % remove cells without a list

% final pass
final_pass = tic;
for i = 1:length(conn_list)

    img_ccl(ismember(img_ccl, conn_list{i})) = min(conn_list{i});

end
toc(final_pass)


end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function L = ccl_uf(mask)
[ny, nx] = size(mask);
L = zeros(ny, nx);
% Worst case for 4-connectivity is a checkerboard: ~half the pixels get new labels
parent = zeros(ceil(ny*nx/2) + 1, 1);
nlab = 0;

% ---- First pass: provisional labels + union-find ----
% Column-major scan (MATLAB stores columns contiguously, so this is faster).
% Top and left neighbours are still already visited in this order.
for j = 1:nx
    for i = 1:ny
        if ~mask(i,j), continue; end
        up = 0; left = 0;
        if i > 1, up   = L(i-1,j); end
        if j > 1, left = L(i,j-1); end

        if up == 0 && left == 0          % new label
            nlab = nlab + 1;
            parent(nlab) = nlab;
            L(i,j) = nlab;
        elseif up == 0
            L(i,j) = left;
        elseif left == 0 || up == left
            L(i,j) = up;
        else                             % two different labels meet -> union
            L(i,j) = min(up, left);
            ra = up;   while parent(ra) ~= ra, parent(ra) = parent(parent(ra)); ra = parent(ra); end
            rb = left; while parent(rb) ~= rb, parent(rb) = parent(parent(rb)); rb = parent(rb); end
            if ra < rb
                parent(rb) = ra;         % always attach the larger root to the smaller
            elseif rb < ra
                parent(ra) = rb;
            end
        end
    end
end
parent = parent(1:nlab);

% ---- Flatten: every label points directly to its root ----
% Because larger roots are always attached under smaller ones, parent(k) < k for
% non-roots, so one increasing sweep is enough.
for k = 1:nlab
    parent(k) = parent(parent(k));
end

% ---- Relabel roots consecutively 1..N and apply (vectorized second pass) ----
isroot = parent == (1:nlab)';
map = zeros(nlab, 1);
map(isroot) = 1:nnz(isroot);
final = map(parent);
fg = L > 0;
L(fg) = final(L(fg));
end