from torchvision import transforms
from PIL import Image
import torch
import pandas as pd
import os
import numpy as np
from torchvision import models
import cv2
import time


class Check_Object:
    def __init__(self):
        self.model = models.resnet18(pretrained=True).eval()
        self.transform = transforms.Compose([
                        transforms.Resize(256),
                        transforms.CenterCrop(224),
                        transforms.ToTensor(),
                        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                        ])
        self.img_path="C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images1"
        self.vector_path="C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/vector"
        self.error_img = "C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/404.png"
        self.data=self.load_data()

    def load_data(self):
        path_txt = self.vector_path
        data=[]
        for filename in os.listdir(path_txt):
            if filename.endswith('.txt'):
                input = os.path.join(path_txt, filename)
                loaded_array = np.loadtxt(input)
                data.append([input.replace(".txt","").replace("vector","images1"),loaded_array,filename])
        
        return data

    def img_to_vector(self,img):
        img = Image.fromarray(img)
        img_tensor = self.transform(img)
        img_tensor = img_tensor.unsqueeze(0)

        with torch.no_grad():
            img_vector = self.model(img_tensor)

        img_vector = img_vector.view(img_vector.size(0), -1)
        return img_vector,img_vector.squeeze().to(torch.float64)

    def find_object(self,img):
        _,img_vector = self.img_to_vector(img)
        max=0
        name=''
        for i in self.data:
            tensor_data_loaded = torch.tensor(i[1])
            cos_similarity = torch.dot(tensor_data_loaded, img_vector) / (torch.norm(tensor_data_loaded) * torch.norm(img_vector))
            conf=cos_similarity.item()
            if max < conf:
                max=conf
                name=i[0]
        if max < 0.80 :
            name = self.error_img
        max = float("{:.2f}".format(max*100))
        
        print(name)
        return cv2.imread(name) , max, name.split("/")[-1]

    def add_object(self,img):
        current_time = time.time()
        time_string = time.strftime("y%Y_m%m_d%d_h%H_m%M_s%S", time.localtime(current_time))
        path= os.path.join(self.img_path, time_string)+'.png'
        cv2.imwrite(path,img)
        vector,vector_np= self.img_to_vector(img)
        np.savetxt(os.path.join(self.vector_path,time_string)+'.png.txt',vector.numpy())
        self.data.append([path,vector_np,time_string+'png'])
        return time_string+'.png'




# a=Check_Object()

# img = cv2.imread("C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images2/12b.png")
# im , conf = a.find_object(img)
# print(conf)

# im.show()