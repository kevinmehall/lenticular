import json
import os

import numpy as np

def translation(x, y):
    return np.array([
        [1, 0, x],
        [0, 1, y],
        [0, 0, 1]
    ])

def rotation(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([
        [c, -s, 0],
        [s,  c, 0],
        [0,  0, 1]
    ])

class Photo:
    def __init__(self, base, path, meta):
        self.base = base
        self.path = path
        self.polygon = meta.get('polygon')

    def fname(self):
        return os.path.join(self.base, self.path)

    def meta(self):
        return {
            'polygon': self.polygon
        }

    def transform_matrix(self):
        polygon = np.array(self.polygon)
        cx, cy = np.average(polygon, 0)

        a1 = np.arctan2(*(polygon[3]-polygon[0]))
        a2 = np.arctan2(*(polygon[2]-polygon[1]))
        a = (a1 + a2)/2

        return translation(1000, 1000) @ rotation(a) @ translation(-cx, -cy)

class Project:
    def __init__(self, base):
        self.base = base

        try:
            data = json.load(open(self.meta_path()))
        except OSError:
            data = {}

        jpeg_names = self.find_photos()
        photos = data.get('photos', {})
        self.photos = [Photo(self.base, path, photos.get(path, {})) for path in sorted(jpeg_names)]
        
    def find_photos(self):
        return [p for p in os.listdir(self.base)
            if os.path.splitext(p)[1].lower() in ('.jpg', '.jpeg')]


    def meta_path(self):
        return os.path.join(self.base, 'project.json')

    def save(self):
        json.dump({
            'photos': { p.path: p.meta() for p in self.photos }
        }, open(self.meta_path(), 'w'))