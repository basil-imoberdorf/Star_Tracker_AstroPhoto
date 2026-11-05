import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


# =================================================================================================
def update_triangle_plot(ax, vertices, color="red"):
    """
    vertices = [ax, bx, cx, ay, by, cy]
    """
    x = vertices[:3]
    y = vertices[3:]

    points = np.column_stack((x, y))

    # Close the triangle: A-B, B-C, C-A
    segments = [
        [points[0], points[1]],
        [points[1], points[2]],
        [points[2], points[0]],
    ]

    # Reuse the existing LineCollection if possible
    if not hasattr(ax, "_triangle_lines"):
        lc = LineCollection(segments, colors=color, linewidths=2)
        ax.add_collection(lc)
        ax._triangle_lines = lc
    else:
        ax._triangle_lines.set_segments(segments)
        ax._triangle_lines.set_color(color)

    ax.figure.canvas.draw_idle()
    ax.figure.canvas.flush_events()
    plt.pause(0.05)
    
    
# =================================================================================================
def fit_kabsch(p, q):
    
    p_avg = np.mean(p, axis=1, keepdims=True)
    q_avg = np.mean(q, axis=1, keepdims=True)

    p_dash = p - p_avg
    q_dash = q - q_avg
    
    C = p_dash @ np.transpose(q_dash)
    
    U,S,V_T = np.linalg.svd(C) # NumPy’s SVD returns Vᵀ, not V
    U_T = np.transpose(U)
    V = np.transpose(V_T)   
     
    d = np.sign(np.linalg.det(V @ U_T))
    B = np.diag([1,d])
    
    R = V @ B @ U_T
    t = q_avg - R @ p_avg
    
    return R, t 
        
        
