from torchvision import transforms
from PIL import Image
import torch
import pandas as pd
import os
import numpy as np
from torchvision import models
import cv2


class Check_Object:
    def __init__(self):
        self.model = models.resnet18(pretrained=True).eval()
        self.transform = transforms.Compose([
                        transforms.Resize(256),
                        transforms.CenterCrop(224),
                        transforms.ToTensor(),
                        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                        ])
        self.data=self.load_data()

    def load_data(self,path_txt='C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/vector'):
        data=[]
        for filename in os.listdir(path_txt):
            if filename.endswith('.txt'):
                input = os.path.join(path_txt, filename)
                loaded_array = np.loadtxt(input)
                data.append([input.replace(".txt","").replace("vector","images1"),loaded_array,filename])
        
        return data


    def find_object(self,img):
        img = Image.fromarray(img)
        img_tensor = self.transform(img)
        img_tensor = img_tensor.unsqueeze(0)

        with torch.no_grad():
            img_vector = self.model(img_tensor)

        img_vector = img_vector.view(img_vector.size(0), -1)
        img_vector=img_vector.squeeze().to(torch.float64)
        max=0
        name=''
        for i in self.data:
            tensor_data_loaded = torch.tensor(i[1])
            cos_similarity = torch.dot(tensor_data_loaded, img_vector) / (torch.norm(tensor_data_loaded) * torch.norm(img_vector))
            conf=cos_similarity.item()
            if max < conf:
                max=conf
                name=i[0]
        max = "{:.2f}".format(max*100)
        return cv2.imread(name) , max, name.split("/")[-1]


# a=Check_Object()

# img = cv2.imread("C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images2/12b.png")
# im , conf = a.find_object(img)
# print(conf)

# im.show()