import torch
import os
import cv2
import clip
from config import Config


class CheckObject:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load('ViT-B/32', self.device)

        self.img_path = Config.OBJECT_IMAGE_LAKE
        self.vector_path = Config.PT_VECTOR_LAKE
        self.error_img = Config.NOT_FOUND_404
        self.data, self.name_img = self.load_data()

    def load_data(self):
        # print("Load DataBase")
        path_txt = self.vector_path
        tensor_all = torch.zeros(torch.Size([1, 512]))
        name_img = ['0']
        for filename in os.listdir(path_txt):
            if filename.endswith('.pt'):
                input = os.path.join(path_txt, filename)
                loaded_pt = torch.load(input)
                tensor_all = torch.vstack((tensor_all, loaded_pt))

                name_img.append(filename.replace('.pt', '.png'))

        return tensor_all, name_img

    def img_to_vector(self, img):
        img = img.resize((2000, 2000))
        img = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self.model.encode_image(img)

        features /= features.norm(dim=-1, keepdim=True)
        return features

    def find_object(self, img):
        img_vector = self.img_to_vector(img)

        # similarity = (100.0 * img_vector @ self.data.T).softmax(dim=-1)
        similarity = (100.0 * img_vector @ self.data.T)
        values, indices = similarity[0].topk(1)

        conf, nameimg = values.item(), self.name_img[indices]

        name_path = os.path.join(self.img_path, nameimg)
        if conf < 50:
            name_path = self.error_img
        conf = float("{:.2f}".format(conf))

        f = cv2.imread(name_path)

        return f, conf, nameimg

    def add_object(self, img, filename="None"):
        img_file = os.path.join(self.img_path, filename) + '.png'
        vec_file = os.path.join(self.vector_path, filename) + '.pt'
        img.save(img_file)
        vector = self.img_to_vector(img)
        torch.save(vector, vec_file)
        self.data = torch.vstack((self.data, vector))
        self.name_img.append(filename + '.png')
        return filename


model_clip = CheckObject()