# =================================================================================================   
def tri_match(xc_img1, yc_img1, n_pixel_img1,
              xc_img2, yc_img2, n_pixel_img2,
              N_STARS, K_NEIGH, TOL, debug_axes=None):
    
    # =================================================================================================
    # SUBSET SELECTION     
    # Select the top N_STARS from both images
    idx_img1 = np.argpartition(n_pixel_img1, -N_STARS)[-N_STARS:]  # get the unsorted indices to the largest values in n_pixel 
    xc_sub_img1 = xc_img1[idx_img1]
    yc_sub_img1 = yc_img1[idx_img1]
    
    idx_img2 = np.argpartition(n_pixel_img2, -N_STARS)[-N_STARS:]  # get the unsorted indices to the largest values in n_pixel 
    xc_sub_img2 = xc_img2[idx_img2]
    yc_sub_img2 = yc_img2[idx_img2]

    # Built triangles
    triang_sidelen_img1, triang_indices_img1, triang_count_img1 = get_triangle_sidelengths(xc_sub_img1, yc_sub_img1, N_STARS, K_NEIGH, TOL)
    triang_sidelen_img2, triang_indices_img2, triang_count_img2 = get_triangle_sidelengths(xc_sub_img2, yc_sub_img2, N_STARS, K_NEIGH, TOL)
    
    # Check if triangles were found and abort if not
    if triang_count_img1 == 0 or triang_count_img2 == 0:
        raise ValueError('No triangles available for matching!')
    
    # =================================================================================================
    # SEARCH FOR MATCHING TRIANGLES
    # Pre-allocate 
    match_idx = np.zeros([K_NEIGH*np.max([triang_count_img1, triang_count_img2]), 2]) # K_NEIGH as a buffer in case that one or more triangles match with multiple others
    match_count = 0
    
    for i in range(triang_count_img1):
        for j in range(triang_count_img2):
            
            diff = np.abs([triang_sidelen_img1[i, :] - triang_sidelen_img2[j, :]]) 
            
            if np.count_nonzero(diff < TOL) == 3:
                match_idx[match_count, :] = [i, j]
                match_count += 1
                                            
                # if debug_axes is not None:
                #     update_triangle_plot(
                #         debug_axes[0],
                #         triang_vertices_img1[i],
                #         color="red"
                #     )

                #     update_triangle_plot(
                #         debug_axes[1],
                #         triang_vertices_img2[j],
                #         color="blue"
                #     )

                #     fig = debug_axes[0].figure
                #     fig.suptitle(
                #         f"Match {match_count}: "
                #         f"triangle {i} vs triangle {j}"
                #     )

    # If there are no triangles found
    if match_count == 0:
        raise ValueError('No matching triangles found! Cannot continue!  --> Check images and try to increase N_STARS and/or TOL')

    # Prune empty over pre-allocated entries
    match_idx = match_idx[:match_count].astype(int)             
    
    # Extract the vertices
    p_triplets_xc = xc_sub_img1[triang_indices_img1[match_idx[:, 0]]]
    p_triplets_yc = yc_sub_img1[triang_indices_img1[match_idx[:, 0]]]  
        
    q_triplets_xc = xc_sub_img2[triang_indices_img2[match_idx[:, 1]]]
    q_triplets_yc = yc_sub_img2[triang_indices_img2[match_idx[:, 1]]] 
      
    # Convert to matrix for Kabsch: Each matrix holds in its ith column the p_i vector or q_i vector respectively 
    P_match = np.stack((p_triplets_xc.ravel(), p_triplets_yc.ravel()))
    Q_match = np.stack((q_triplets_xc.ravel(), q_triplets_yc.ravel())) 
    
    # For testing we use the whole subset of stars even if there can be stars which are present on one image but not the other
    P_all = np.stack((xc_sub_img1, yc_sub_img1))
    Q_all = np.stack((xc_sub_img2, yc_sub_img2))
        
    # =================================================================================================
    # FIND THE TRANSFORM TO BEST ALIGN THE IMAGES
    num_neighbours_best = 0
    CIRCLE_TOL_SQ = 25
    # Extract one matching triangle after the other
    for k in range(match_count):
        
        p_tri_k = P_match[:, k*3:(k+1)*3]
        q_tri_k = Q_match[:, k*3:(k+1)*3]
        
        # Compute rotation and translation that aligns the points in p with q as close as possible
        R_k, t_k = fit_kabsch(p_tri_k, q_tri_k)
        
        # Test the transform on all stars
        Q_pred_all = (R_k @ P_all + t_k)
        
        # RANSAC - find the number stars that lie within some radius of another star after transformation to grade the quality of the transform
        num_neighbours = 0
        match_idx_p = []
        match_idx_q = []
        
        for i in range(P_all.shape[1]):
        
            dist_sq = np.sum((Q_pred_all[:, i].reshape((2,1)) - Q_all)**2, axis=0)
            circle_logic = dist_sq < CIRCLE_TOL_SQ # if the squared distance between a point on image2 and the transformed point i from image 1 is smaller than the squared radius of the decision boundary we count it as neighbour

            if np.count_nonzero(circle_logic) == 1:
                num_neighbours += 1
                match_idx_p.append(i)
                match_idx_q.append(np.flatnonzero(circle_logic)[0])
                
            elif np.count_nonzero(circle_logic) > 1:
                print(f"POINT DISCARDED: Star {i} is to more than 1 star within boundary distance")

        # Check if the current transform outperforms the best one yet
        if num_neighbours > num_neighbours_best:
            num_neighbours_best = num_neighbours
            match_idx_p_best = match_idx_p
            match_idx_q_best = match_idx_q
            
    P_final = P_all[:, match_idx_p_best]
    Q_final = Q_all[:, match_idx_q_best]
       
    # Final transformation parameters are estimated using all unique pairs found from the best matched
    R, t = fit_kabsch(P_final, Q_final)
    Q_pred_final_0 = (R @ P_final)
        
    if debug_axes is not None:
        debug_axes[0].scatter(P_final[0, :], P_final[1, :], s=25, color="r", marker='+')
        debug_axes[0].scatter(Q_pred_final_0[0, :], Q_pred_final_0[1, :], s=25, color="m", marker='o')
        
        debug_axes[1].scatter(Q_final[0, :], Q_final[1, :], s=15, color="r", marker='+')
        debug_axes[1].scatter(Q_pred_final_0[0, :], Q_pred_final_0[1, :], s=15, color="m", marker='o')
    
                
    # Final transformation parameters are estimated using all unique pairs found from the best matched
    R, t = fit_kabsch(P_final, Q_final)
    Q_pred_final = (R @ P_final + t)
        
    if debug_axes is not None:
        debug_axes[0].scatter(P_final[0, :], P_final[1, :], s=25, color="r", marker='+')
        debug_axes[0].scatter(Q_pred_final[0, :], Q_pred_final[1, :], s=25, color="m", marker='o')
        
        debug_axes[1].scatter(Q_final[0, :], Q_final[1, :], s=15, color="r", marker='+')
        debug_axes[1].scatter(Q_pred_final[0, :], Q_pred_final[1, :], s=15, color="m", marker='o')
    
    # Q_pred = (R @ P_match + t)
    # if debug_axes is not None:
    #     debug_axes[0].scatter(P_match[0, :], P_match[1, :], s=40, color="r", marker='+')
    #     debug_axes[0].scatter(Q_pred[0, :], Q_pred[1, :], s=15, color="m", marker='o')
        
    #     debug_axes[1].scatter(Q_match[0, :], Q_match[1, :], s=40, color="r", marker='+')
    #     debug_axes[1].scatter(Q_pred[0, :], Q_pred[1, :], s=15, color="m", marker='o')    
    
    RMSE = np.sqrt(np.mean((Q_pred_final - Q_final)**2))
    rot_ang_deg = np.acos(R[0,0]) * 180/np.pi 
    print(rot_ang_deg)
    
    return R, t


