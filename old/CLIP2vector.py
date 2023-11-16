from torchvision import models
import clip
from PIL import Image

from PIL import Image
import torch
import pandas as pd
import os
import numpy as np

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

image_dir = 'C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images1'

for filename in os.listdir(image_dir):
    if filename.endswith('.png'):
        with torch.no_grad():
            img = preprocess(Image.open(os.path.join(image_dir, filename))).unsqueeze(0).to(device)
            img_vector = model.encode_image(img)
            img_vector /= img_vector.norm(dim=-1, keepdim=True)
            # img_vector = img_vector.view(img_vector.size(0), -1)
            print(img_vector.shape,img_vector)
            torch.save(img_vector,'C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/old/vectorPT/'+filename+'.pt')
            # np.savetxt('C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/old/vectorCLIP/'+filename+'.txt',img_vector.numpy())

