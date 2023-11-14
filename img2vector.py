from torchvision import models

model = models.resnet18(pretrained=True)

from torchvision import transforms
from PIL import Image
import torch
import pandas as pd
import os
import numpy as np

model.eval()
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

image_dir = './images1'

for filename in os.listdir(image_dir):
    if filename.endswith('.png'):

        print(filename)
        img = Image.open(os.path.join(image_dir, filename))

        img_tensor = transform(img)

        img_tensor = img_tensor.unsqueeze(0)

        with torch.no_grad():
            img_vector = model(img_tensor)

        img_vector = img_vector.view(img_vector.size(0), -1)

        np.savetxt('./vector/'+filename+'.txt',img_vector.numpy())

