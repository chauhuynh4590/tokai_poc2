import torch
import os
import cv2
import clip
from config import Config
from utilities.general import Enum, _auto_enumerate, image_resize_size, SRC


class CheckStatus(Enum):
    FOUND = _auto_enumerate()
    CONFUSE = _auto_enumerate()
    NOT_FOUND = _auto_enumerate()
    NULL = _auto_enumerate()


class CheckObject:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load('ViT-B/16', self.device)
        self.img_vectors, self.txt_vectors, self.name_img = self.load_data()

    @staticmethod
    def load_data():
        tensor_imgs = torch.zeros(torch.Size([1, 512]))
        # tensor_txts = torch.zeros(torch.Size([1, 512]))
        tensor_txts = []
        name_img = []
        for filename in os.listdir(Config.IMG_VECTOR_PATH):
            if filename.endswith('.pt'):
                img_input = os.path.join(Config.IMG_VECTOR_PATH, filename)
                txt_input = os.path.join(Config.TXT_VECTOR_PATH, filename)
                loaded_img_pt = torch.load(img_input)
                loaded_txt_pt = torch.load(txt_input)
                tensor_imgs = torch.vstack((tensor_imgs, loaded_img_pt))
                # tensor_txts = torch.vstack((tensor_txts, loaded_txt_pt))
                tensor_txts += loaded_txt_pt

                name_img.append(filename.replace('.pt', '.png'))

        return tensor_imgs, tensor_txts, name_img

    def _image_to_vector(self, img):
        img = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            image_features = self.model.encode_image(img)

        image_features /= image_features.norm(dim=-1, keepdim=True)

        return image_features

    def _text_to_vector(self, txt):
        text = clip.tokenize([txt]).to(self.device)

        with torch.no_grad():
            text_features = self.model.encode_text(text)

        text_features /= text_features.norm(dim=-1, keepdim=True)

        return text_features

    def find_object(self, img):
        img_vector = self._image_to_vector(img)

        img_similarity = (100.0 * img_vector @ self.img_vectors.T)
        img_values, target_indices = img_similarity[0].topk(1)

        if target_indices == 0:  # no object in db
            # print(f"[{SRC.CLIP}] - Object not found")
            return None, CheckStatus.NOT_FOUND, ''

        txt_similarity = (100.0 * img_vector @ self.txt_vectors[target_indices - 1].T)
        txt_values, _ = txt_similarity[0].topk(1)

        img_conf, txt_conf, img_name = img_values.item(), txt_values.item(), self.name_img[target_indices - 1]

        # print(f"[{SRC.CLIP}] - Img conf: {img_conf}, TXT conf: {txt_conf}")

        status = CheckStatus.CONFUSE
        name_path = os.path.join(Config.IMG_OBJECT_PATH, img_name)

        if img_conf >= Config.IMG_THRESHOLD and txt_conf >= Config.TXT_THRESHOLD:
            status = CheckStatus.FOUND
        elif img_conf < Config.IMG_THRESHOLD and txt_conf < Config.TXT_THRESHOLD:
            status = CheckStatus.NOT_FOUND
            name_path = Config.NOT_FOUND_404

        img = cv2.imread(name_path)
        img_from_db = cv2.resize(img, image_resize_size(img.shape))

        return img_from_db, status, img_name

    def add_object(self, img, txt, filename="None"):
        img_file = os.path.join(Config.IMG_OBJECT_PATH, filename) + '.png'
        img_vec_file = os.path.join(Config.IMG_VECTOR_PATH, filename) + '.pt'
        txt_vec_file = os.path.join(Config.TXT_VECTOR_PATH, filename) + '.pt'
        img.save(img_file)
        img_vec, txt_vec = self._image_to_vector(img), self._text_to_vector(txt)
        torch.save(img_vec, img_vec_file)
        torch.save(txt_vec, txt_vec_file)
        self.img_vectors = torch.vstack((self.img_vectors, img_vec))
        self.txt_vectors += [txt_vec]
        self.name_img.append(filename + '.png')
        return filename


model_clip = CheckObject()
