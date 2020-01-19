import sys
import os
from project import Project, Photo
from PIL import Image
import numpy as np

def process(project):
    out = os.path.join(project.base, 'out')
    os.makedirs(out, exist_ok=True)

    for i, photo in enumerate(project.photos):
        print("{:2d}/{:2d}: {}".format(i+1, len(project.photos), photo.path))
        image = Image.open(photo.fname())
        inv = np.linalg.inv(photo.transform_matrix())
        transformed = image.transform(project.crop_size(), Image.AFFINE, data=inv.flatten()[:6], resample=Image.CUBIC)
        transformed.thumbnail(project.out_size(), resample=Image.BICUBIC)
        out_path = os.path.join(out, "{}.jpg".format(i))
        transformed.save(out_path)

if __name__ == "__main__":
    process(Project(sys.argv[1]))