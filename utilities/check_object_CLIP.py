from torchvision import transforms
from PIL import Image
import torch
import pandas as pd
import os
import numpy as np
from torchvision import models
import cv2
import time
import clip 


class Check_Object:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load('ViT-B/32',self.device )

        self.img_path="C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images1"
        self.vector_path="C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/old/vectorPT"
        self.error_img = "C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/404.png"
        self.data, self.name_img =self.load_data()

    def load_data(self):
        path_txt = self.vector_path
        tensor_all = torch.zeros(torch.Size([1, 512]))
        name_img=["0"]
        for filename in os.listdir(path_txt):
            if filename.endswith('.pt'):
                input = os.path.join(path_txt, filename)
                loaded_pt = torch.load(input)
                tensor_all = torch.vstack((tensor_all,loaded_pt))
                name_img.append(filename.replace('.pt','.png'))
        return tensor_all, name_img

    def img_to_vector(self,img):
        img = Image.fromarray(img)
        img = img.resize((500,500))
        img = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self.model.encode_image(img)
            features /= features.norm(dim=-1, keepdim=True)

        return features

    def find_object(self,img):
        img_vector = self.img_to_vector(img)
        
        similarity = (100.0 * img_vector @ self.data.T).softmax(dim=-1)
        values, indices = similarity[0].topk(1)

        conf, nameimg  = values.item(),self.name_img[indices]

        name_path = os.path.join(self.img_path,nameimg)
        if conf < 0.80 :
            name_path = self.error_img
        conf = float("{:.2f}".format(conf*100))
        
        print(conf, nameimg)
        return cv2.imread(name_path) , conf, nameimg

    def add_object(self,img):
        current_time = time.time()
        time_string = time.strftime("y%Y_m%m_d%d_h%H_m%M_s%S", time.localtime(current_time))

        path= os.path.join(self.img_path, time_string)+'.png'
        cv2.imwrite(path,img)
        vector= self.img_to_vector(img)
        torch.save(vector,(os.path.join(self.vector_path,time_string)+'.pt'))
        self.data =  torch.vstack((self.data,vector))
        self.name_img.append(time_string+'.png')
        return time_string+'.png'




# a=Check_Object()

# img = cv2.imread("C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images2/12b.png")
# x,y,z= a.find_object(img)

# print(y,z)

# cv2.imshow("im",x)