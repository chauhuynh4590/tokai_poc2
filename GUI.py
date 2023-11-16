import os
import traceback
import cv2


os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from utilities.check_object_CLIP import Check_Object
from utilities.dataset import CVFreshestFrame
from utilities.popup_windows import ConfidencePopup, center, MessageBox
from tkinter import Tk, Button, Label, Menu, messagebox, ttk
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Notebook

from PIL import ImageTk, Image


def get_data_askfile(title: str):
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    dirPath = str(askopenfilename(title=title)).strip()
    if not len(dirPath):
        return None
    return dirPath


class App:
    def __init__(self, window):
        self.window = window
        self.window.maxsize(1920, 1080)
        # self.window.resizable(0, 0)
        self.window.title("Encoding IMG")
        # self.window.iconbitmap(Config.APP_ICON)
        self.window.bind("<Control-o>", self.open_video)

        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)

        self.defaultBackground = window.cget("background")

        self.link = ""

        self.runUpdate = False
        self.videoCapture = None

        self.currentHeight = 504
        self.currentWidth = 896
        self.image = None
        # is in error box
        
        self.model_check = Check_Object()

        self.create_tool_bar()

        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Consolas", "14", "bold"), padding=[10, 5])

        self.tab_control = Notebook(self.window)
        self.tab_control.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.create_tab_control()

        center(self.window)
        self.window.protocol("WM_DELETE_WINDOW", self.quit)
        self.window.mainloop()

    def quit(self):
        try:
            self.runUpdate = False
            if self.videoCapture:
                self.videoCapture.release()
                cv2.destroyAllWindows()

            self.window.destroy()
            self.window.quit()

        except:
            traceback.print_exc()

    def create_tool_bar(self):
        menu_bar = Menu(self.window)
        self.window.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open Video", command=self.open_video)
        file_menu.add_command(label="Version",
                              command=lambda: MessageBox(self.window, f"TokaiRika Version {0}"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

    def create_tab_control(self):
        self.tab_video = ttk.Frame(self.tab_control)
        self.tab_video.bind("<Configure>", self._resize_image)

        self.tab_video.rowconfigure(0, weight=1)
        self.tab_video.columnconfigure(0, weight=1)

        self.hypl_connect = Button(self.tab_video, text="Open Video", fg="blue", cursor="hand2", font=("Consolas", 32),
                                   bd=0, highlightthickness=0, width=39, height=10,
                                   command=self.open_video)
        self.hypl_connect.grid(row=0, column=0, sticky="nsew")

        # ------------------------- Result--
        self.tab_ocr = ttk.Frame(self.tab_control)
        self.tab_ocr.grid_columnconfigure((0, 1), weight=1)

        label_img_text = Label(self.tab_ocr,borderwidth=1, text="Input Images", font=("Consolas", 12))
        label_img_text.grid(row=0, column=0)

        label_img_text2 = Label(self.tab_ocr,borderwidth=1, text="DataBase", font=("Consolas", 12))
        label_img_text2.grid(row=0, column=1)

        self.ocr_1_img = Label(self.tab_ocr, borderwidth=1, relief="solid", height=20)
        self.ocr_1_img.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.ocr_2_img = Label(self.tab_ocr, borderwidth=1, relief="solid", height=20)
        self.ocr_2_img.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.label_img_text_db = Label(self.tab_ocr, borderwidth=1, font=("Consolas", 12))
        self.label_img_text_db.grid(row=2, column=1)

        self.label_img_text_add = Label(self.tab_ocr, borderwidth=1, font=("Consolas", 12))
        self.label_img_text_add.grid(row=2, column=0,sticky="ne")


        self.tab_control.add(self.tab_video, text="Video")
        self.tab_control.add(self.tab_ocr, text="Result")

    def _resize_image(self, event):
        new_width = event.width
        new_height = event.height
        cal_height = int(((new_width * 9 / 16 + 32) // 32) * 32)
        cal_width = int(((new_height * 16 / 9 + 32) // 32) * 32)
        if 360 <= cal_height <= new_height:
            self.currentWidth = new_width - 25  # padding
            self.currentHeight = cal_height - 25  # padding
        elif 640 <= cal_width <= new_width:
            self.currentWidth = cal_width - 25  # padding
            self.currentHeight = new_height - 25  # padding

    def _pause_detection(self):
        self.runUpdate = False  # turn off video detection
        self.reset_display()

    def _unpause_detection(self):
        if self.link != "":  # video or rtsp
            self.runUpdate = True
            self.open_vid_source(self.link)
        else:
            self.reset_display()

    def popup_set_conf(self):
        self._pause_detection()
        self.w = ConfidencePopup(self.window)
        try:
            if self.conf == self.w.conf:
                # print(f"[{SRC.GUI}] - CONF NO CHANGE")
                pass
            else:
                # print(f"[{SRC.GUI}] - NEW CONF", self.conf)
                ver = self.w.conf[0]
                # print(f"[{SRC.GUI}] - Version check: old = {self.conf[0]} and new = {ver}")
                if self.conf[0] != ver:
                    # model.reload_yolo_model(ver)
                    pass
                self.conf = self.w.conf

            self._unpause_detection()

        except AttributeError:
            traceback.print_exc()
            # print(f"[{SRC.GUI}] - Set confidences: CANCEL")
            return

    def reset_display(self):
        try:
            # destroy current display
            self.check_img.grid_forget()
            # self.check_img.destroy()
            self.hypl_connect.destroy()
            self.displayImage.destroy()
            self.ocr_1_img.configure(image='')
            self.ocr_2_img.configure(image='')
            self.link = ""
        except AttributeError:  # no displayImage
            # traceback.print_exc()
            pass

        # add link: Please connect to camera
        self.hypl_connect = Button(self.tab_video, text="Open Video", fg="blue", cursor="hand2",
                                   font=("Consolas", 32), bd=0, highlightthickness=0, width=39, height=10,
                                   command=self.open_video)
        self.hypl_connect.grid(row=0, column=0, sticky="nsew")

        

    # ==================================================================================================================
    # ----------------------------------------- RUN process ------------------------------------------------------------
    # ==================================================================================================================
    def check_object(self):
        self.img_check=self.image
        img = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img,(400,400))
        photo = ImageTk.PhotoImage(image=Image.fromarray(img))
        self.ocr_1_img.configure(image=photo,height=400)
        self.ocr_1_img.image = photo

        img2, conf, name2 = self.model_check.find_object(self.image)

        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)
        img2 = cv2.resize(img2,(400,400))
        photo2 = ImageTk.PhotoImage(image=Image.fromarray(img2))
        self.ocr_2_img.configure(image=photo2)
        self.ocr_2_img.image = photo2

        self.add_img = Button(self.tab_ocr, text="Add Object",bg ="blue" , fg="red", cursor="hand2", font=("Consolas", 14),
                                   bd=5, highlightthickness=5, width=10, height=1,
                                   command=self.add_object)
        self.add_img.grid(row=2, column=0,sticky="w" )

        self.label_img_text_add.configure(text='')
        self.label_img_text_db.configure(text='')
        if conf >80:
            self.label_img_text_db = Label(self.tab_ocr, borderwidth=1, text=f'img: {name2},\n conf: {conf} %', font=("Consolas", 12))
            self.label_img_text_db.grid(row=2, column=1)
        else:
            self.label_img_text_db = Label(self.tab_ocr, borderwidth=1, text=f'Image does not exist', font=("Consolas", 12))
            self.label_img_text_db.grid(row=2, column=1)
    

    def add_object(self):
        name = self.model_check.add_object(self.img_check)
        self.label_img_text_add = Label(self.tab_ocr, borderwidth=1, text=f'Add Imgae : \n{name}', font=("Consolas", 12))
        self.label_img_text_add.grid(row=2, column=0,sticky="ne")
        img2 = cv2.cvtColor(self.img_check, cv2.COLOR_BGR2RGB)
        img2 = cv2.resize(img2,(400,400))
        photo2 = ImageTk.PhotoImage(image=Image.fromarray(img2))
        self.ocr_2_img.configure(image=photo2)
        self.ocr_2_img.image = photo2
        messagebox.showinfo("Info", "New object added!")

    def open_video(self, event=None):
        self._pause_detection()
        video_file = get_data_askfile("Open Video file")
        # if self.quit()
        if video_file is None:
            self._unpause_detection()
            return
        # unsupported video format
        if not video_file.lower().endswith((".mp4", ".mkv", ".flv", ".wmv", ".mov", ".avi", ".webm")):
            messagebox.showinfo("Info", "Unsupported video format.")
            return
        self.link = str(video_file)

        self.open_vid_source(video_file)
        

    def open_vid_source(self, source):
        try:
            if self.videoCapture:
                self.videoCapture.release()
                self.check_img.grid_forget()
                # cv2.destroyAllWindows()

            self.cnt = 0
            if not os.path.isfile(source):
                messagebox.showerror("Error", f"Source '{source}' is not found!")
                return
            else:
                capf = cv2.VideoCapture(source)
                fps = capf.get(cv2.CAP_PROP_FPS)
                capf.release()
                self.videoCapture = CVFreshestFrame(source, fps)
                # print(f"[{SRC.GUI}] - Open video: {source}")

            self.in_running()
        except:
            traceback.print_exc()
            raise Exception("Exception occurred in open_vid_source")

    def in_running(self):
        self.runUpdate = True

        try:
            self.hypl_connect.destroy()
            self.displayImage.destroy()
        except AttributeError:  # no displayImage
            # traceback.print_exc()
            pass

        self.displayImage = Label(self.tab_video)
        self.displayImage.grid(row=0, column=0, sticky="nsew")
        self.displayImage.bind("<Configure>", self._resize_image)

        self.check_img = Button(self.tab_video, text="Check",bg ="blue" , fg="red", cursor="hand2", font=("Consolas", 14),
                                   bd=0, highlightthickness=0, width=6, height=2,
                                   command=self.check_object)
        self.check_img.grid(row=1, column=1, sticky="se")
        self.update_detection()

    def update_detection(self):
        try:
            if self.runUpdate:

                cnt, img0 = self.videoCapture.read()

                if not cnt:
                    # print(f"[{SRC.GUI}] - [INFO] - Video is over.")
                    self.runUpdate = False
                    
                    messagebox.showinfo("Info", "Video is over!")
                    self.videoCapture.release()
                    self.reset_display()
                    self.check_img.grid_forget()
                    return

                if not (img0 is None or img0.size == 0):
                    if img0.shape[0] != self.currentWidth:
                        img0 = cv2.resize(img0, (self.currentWidth, self.currentHeight))
                    self.image = img0
                    imgrz = cv2.cvtColor(img0, cv2.COLOR_BGR2RGB)
                    self.photo = ImageTk.PhotoImage(image=Image.fromarray(imgrz))

                    if self.displayImage:
                        self.displayImage.configure(image=self.photo, background=self.defaultBackground, text="")

                self.window.after(10, self.update_detection)
        except:
            traceback.print_exc()
            self.runUpdate = False
            self.quit()
            return


def main():
    # Create a window and pass it to the Application object
    App(Tk())


if __name__ == "__main__":
    main()
