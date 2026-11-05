import time
import rawpy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from PIL import Image


# PATH = "C:\\Users\\basil\\Documents\\Astrophotographie\\EqMount\\TestData\\"

# filename = PATH + "_9264160.jpg"

# image = Image.open(filename)

# print(type(image))

# image_array = np.array(image)

# print(image_array.shape)

# img_red = image_array[:,:,0]

# print('Red max', img_red.max())
# print('Red max', img_red.min())

# img_gre = image_array[:,:,1]

# print('Green max', img_gre.max())
# print('Green min', img_gre.min())

# img_blu = image_array[:,:,2]

# print('Blue max', img_blu.max())
# print('Blue min', img_blu.min())

# print(img_red.shape)


# fig, ax = plt.subplots(1,3, figsize=(24, 8), sharex=True, sharey=True)

# ax[0].imshow(img_red, cmap='jet')
# ax[0].set_title('Red')
# ax[1].imshow(img_gre, cmap='jet')
# ax[1].set_title('Green')
# im = ax[2].imshow(img_blu, cmap='jet')
# ax[2].set_title('Blue')

# plt.colorbar(im, ax=ax, label="Intensity log2 scale")
# plt.tight_layout()
# plt.show()



import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

start_time = time.perf_counter()


a_x = 1
b_x = 3
c_x = 3

a_y = 1
b_y = 2
c_y = 5

x_vert = [a_x, b_x, c_x]
y_vert = [a_y, b_y, c_y]

lines = [
    [(x_vert[0], y_vert[0]), (x_vert[1], y_vert[1])],  # Line AB
    [(x_vert[0], y_vert[0]), (x_vert[2], y_vert[2])],  # Line AC
    [(x_vert[1], y_vert[1]), (x_vert[2], y_vert[2])],  # Line BC
]

end_time = time.perf_counter()

end_time - start_time

print('Time :', end_time - start_time)


fig, ax = plt.subplots()
lc = LineCollection(lines, colors='red', linewidths=2)
ax.add_collection(lc)

ax.scatter(x_vert, y_vert, color='black', zorder=3)
ax.autoscale()
plt.show()




