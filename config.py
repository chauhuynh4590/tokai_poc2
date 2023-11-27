import os
import traceback
from configparser import RawConfigParser, NoSectionError
from pathlib import Path
from typing import get_type_hints, Union


class AppConfigError(Exception):
    pass


def _parse_bool(val: Union[str, bool]) -> bool:  # pylint: disable=E1136
    return val if type(val) == bool else val.lower() in ["true", "yes", "1"]


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # base_path = sys._MEIPASS
        base_path = os.path.abspath(".")
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


ROOT = Path(os.path.dirname(os.path.abspath(__file__)))


# Ensure methods to raise an AppConfigError Exception
# when something was wrong
def safe_cfg_func(func):
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            # print('Ouuups: err =', err, ', func =', func, ', args =', args, ', kwargs =', kwargs)
            raise AppConfigError(err)

    return wrapped


class AppConfig:
    APP_VERSION: str = "1.5"
    ENV: str = "production"
    APP_TITLE: str = "TOKAIRIKA DEMO"  # Name of Application
    APP_ICON: str = ROOT / "data/app_icon.ico"  # Icon for Application
    OCR_CHAR_FONT: str = ROOT / r"data/latin.ttf"
    ICON_ASK: str = ROOT / r"data/ask.png"
    ICON_INFO: str = ROOT / r"data/info.png"
    NO_BARCODE: str = ROOT / r"data/no_barcode.jpg"
    NO_TAGNAME: str = ROOT / r"data/no_tagname.jpg"
    LOADING_GIF: str = ROOT / r"data/loading.gif"
    CHECKAREA_DATA: str = ROOT / r"data/CHECKAREA"

    FRAME_WIDTH = 1280
    FRAME_HEIGHT = int(((FRAME_WIDTH * 9 / 16 + 32) // 32) * 32)

    # check area
    PAD_LEFT: int = 30  # pad PAD_LEFT -> % of width
    PAD_RIGHT: int = 2  # pad PAD_RIGHT -> % of width

    # openvino device
    DEVICE: str = "CPU"

    # openvino models
    PDOCR_DET_MODEL: str = ROOT / "model/en_PP-OCRv3_det_infer/inference.pdmodel"
    PDOCR_REC_MODEL: str = ROOT / "model/en_PP-OCRv3_rec_infer/inference.pdmodel"
    REID_MODEL: str = ROOT / "model/person-reidentification-retail-0287/person-reidentification-retail-0287.xml"

    # CLIP
    IMG_VECTOR_PATH: str = ROOT / "data/CLIP/vector_images/"
    TXT_VECTOR_PATH: str = ROOT / "data/CLIP/vector_texts/"
    NOT_FOUND_404: str = ROOT / "data/404.png"
    IMG_OBJECT_PATH: str = ROOT / "data/CLIP/images/"
    IMG_THRESHOLD: float = 84.0
    TXT_THRESHOLD: float = 26.5

    APP_CNF_FILE: str = ROOT / "config.cfg"
    """
    Map environment variables to class fields according to these rules:
      - Field won't be parsed unless it has a type annotation
      - Field will be skipped if not in all caps
      - Class field and environment variable name are the same
    """

    def __init__(self, env):
        for field in self.__annotations__:
            if not field.isupper():
                continue
            # Raise AppConfigError if required field not supplied
            default_value = getattr(self, field, None)
            if default_value is None and env.get(field) is None:
                raise AppConfigError("The {} field is required".format(field))

            # Cast env var value to expected type and raise AppConfigError on failure
            try:
                var_type = get_type_hints(AppConfig)[field]
                if var_type == bool:
                    value = _parse_bool(env.get(field, default_value))
                else:
                    value = var_type(env.get(field, default_value))

                self.__setattr__(field, value)
            except ValueError:
                raise AppConfigError("Unable to cast value of '{}' to type '{}' for '{}' field".format(
                    env[field],
                    var_type,
                    field
                )
                )

    def __repr__(self):
        return str(self.__dict__)


# Expose Config object for app to import
Config = AppConfig(os.environ)
"""
It's fine if a guy is named Guy but weird if a girl is named Girl.
What do you call a blind deer? No eyes deer!
"""
