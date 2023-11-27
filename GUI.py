import faulthandler
import os
import traceback
import cv2

from config import Config

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from utilities.dataset import CVFreshestFrame
from utilities.popup_windows import center, MessageBox, LoadingBox
from utilities.general import SRC, image_resize_size, load_ca
from tkinter import Tk, Button, Label, Menu, messagebox, ttk
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Notebook
from PIL import ImageTk, Image

faulthandler.enable()


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
        self.window.minsize(720, 405)
        # self.window.resizable(0, 0)
        self.window.title(Config.APP_TITLE)
        self.window.iconbitmap(Config.APP_ICON)
        self.window.bind("<Control-o>", self.open_video)

        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)

        self.defaultBackground = window.cget("background")

        self.runUpdate = False
        self.videoCapture = None

        self.currentHeight = 504
        self.currentWidth = 896
        self.image = None
        # self.check_box = [170, 90, 470, 390]
        self.check_box = load_ca(896, 504)
        # is in error box

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
        file_menu.add_command(label="Open Camera", command=self.open_camera)
        file_menu.add_command(label="Check Seal",
                              command=lambda: MessageBox(self.window, f"This function is not yet developed"))
        file_menu.add_command(label="Product List",
                              command=lambda: MessageBox(self.window, f"This function is not yet developed"))
        file_menu.add_command(label="Version",
                              command=lambda: MessageBox(self.window, f"TokaiRika Version {Config.APP_VERSION}"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

    def create_tab_control(self):
        self.tab_video = ttk.Frame(self.tab_control)
        self.tab_video.bind("<Configure>", self._resize_image)

        self.tab_video.rowconfigure(0, weight=1)
        self.tab_video.columnconfigure(0, weight=1)

        self.hypl_connect = Button(self.tab_video, text="Open Camera", fg="blue", cursor="hand2", font=("Consolas", 32),
                                   bd=0, highlightthickness=0, width=39, height=10,
                                   command=self.open_camera)
        self.hypl_connect.grid(row=0, column=0, sticky="nsew")

        self.tab_control.add(self.tab_video, text="Video")

    def _resize_image(self, event):
        # padding by 25
        self.currentWidth = event.width - 25
        self.currentHeight = event.height - 25

    def reset_display(self):
        try:
            # destroy current display
            self.runUpdate = False  # turn off video detection
            self.btn_check.grid_forget()
            self.hypl_connect.destroy()
            self.displayImage.destroy()
            self.image = None

        except AttributeError:  # no displayImage
            # traceback.print_exc()
            pass

        # add link: Please connect to camera
        self.hypl_connect = Button(self.tab_video, text="Open Camera", fg="blue", cursor="hand2",
                                   font=("Consolas", 32), bd=0, highlightthickness=0, width=39, height=10,
                                   command=self.open_camera)
        self.hypl_connect.grid(row=0, column=0, sticky="nsew")

    # def set_check_area(self):
    #     try:
    #         if self.image is not None:
    #             imgrz = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
    #             ca = CheckAreaPopup(self.window, imgrz)
    #             self.check_box = save_ca(ca.W, ca.H)
    #
    #         else:
    #             messagebox.showinfo("Info", "Please open the camera or video first.")
    #             return
    #
    #     except:
    #         traceback.print_exc()

    # ==================================================================================================================
    # ----------------------------------------- RUN process ------------------------------------------------------------
    # ==================================================================================================================

    def check_object(self):
        try:
            self.runUpdate = False
            w = LoadingBox(self.window,
                           self.image[self.check_box[1]:self.check_box[3], self.check_box[0]:self.check_box[2]],
                           open_cam=False)
            self.runUpdate = True
            self.update_detection()
        except:
            traceback.print_exc()

    def open_video(self, event=None):
        """
        Open video - keep 'event=None' to work with window.bind
        """
        self.reset_display()
        video_file = get_data_askfile("Open Video file")
        # if self.quit()
        if video_file is None:
            self.reset_display()
            return
        # unsupported video format
        if not video_file.lower().endswith((".mp4", ".mkv", ".flv", ".wmv", ".mov", ".avi", ".webm")):
            messagebox.showinfo("Info", "Unsupported video format.")
            return

        self.open_vid_source(source=video_file)

    def open_camera(self):
        self.reset_display()
        self.open_vid_source(source=0)

    def open_vid_source(self, source=0):
        try:
            if self.videoCapture:
                self.videoCapture.release()

            if source == 0 or os.path.isfile(source):
                F = LoadingBox(self.window, None, True, source, "Opening...")
                if F.fps == 0:  # no camera found
                    # print(f"[{SRC.GUI}] - ERROR: NO CAMERA FOUND")
                    messagebox.showinfo("Info", "Camera not found. Open the video instead.")
                    self.open_video()
                else:
                    self.videoCapture = CVFreshestFrame(F.cap, F.fps)
                    print(f"[{SRC.GUI}] - Open video - source = {source}")
                    self.in_running()
            else:
                messagebox.showerror("Error", f"Source '{source}' is not found!")
                return
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

        self.check_box = load_ca(self.videoCapture.W, self.videoCapture.H)
        print(self.videoCapture.W, self.videoCapture.H, self.check_box)
        self.displayImage = Label(self.tab_video, borderwidth=1, relief='solid')
        self.displayImage.grid(row=0, column=0, sticky="nsew")
        self.displayImage.bind("<Configure>", self._resize_image)

        self.btn_check = Button(self.tab_video, text="Check", cursor="hand2", bg="yellow",  # fg="red",
                                font=("Consolas", 14),
                                bd=1, highlightthickness=1, width=8, height=2,
                                command=self.check_object)
        self.btn_check.grid(row=0, column=0, padx=20, pady=20, sticky="se")
        self.update_detection()

    def update_detection(self):
        try:
            if self.runUpdate:

                cnt, img0 = self.videoCapture.read()

                if not cnt:
                    self.runUpdate = False
                    messagebox.showinfo("Info", "Video is over!")
                    self.videoCapture.release()
                    self.reset_display()
                    self.btn_check.grid_forget()
                    return

                if not (img0 is None or img0.size == 0):
                    self.image = img0.copy()
                    cv2.rectangle(img0,
                                  (int(self.check_box[0]), int(self.check_box[1])),
                                  (int(self.check_box[2]), int(self.check_box[3])),
                                  (0, 255, 0), 2
                                  )
                    if img0.shape[0] != self.currentWidth:
                        ssize = image_resize_size(img0.shape, (self.currentHeight, self.currentWidth))
                        if ssize != -1:
                            img0 = cv2.resize(img0, ssize)
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
