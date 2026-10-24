import glob
from PIL import Image

print("--- Inspecting Images ---")
for p in glob.glob('dataset/evidence/images/*.png'):
    im = Image.open(p)
    print(f"Image: {p} | Size: {im.size} | Mode: {im.mode} | Info: {list(im.info.keys())}")
    for k, v in im.info.items():
        if isinstance(v, str) and len(v) < 200:
            print(f"  {k}: {v}")
