from PIL import Image
import imagehash
import os


def hamming2(s1, s2):
    """Calculate the Hamming distance between two bit strings"""
    assert len(s1) == len(s2)
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))


img_size = (750, 750)
folder_jaquette = "./Images/Images_jaquette/"
img_res = "./Images/Images_res/FFX.jpg"

hashes = []
for img in os.listdir(folder_jaquette):
    pil_img = Image.open(os.path.join(folder_jaquette, img))
    hashes.append(str(imagehash.whash(pil_img, hash_size=32)))


otherhash = imagehash.whash(Image.open(img_res), hash_size=32)


dist = list(map(lambda x: hamming2(x, str(otherhash)), hashes))

print(os.listdir(folder_jaquette))
print(dist)


min_val = min(dist)
index_min = dist.index(min_val)
print(os.listdir(folder_jaquette)[index_min])
