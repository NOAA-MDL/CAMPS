import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import random



def display(grid):
    plt.imshow(grid,origin='lower', cmap=cm.gist_rainbow)
    plt.savefig('img'+str(random.randint(1,30))+'.png')
    plt.show()


def test():
    mmk = np.random.rand(400,400)
    display(mmk)

