"""Render actual released STL facets; optional matplotlib dependency."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parents[1]


def triangles(path):
    return np.frombuffer(path.read_bytes(), dtype=[('n', '<f4', 3),
        ('p', '<f4', (3, 3)), ('a', '<u2')], offset=84)['p'].astype(float)


def main():
    fig = plt.figure(figsize=(12, 7.2), facecolor='#f3f5f7')
    for column, size in enumerate(['45', '55.5', '95']):
        for row, side in enumerate(['gear-side-2.2mm-flange', 'cap-side-0.6mm-lip']):
            folder = ROOT/'models' if size == '55.5' else ROOT/'stock-sizes/models'
            points = triangles(folder/f'kraken-spool-ring-{size}-mm-pentagon-{side}.stl')
            normal = np.cross(points[:, 1]-points[:, 0], points[:, 2]-points[:, 0])
            normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-15)
            light = np.array([-.3, -.4, 1.]); light /= np.linalg.norm(light)
            shade = .45 + .55*np.maximum(0, normal@light)
            shade = np.round(shade*5)/5
            color = np.array([.96, .52, .13]) if row == 0 else np.array([.18, .58, .84])
            colors = np.clip(shade[:, None]*color, 0, 1)
            ax = fig.add_subplot(2, 3, row*3+column+1, projection='3d', facecolor='#f3f5f7')
            ax.add_collection3d(Poly3DCollection(points, facecolors=colors, edgecolors='none', linewidths=0, antialiaseds=False))
            ax.set(xlim=(-60,60), ylim=(-60,60), zlim=(0,30))
            ax.set_box_aspect((120,120,30)); ax.view_init(elev=90, azim=-90)
            ax.set_axis_off()
            ax.set_title(f'{size} mm — {"gear side" if row == 0 else "cap side"}', fontsize=12, pad=-5)
    fig.suptitle('Pentagon flange pairs: same holder fit across sizes', fontsize=17, y=.98)
    fig.text(.5,.035,'Top views of actual meshes • same scale in every panel • geometry checks do not certify physical fit',ha='center',fontsize=10,color='#425062')
    fig.subplots_adjust(left=.01,right=.99,bottom=.06,top=.9,wspace=.0,hspace=.0)
    out=ROOT/'stock-sizes/images';out.mkdir(exist_ok=True)
    fig.savefig(out/'family.png', dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == '__main__':
    main()
