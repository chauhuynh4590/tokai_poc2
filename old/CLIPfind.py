from torchvision import models
import clip
from PIL import Image
import torch
import pandas as pd
import os
import numpy as np
from torchvision import models

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def find(img_path,image_dir='C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/old/vectorPT'):
    print("new")
    with torch.no_grad():
        img = preprocess(Image.open(os.path.join(img_path))).unsqueeze(0).to(device)
        img_vector = model.encode_image(img)

    # img_vector = img_vector.view(img_vector.size(0), -1)
    # img_vector=img_vector.squeeze().to(torch.float64)
    img_vector /= img_vector.norm(dim=-1, keepdim=True)
    max=0
    name=''
    max2=0
    name2=''
    torch_data = torch.empty_like(img_vector)
    # Duyệt qua tất cả các ảnh trong thư mục
    for filename in os.listdir(image_dir):
        if filename.endswith('.pt'):
            input = os.path.join(image_dir, filename)
            # loaded_array = np.loadtxt(input)
            # tensor_data_loaded = torch.tensor(loaded_array)
            tensor_data_loaded = torch.load(input)
            torch_data= torch.vstack((torch_data,tensor_data_loaded))
            # cos_similarity = torch.dot(tensor_data_loaded, img_vector) / (torch.norm(tensor_data_loaded) * torch.norm(img_vector))
            # similarity = (100.0 * img_vector @ tensor_data_loaded.T)
            # conf=similarity.item()
            # print(conf)
            # if max < conf:
            #     max=conf
            #     name=filename
            # if conf <max and max2 <conf:
            #     # print(conf,max,max2)
            #     max2=conf
            #     name2=filename
        
    print(torch_data.shape)
    similarity = (100.0 * img_vector @ torch_data.T)
    values, indices = similarity[0].topk(2)
    name,name2 = values[0], values[1]
    max,max2 = indices[0], indices[1]
    return name, max, name2, max2


image_dir = 'C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images2'
ls=[]
# Duyệt qua tất cả các ảnh trong thư mục
for filename in os.listdir(image_dir):
    if filename.endswith('.png') or filename.endswith('.jpg'):
        input = os.path.join(image_dir, filename)
        name, max, name2, max2=find(input)
        ls.append([filename,name,max,name2,max2])

df = pd.DataFrame(ls,columns=['image_name', 'infer', 'conf','infer2', 'conf2'],index=None)
df.to_csv('out_infer_CLIP.csv')
