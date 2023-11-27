import os
from typing import List

import numpy as np
import onnxruntime as ort

from PIL import Image
from PIL.Image import Image as PILImage

from typing import Type
from rembg import remove
from rembg.sessions import sessions_class, BaseSession
from config import Config


class U2netLocalSession(BaseSession):
    def __init__(self,
                 model_name: str,
                 sess_opts: ort.SessionOptions,
                 providers=None,
                 *args,
                 **kwargs
                 ):
        model_path = Config.REMBG_MODEL
        # print(f"Model path: {model_path}")

        if model_path is None:
            raise ValueError("model_path is required")

        super().__init__(model_name, sess_opts, providers, *args, **kwargs)

    def predict(self, img: PILImage, *args, **kwargs) -> List[PILImage]:
        ort_outs = self.inner_session.run(
            None,
            self.normalize(
                img, (0.485, 0.456, 0.406), (0.229, 0.224, 0.225), (320, 320)
            ),
        )

        pred = ort_outs[0][:, 0, :, :]

        ma = np.max(pred)
        mi = np.min(pred)

        pred = (pred - mi) / (ma - mi)
        pred = np.squeeze(pred)

        mask = Image.fromarray((pred * 255).astype("uint8"), mode="L")
        mask = mask.resize(img.size, Image.LANCZOS)

        return [mask]

    @classmethod
    def download_models(cls, *args, **kwargs):
        model_path = Config.REMBG_MODEL
        if model_path is None:
            return

        return os.path.abspath(os.path.expanduser(model_path))

    @classmethod
    def name(cls, *args, **kwargs):
        return "u2net_local"


def new_session(
        model_name: str = "u2net_local", providers=None, *args, **kwargs
) -> BaseSession:
    """
    Create a new session object based on the specified model name.

    This function searches for the session class based on the model name in the 'sessions_class' list.
    It then creates an instance of the session class with the provided arguments.
    The 'sess_opts' object is created using the 'ort.SessionOptions()' constructor.
    If the 'OMP_NUM_THREADS' environment variable is set, the 'inter_op_num_threads' option of 'sess_opts' is set to its value.

    Parameters:
        model_name (str): The name of the model.
        providers: The providers for the session.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.

    Returns:
        BaseSession: The created session object.
    """
    session_class: Type[BaseSession] = U2netLocalSession

    for sc in sessions_class:
        if sc.name() == model_name:
            session_class = sc
            break

    sess_opts = ort.SessionOptions()

    if "OMP_NUM_THREADS" in os.environ:
        sess_opts.inter_op_num_threads = int(os.environ["OMP_NUM_THREADS"])
        sess_opts.intra_op_num_threads = int(os.environ["OMP_NUM_THREADS"])

    return session_class(model_name, sess_opts, providers, *args, **kwargs)


session = new_session("u2net_local")


def remove_bg(input_image):
    res = remove(input_image, session=session, bgcolor=(192, 192, 192, 0))
    return res
