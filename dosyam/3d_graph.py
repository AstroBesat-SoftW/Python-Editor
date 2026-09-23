import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Veri oluşturma
x = np.linspace(-5, 5, 100)
y = np.linspace(-5, 5, 100)
x, y = np.meshgrid(x, y)
z = np.sin(np.sqrt(x**2 + y**2)) * np.cos(np.sqrt(x**2 + y**2))

# Grafik oluşturma
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(x, y, z, cmap='viridis')

# Başlık ve etiketler
ax.set_title('3D Karmaşık Grafik')
ax.set_xlabel('X Ekseni')
ax.set_ylabel('Y Ekseni')
ax.set_zlabel('Z Ekseni')

# Grafiği göster
plt.show()