# =================================================================================================
def get_triangle_sidelengths(xc_sub, yc_sub, N_STARS, K_NEIGH, TOL):

    # Pre-allocate 
    n_upperbound = int(math.factorial(N_STARS - 1)/(math.factorial(2)*math.factorial(N_STARS - 3)))
    triang_sidelen = np.zeros([n_upperbound, 3]) 
    triang_indices = np.zeros([n_upperbound, 3], dtype=int) 
    count = 0
    
    for i in range(N_STARS):
                
        # Compute distance to all other N stars 
        dist = np.sqrt((xc_sub - xc_sub[i])**2 + (yc_sub - yc_sub[i])**2)
        dist[i] = np.inf  # take the star particle out of possible detection range
    
        # Get indices to the k nearest neighbours 
        knn_idx = np.argpartition(dist, K_NEIGH)[:K_NEIGH]

        # The first point, point A (opposite to side BC), is the current star itself, computed outside once per outer iteration
        triang_vert_a_x = xc_sub[i] 
        triang_vert_a_y = yc_sub[i]
        
        # Accept a triangle with the index trick: A triangle has three different indices per vertex so by building a triangle only if the index is the smallest of the three. If in a later loop iteration the same three vertecies are selected they will have their values in a different variable (i,j,k) and the check for the smallest index will fail 
        for j in range(K_NEIGH):
            # Get the indices to the neighbours in the sub arrays
            idx_j = knn_idx[j]
            for k in range(j+1, K_NEIGH):
                idx_k = knn_idx[k]
                if i < idx_k and i < idx_j:    
                    # Second point, point B, opposite to side AC    
                    triang_vert_b_x = xc_sub[idx_j] # can be outside the inner most loop
                    triang_vert_b_y = yc_sub[idx_j]
                    # Third point, point C, opposite to side AB   
                    triang_vert_c_x = xc_sub[idx_k] 
                    triang_vert_c_y = yc_sub[idx_k]
                    
                    dist_A_bc = np.sqrt((triang_vert_c_x - triang_vert_b_x)**2 + (triang_vert_c_y - triang_vert_b_y)**2)
                    dist_B_ac = np.sqrt((triang_vert_c_x - triang_vert_a_x)**2 + (triang_vert_c_y - triang_vert_a_y)**2)
                    dist_C_ab = np.sqrt((triang_vert_b_x - triang_vert_a_x)**2 + (triang_vert_b_y - triang_vert_a_y)**2)
                    
                    # Discard triangles that have sidelengths that agree to tolerance because these could flip positions from image to image due to the centroid uncertanty
                    if np.abs(dist_A_bc - dist_B_ac) <= TOL or np.abs(dist_A_bc - dist_C_ab) <= TOL or np.abs(dist_B_ac - dist_C_ab) <= TOL: 
                        continue
                                    
                    triang_sidelen[count, :] = [dist_A_bc, dist_B_ac, dist_C_ab]
                    triang_indices[count, :] = [i,         idx_j,     idx_k]
                    count += 1

    # Prune empty over pre-allocated entries
    triang_sidelen = triang_sidelen[:count] 
    triang_indices = triang_indices[:count] 
    
    # Sort the lengths of each triangle for easy comparison with another table
    sort_idx = np.argsort(triang_sidelen, axis=1) # we need the indices since we have to order the indices to the vertices in the same order to match stars A,B,C from both images triangles
    triang_sidelen = np.take_along_axis(triang_sidelen, sort_idx, axis=1)
    triang_indices = np.take_along_axis(triang_indices, sort_idx, axis=1) 
    
    return triang_sidelen, triang_indices, count
    
