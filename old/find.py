from torchvision import transforms
from PIL import Image
import torch
import pandas as pd
import os
import numpy as np
from torchvision import models
model = models.resnet18(pretrained=True)

def find(img_path,image_dir='./vector'):
    img = Image.open(img_path)
    img_tensor = transform(img)
    img_tensor = img_tensor.unsqueeze(0)

    with torch.no_grad():
        img_vector = model(img_tensor)

    img_vector = img_vector.view(img_vector.size(0), -1)
    img_vector=img_vector.squeeze().to(torch.float64)
    max=0
    name=''
    name2=''
    max2=0
    # Duyệt qua tất cả các ảnh trong thư mục
    for filename in os.listdir(image_dir):
        if filename.endswith('.txt'):
            input = os.path.join(image_dir, filename)
            loaded_array = np.loadtxt(input)

            tensor_data_loaded = torch.tensor(loaded_array)

            cos_similarity = torch.dot(tensor_data_loaded, img_vector) / (torch.norm(tensor_data_loaded) * torch.norm(img_vector))
            conf=cos_similarity.item()
            if max < conf:
                max=conf
                name=filename
            if conf <max and max2 <conf:
                # print(conf,max,max2)
                max2=conf
                name2=filename
    return name, max, name2, max2


model.eval()
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


image_dir = './images2'
ls=[]
# Duyệt qua tất cả các ảnh trong thư mục
for filename in os.listdir(image_dir):
    if filename.endswith('.png') or filename.endswith('.jpg'):
        input = os.path.join(image_dir, filename)
        name, max, name2, max2=find(input)
        ls.append([filename,name,max, name2, max2])

df = pd.DataFrame(ls,columns=['image_name', 'infer', 'conf','infer2', 'conf2'],index=None)
df.to_csv('out_infer_no.csv')
