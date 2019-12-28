import sys
import os
from project import Project, Photo
from PIL import Image
import numpy as np

def process(project):
    out = os.path.join(project.base, 'out')
    os.makedirs(out, exist_ok=True)

    for i, photo in enumerate(project.photos):
        print(f"{i+1:2d}/{len(project.photos):2d}: {photo.path}")
        image = Image.open(photo.fname())
        inv = np.linalg.inv(photo.transform_matrix())
        transformed = image.transform((2000, 2000), Image.AFFINE, data=inv.flatten()[:6], resample=Image.CUBIC)
        out_path = os.path.join(out, f"{i}.jpg")
        transformed.save(out_path)

if __name__ == "__main__":
    process(Project(sys.argv[1]))