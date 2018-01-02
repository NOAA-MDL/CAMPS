import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import random



def display(grid, filename=None, axis=True):
    img = plt.imshow(grid,origin='lower', cmap=cm.gist_rainbow, vmin=0, vmax=1)
    img.set_cmap('tab20b')
    if not axis:
        plt.axis('off')
    if filename is None:
        plt.savefig('img'+str(random.randint(1,30))+'.png')
    else:
        plt.savefig(filename + '.png', bbox_inches='tight')
    plt.show()


def test():
    mmk = np.random.rand(400,400)
    display(mmk)

