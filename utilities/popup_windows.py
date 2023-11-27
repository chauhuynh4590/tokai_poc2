import datetime
import sys
import threading
import traceback
from tkinter import *
from tkinter import messagebox
from tkinter.font import Font

import cv2
from PIL import ImageTk, Image

from config import Config
from utilities.check_object_CLIP import model_clip, CheckStatus
from utilities.general import SRC, image_resize_size
from rembg import remove


def center(win):
    """
    centers a tkinter window
    :param win: the main window or Toplevel window to center
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry("{}x{}+{}+{}".format(width, height, x, y))
    win.deiconify()


class MessageBox:
    """Prevent open multiple times when using default tkinter.messagebox"""

    def __init__(self, master, msg):
        self.top = Toplevel(master)
        self.top.geometry("0x0")
        self.top.resizable(False, False)
        self.top.overrideredirect(True)
        self.top.after(10, self.show, msg)
        # wait for popup complete
        self.top.transient(master)
        self.top.grab_set()
        master.wait_window(self.top)

    def show(self, msg):
        messagebox.showinfo("Information", msg)
        self.top.destroy()


class LoadingBox:
    def __init__(self, master, image, open_cam, source=0, title="Checking..."):
        self.master = master
        self.top = Toplevel(master)
        self.top.overrideredirect(1)
        # self.top.title(title)
        # self.top.geometry("50x50")
        self.top.resizable(False, False)

        file = Config.LOADING_GIF
        info = Image.open(file)
        self.current_image = None
        self.fps = 0
        self.cap = None

        self.frames = info.n_frames  # number of frames

        self.photoimage_objects = []
        for i in range(self.frames):
            obj = PhotoImage(file=file, format=f"gif -index {i}")
            self.photoimage_objects.append(obj)

        # --------------------------------------------------------------------------------------------------------------
        self.gif_label = Label(self.top, image="", height=2)
        self.gif_label.grid(row=0, column=0, sticky="nsew")

        Label(self.top, text=title, font=('Consolas', 14), height=2, width=16,
              anchor='w', bg="#FCFEFC").grid(row=0, column=1)
        # --------------------------------------------------------------------------------------------------------------

        self.run = True
        self.img_from_db = None
        self.status = CheckStatus.NULL
        self.file_from_db = ''

        if open_cam:
            self.top.after(10, self.open_cam_animation)
            threading.Thread(target=self.check_camera, args=(source,)).start()
        elif not open_cam:
            self.top.after(10, self.animation)
            threading.Thread(target=self.check, args=(image,)).start()

        self.top.protocol("WM_DELETE_WINDOW", self.top.destroy)
        # wait for popup complete
        center(self.top)
        self.top.transient(master)
        self.top.grab_set()
        master.wait_window(self.top)

    def open_cam_animation(self, current_frame=0):
        if self.run:
            image = self.photoimage_objects[current_frame]

            self.gif_label.configure(image=image)
            current_frame = current_frame + 1

            if current_frame == self.frames:
                current_frame = 0

            self.top.after(50, lambda: self.open_cam_animation(current_frame))
        else:
            self.top.destroy()

    def check_camera(self, source=0):
        self.cap = cv2.VideoCapture(source)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.run = False

    def animation(self, current_frame=0):
        if self.run:
            image = self.photoimage_objects[current_frame]

            self.gif_label.configure(image=image)
            current_frame = current_frame + 1

            if current_frame == self.frames:
                current_frame = 0

            self.top.after(50, lambda: self.animation(current_frame))
        else:
            self.top.destroy()

            # print(f"[{SRC.POPUP_WIN}] - Status = {self.status}; File = {self.file_from_db}, ")

            if self.status == CheckStatus.FOUND:
                dt = self.file_from_db.split("_")
                if len(dt) != 5:
                    txt_data = ['(None)'] * 4
                else:
                    txt_data = dt[1:]
                    txt_data[-1] = dt[-1].split(".")[0].replace("@", " ")  # remove string: '.png'
                PopupResult80(self.master, self.img_from_db, txt_data)

            elif self.status == CheckStatus.NOT_FOUND:
                confirm_box = ConfirmAdd(self.master)
                if confirm_box.isOK:
                    PopupAddObject(self.master, self.current_image)

            elif self.status == CheckStatus.CONFUSE:
                PopupConfirm5080(self.master, self.img_from_db, self.current_image)

            else:
                print(f"[{SRC.POPUP_WIN}] - NULL")

    def check(self, image):
        try:
            # print(f"[{SRC.POPUP_WIN}] - Begin Check")
            self.current_image = self.removebg_and_crop(image)  # , bgcolor=(0, 0, 0, 0), border=1)
            self.img_from_db, self.status, self.file_from_db = model_clip.find_object(
                img=Image.fromarray(self.current_image)
            )
        except:
            print(f"[{SRC.POPUP_WIN}] - Check fail")
            traceback.print_exc()

        self.run = False

    @staticmethod
    def removebg_and_crop(img_np, bgcolor=(192, 192, 192, 0), border=191):
        img_np = remove(img_np, bgcolor=bgcolor)
        top, left = 0, 0
        bottom, right, _ = img_np.shape
        # print(top, bottom, left, right)
        for i in range(right):  # left: from 0 -> width
            if border in img_np[:, i]:
                left = i
                break
        for i in range(bottom):  # top: from 0 -> height
            if border in img_np[i, left:]:
                top = i
                break
        for i in range(bottom - 1, top, -1):  # bottom: from height -> top
            if border in img_np[i, left:]:
                bottom = i
                break
        for i in range(right - 1, left, -1):  # right: from width -> left
            if border in img_np[:, i]:
                right = i
                break
        # print(top, bottom, left, right)
        return img_np[top:bottom, left:right]


class ConfirmAdd:
    def __init__(self, master):
        self.top = Toplevel(master)
        self.top.title("Confirm")
        self.top.resizable(False, False)

        text_font = Font(family="Consolas", size=14)

        self.isOK = False

        img = ImageTk.PhotoImage(Image.open(Config.ICON_ASK))
        msg = "The product does not exist in the database.\nDo you want to add to the database?"
        Label(self.top, image=img, width=50, font=text_font).grid(row=0, column=0, padx=15, pady=15)
        Label(self.top, text=msg, width=45, height=3, font=text_font, borderwidth=0, relief='solid',
              justify="left").grid(row=0, column=1, padx=5, pady=15)

        group_btn = LabelFrame(self.top, width=50, borderwidth=0)
        group_btn.grid(row=1, column=1, sticky="nsew")
        group_btn.grid_columnconfigure((0), weight=1)
        # Button that lets the user open a video
        self.btn_no = Button(group_btn, text="NO", width=10, height=1, font=text_font,
                             command=self.top.destroy)
        self.btn_no.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Button that lets the user open a video
        self.btn_ok = Button(group_btn, text="YES", width=10, height=1, font=text_font,
                             command=self.ok)
        self.btn_ok.grid(row=0, column=0, padx=80, pady=15, sticky="e")

        center(self.top)
        # wait for popup complete
        self.top.transient(master)
        self.top.grab_set()
        master.wait_window(self.top)

    def ok(self):
        self.isOK = True
        self.top.destroy()


class PopupResult80:
    def __init__(self, master, image, txt_data):
        self.top = Toplevel(master)

        self.top.title("Result")
        self.top.resizable(False, False)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, _ = image.shape
        photo2 = ImageTk.PhotoImage(image=Image.fromarray(image))

        header_font = Font(family="Consolas", size=16)
        text_font = Font(family="Consolas", size=14)

        # --------------------------------------------------------------------------------------------------------------
        group_Notif = LabelFrame(self.top, borderwidth=1, relief='solid')
        group_Notif.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        Label(group_Notif, text="Note:", font=header_font).grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.lbl_notif = Label(group_Notif, text="The product has been found in the database", font=header_font)
        self.lbl_notif.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        # --------------------------------------------------------------------------------------------------------------
        group_showDB = LabelFrame(self.top, borderwidth=0, relief='solid')
        group_showDB.grid(row=1, column=0, sticky="nsew")
        # group_showDB.grid_columnconfigure((0, 1), weight=1)

        Label(group_showDB, borderwidth=0, relief='solid',
              text="Image from database:", font=text_font, anchor='w').grid(row=0, column=0)
        self.img_target = Label(group_showDB, borderwidth=1, relief="solid", height=h, width=w, image=photo2)
        self.img_target.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        Label(group_showDB, borderwidth=0, relief='solid',
              text="Product information:", font=text_font, anchor='w').grid(row=0, column=1)

        group_showTxtDB = LabelFrame(group_showDB, borderwidth=0, relief='solid')
        group_showTxtDB.grid(row=1, column=1, sticky="nsew")

        Label(group_showTxtDB, text="Name:", font=text_font).grid(row=0, column=0, padx=5, pady=15, sticky="w")
        self.txt_name = Label(group_showTxtDB, width=20,  # borderwidth=1, relief='solid',
                              font=text_font, text=txt_data[0], justify='left', anchor='w')
        self.txt_name.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        Label(group_showTxtDB, text="Size:", font=text_font).grid(row=1, column=0, padx=5, pady=15, sticky="w")
        self.txt_size = Label(group_showTxtDB, width=20,  # borderwidth=1, relief='solid',
                              font=text_font, text=txt_data[1], justify='left', anchor='w')
        self.txt_size.grid(row=1, column=1, padx=10, pady=15, sticky="w")

        Label(group_showTxtDB, text="Amount:", font=text_font).grid(row=2, column=0, padx=5, pady=15, sticky="w")
        self.txt_amount = Label(group_showTxtDB, width=20,  # borderwidth=1, relief='solid',
                                font=text_font, text=txt_data[2], justify='left', anchor='w')
        self.txt_amount.grid(row=2, column=1, padx=10, pady=15, sticky="w")

        Label(group_showTxtDB, text="Description:", font=text_font).grid(row=3, column=0, padx=5, pady=15, sticky="w")
        self.txt_amount = Label(group_showTxtDB, width=20, height=3,  # borderwidth=1, relief='solid',
                                font=text_font, text=txt_data[3], wraplength=200, justify='left')
        self.txt_amount.grid(row=3, column=1, padx=10, pady=15, sticky="w")

        # self.txt_amount.insert(END, txt_data[3])
        # self.txt_amount.config(wrap=WORD, state='disabled')
        # --------------------------------------------------------------------------------------------------------------
        group_Btn = LabelFrame(self.top, borderwidth=0, relief='solid')
        group_Btn.grid(row=3, column=0, sticky="nsew")
        group_Btn.grid_columnconfigure((0), weight=1)

        self.btn_confirm = Button(group_Btn, text="Confirm", height=1, font=text_font,
                                  command=self._quit)
        self.btn_confirm.grid(row=0, column=0, padx=10, pady=10, sticky="we")
        # --------------------------------------------------------------------------------------------------------------
        # wait for popup complete
        center(self.top)
        self.top.transient(master)
        self.top.grab_set()
        master.wait_window(self.top)

    def _quit(self):
        self.top.destroy()


class PopupConfirm5080:
    def __init__(self, master, db_image, cur_image):
        self.master = master
        self.cur_image = cur_image
        self.top = Toplevel(master)

        self.top.title("Confirm")
        self.top.resizable(False, False)

        rsz_db_img = cv2.resize(db_image, image_resize_size(db_image.shape))
        rsz_cur_img = cv2.resize(cur_image, image_resize_size(cur_image.shape))

        # convert to PIL color to display on tkinter
        rsz_db_img = cv2.cvtColor(rsz_db_img, cv2.COLOR_BGR2RGB)
        rsz_cur_img = cv2.cvtColor(rsz_cur_img, cv2.COLOR_BGR2RGB)

        h1, w1, _ = rsz_db_img.shape
        h2, w2, _ = rsz_cur_img.shape
        photo1 = ImageTk.PhotoImage(image=Image.fromarray(rsz_db_img))
        photo2 = ImageTk.PhotoImage(image=Image.fromarray(rsz_cur_img))

        header_font = Font(family="Consolas", size=16)
        text_font = Font(family="Consolas", size=14)

        img = ImageTk.PhotoImage(Image.open(Config.ICON_ASK))
        msg = "Similar product were found in the database.\nDo you want to add the current product to the database?"

        # --------------------------------------------------------------------------------------------------------------
        group_Notif = LabelFrame(self.top, borderwidth=1, relief='solid')
        group_Notif.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        Label(group_Notif, image=img, width=50, font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.lbl_notif = Label(group_Notif, text=msg, font=header_font)
        self.lbl_notif.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        # --------------------------------------------------------------------------------------------------------------
        group_showDB = LabelFrame(self.top, borderwidth=0, relief='solid')
        group_showDB.grid(row=1, column=0, sticky="nsew")
        group_showDB.grid_columnconfigure((0, 1), weight=1)

        Label(group_showDB, borderwidth=0, relief='solid',
              text="Product from database:", font=text_font, anchor='w').grid(row=0, column=0)
        self.img_target = Label(group_showDB, borderwidth=1, relief="solid", height=h1, width=w1, image=photo1)
        self.img_target.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        Label(group_showDB, borderwidth=0, relief='solid',
              text="Current Product:", font=text_font, anchor='w').grid(row=0, column=1)

        self.img_target = Label(group_showDB, borderwidth=1, relief="solid", height=h2, width=w2, image=photo2)
        self.img_target.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        # --------------------------------------------------------------------------------------------------------------
        group_Btn = LabelFrame(self.top, borderwidth=0, relief='solid')
        group_Btn.grid(row=3, column=0, sticky="nsew")
        group_Btn.grid_columnconfigure((0), weight=1)

        self.btn_confirm = Button(group_Btn, text="NO", width=20, height=1, font=text_font,
                                  command=self._quit)
        self.btn_confirm.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.btn_save = Button(group_Btn, text="YES", width=20, height=1, font=text_font,
                               command=self._on_save_press)
        self.btn_save.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        # --------------------------------------------------------------------------------------------------------------
        # wait for popup complete
        center(self.top)
        self.top.transient(master)
        self.top.grab_set()
        master.wait_window(self.top)

    def _quit(self):
        self.top.destroy()

    def _on_save_press(self):
        self._quit()
        PopupAddObject(self.master, self.cur_image)

    @staticmethod
    def gen_file_id() -> str:
        """Generate an id based on current datetime"""
        name = f"{datetime.datetime.now().strftime(f'%Y%m%d%H%M%S')}"
        return name


class PopupAddObject:
    def __init__(self, master, image):
        self.top = Toplevel(master)

        self.top.title("Insert Product")
        self.top.resizable(False, False)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        rsz_img = cv2.resize(image, image_resize_size(image.shape))
        h, w, _ = rsz_img.shape
        photo2 = ImageTk.PhotoImage(image=Image.fromarray(rsz_img))

        header_font = Font(family="Consolas", size=16)
        text_font = Font(family="Consolas", size=14)

        # --------------------------------------------------------------------------------------------------------------
        group_Notif = LabelFrame(self.top, borderwidth=1, relief='solid')
        group_Notif.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        Label(group_Notif, text="Note:", font=header_font).grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.lbl_notif = Label(group_Notif, text="Add product to the database", font=header_font)
        self.lbl_notif.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        # --------------------------------------------------------------------------------------------------------------
        group_showDB = LabelFrame(self.top, borderwidth=0, relief='solid')
        group_showDB.grid(row=1, column=0, sticky="nsew")
        # group_showDB.grid_columnconfigure((0, 1), weight=1)

        Label(group_showDB, borderwidth=0, relief='solid',
              text="Product Image:", font=text_font, anchor='w').grid(row=0, column=0)
        self.img_target = Label(group_showDB, borderwidth=1, relief="solid", height=h, width=w, image=photo2)
        self.img_target.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        Label(group_showDB, borderwidth=0, relief='solid',
              text="Product information:", font=text_font, anchor='w').grid(row=0, column=1)

        group_showTxtDB = LabelFrame(group_showDB, borderwidth=0, relief='solid')
        group_showTxtDB.grid(row=1, column=1, sticky="nsew")

        Label(group_showTxtDB, text="Name:", font=text_font).grid(row=0, column=0, padx=5, pady=15, sticky="w")
        self.txt_name = Entry(group_showTxtDB, width=20, font=text_font)
        self.txt_name.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        Label(group_showTxtDB, text="Size:", font=text_font).grid(row=1, column=0, padx=5, pady=15, sticky="w")
        self.txt_size = Entry(group_showTxtDB, width=20, font=text_font)
        self.txt_size.grid(row=1, column=1, padx=10, pady=15, sticky="w")

        Label(group_showTxtDB, text="Amount:", font=text_font).grid(row=2, column=0, padx=5, pady=15, sticky="w")
        self.txt_amount = Entry(group_showTxtDB, width=20, font=text_font)
        self.txt_amount.grid(row=2, column=1, padx=10, pady=15, sticky="w")

        Label(group_showTxtDB, text="Description:", font=text_font).grid(row=3, column=0, padx=5, pady=15, sticky="w")
        self.txt_descrpt = Entry(group_showTxtDB, width=20, font=text_font)
        self.txt_descrpt.grid(row=3, column=1, padx=10, pady=15, sticky="w")

        group_Btn = LabelFrame(self.top, borderwidth=0, relief='solid')
        group_Btn.grid(row=3, column=0, sticky="nsew")
        group_Btn.grid_columnconfigure((0), weight=1)

        self.btn_confirm = Button(group_Btn, text="Cancel", width=20, height=1, font=text_font,
                                  command=self._quit)
        self.btn_confirm.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.btn_save = Button(group_Btn, text="Save", width=20, height=1, font=text_font,
                               command=lambda: self._on_save_press(image))
        self.btn_save.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        # --------------------------------------------------------------------------------------------------------------
        # wait for popup complete
        center(self.top)
        self.top.transient(master)
        self.top.grab_set()
        master.wait_window(self.top)

    def _quit(self):
        self.top.destroy()

    def _on_save_press(self, image=None):
        try:
            name, size, amount, desc = (self.txt_name.get(), self.txt_size.get(), self.txt_amount.get(),
                                        self.txt_descrpt.get())
            if any(x == "" for x in [name, size, amount]):
                MessageBox(self.top, "Fields cannot be blank!")
                return
            if any(x.__contains__("_") for x in [name, size, amount]):
                MessageBox(self.top, "Fields cannot contain '_' (underscore)!")
                return
            if not amount.isnumeric() or int(amount) != float(amount):
                MessageBox(self.top, "The Amount must be integer!")
                return

            if int(amount) < 1:
                MessageBox(self.top, "The Amount must be greater than 0!")
                return
            desc_data = desc.replace(" ", "@")
            filename = rf"{self.gen_file_id()}_{name}_{size}_{amount}_{desc_data}"
            # print(f"[{SRC.POPUP_WIN}] - Add: {filename}, shape = {image.shape}")
            img_name = model_clip.add_object(Image.fromarray(image), desc, filename)

        except:
            traceback.print_exc()
        self._quit()

    @staticmethod
    def gen_file_id() -> str:
        """Generate an id based on current datetime"""
        name = f"{datetime.datetime.now().strftime(f'%Y%m%d%H%M%S')}"
        return name


class ConfirmBox:
    def __init__(self, master, msg):
        self.top = Toplevel(master)
        self.top.title("Confirm")
        self.top.resizable(False, False)

        text_font = Font(family="Consolas", size=14)

        self.isOK = False

        img = ImageTk.PhotoImage(Image.open(Config.ICON_ASK))

        Label(self.top, image=img, width=50, font=text_font).grid(row=0, column=0, padx=15, pady=15)
        Label(self.top, text=msg, width=25, height=2, font=text_font,
              wraplength=300, justify="left").grid(row=0, column=1, padx=5, pady=15)

        group_btn = LabelFrame(self.top, width=50, borderwidth=0)
        group_btn.grid(row=1, column=1, sticky="e")
        # Button that lets the user open a video
        self.btn_cancel = Button(group_btn, text="Cancel", width=8, height=1, font=text_font,
                                 command=self.top.destroy)
        self.btn_cancel.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Button that lets the user open a video
        self.btn_ok = Button(group_btn, text="OK", width=8, height=1, font=text_font,
                             command=self.ok)
        self.btn_ok.grid(row=0, column=1, padx=20, pady=15, sticky="e")

        center(self.top)
        # wait for popup complete
        self.top.transient(master)
        self.top.grab_set()
        master.wait_window(self.top)

    def ok(self):
        self.isOK = True
        self.top.destroy()


# class CheckAreaPopup:
#     def __init__(self, master, img):
#         self.top = Toplevel(master)
#         self.top.title("Set check area")
#         self.top.resizable(False, False)
#         self.top.rowconfigure(0, weight=1)
#         self.top.columnconfigure(0, weight=1)
#         w, h, _ = img.shape
#
#         self.canvas_run = Canvas(self.top)  # , width=1280, height=720)  # width=img.shape[1], height=img.shape[0])
#         self.canvas_run.grid(row=0, column=0, padx=2, pady=4)
#         # self.canvas_run.grid(row=0, column=0, sticky=N + S + E + W)
#         self.canvas_run.bind("<ButtonPress-1>", self._on_button_press)
#         self.canvas_run.bind("<B1-Motion>", self._on_move_press)
#         self.canvas_run.bind("<ButtonRelease-1>", self._on_button_release)
#
#         self.rect = None
#         self.x = self.y = 1
#         self.startX = None
#         self.startY = None
#         self.tk_im = ImageTk.PhotoImage(image=Image.fromarray(img))
#         # self.tk_im = ImageTk.PhotoImage(self.im)
#         self.canvas_run.create_image(0, 0, anchor="nw", image=self.tk_im)
#
#         # wait for popup complete
#         center(self.top)
#         self.top.transient(master)
#         self.top.grab_set()
#         master.wait_window(self.top)
#
#     def _quit(self):
#         self.top.destroy()
#
#     def _on_button_press(self, event):
#         self.isMouseMove = False
#         # save mouse drag start position
#         self.startX = self.canvas_run.canvasx(event.x)
#         self.startY = self.canvas_run.canvasy(event.y)
#
#         # create rectangle if not yet exist
#         if not self.rect:
#             self.rect = self.canvas_run.create_rectangle(self.x, self.y, 1, 1, outline="red", width=3)
#
#     def _on_move_press(self, event):
#         self.isMouseMove = True
#         self.curX = self.canvas_run.canvasx(event.x)
#         self.curY = self.canvas_run.canvasy(event.y)
#
#         self.canvas_run.coords(self.rect, self.startX, self.startY, self.curX, self.curY)
#
#     def _on_button_release(self, event):
#         if self.isMouseMove and \
#                 0 <= self.curX <= 1280 and \
#                 0 <= self.curY <= 720 and \
#                 0 <= self.startX <= 1280 and \
#                 0 <= self.startY <= 720:
#             ok = ConfirmBox(self.top, "Do you want to save?")
#             if not ok.isOK:
#                 print(f"[{SRC.POPUP_WIN}] - not save check_area")
#                 return
#             print(f"[{SRC.POPUP_WIN}] - save check_area")
#             self._save_area()
#             self._quit()
#
#     def _save_area(self):
#         check_area = [
#             int(min(self.startX, self.curX)),
#             int(min(self.startY, self.curY)),
#             int(max(self.startX, self.curX)),
#             int(max(self.startY, self.curY))
#         ]
#         value = f"{check_area[0]} {check_area[1]} {check_area[2]} {check_area[3]}"
#         print(f"{SRC.POPUP_WIN} - New CheckArea: {value}")
#         # ConfigFile.update_raw_conf("Setting", "check_area", value)
#         # Config.set_check_area(check_area)


if __name__ == "__main__":
    # -----------------    test
    class MainWindow(object):
        def __init__(self, master):
            self.master = master
            self.ff = LabelFrame(self.master, borderwidth=1)
            self.ff.pack(side="top", fill="both")

            self.master.bind("<Control-Alt-F9>", self.popup_connect)
            self.b = Button(self.ff, text="connect", command=self.popup_connect)
            self.b.pack()

            self.b1 = Button(self.ff, text="set conf", command=self.popup_setConf)
            self.b1.pack()

            self.b3 = Button(self.ff, text="confirm", command=self.popup_confirm)
            self.b3.pack()

            self.b4 = Button(self.ff, text="add", command=self.popup_add)
            self.b4.pack()

            self.b5 = Button(self.ff, text="test", command=self.popup_test)
            self.b5.pack()

            self.bload = Button(self.ff, text="loading", command=self.popup_load)
            self.bload.pack()

            self.b2 = Button(self.ff, text="print value", command=lambda: sys.stdout.write(self.entryValue() + "\n"))
            self.b2.pack()

        def popup_connect(self, event=None):
            pass
            # self.w = CameraPopup(self.master)
            # self.b["state"] = "disabled"
            # self.master.wait_window(self.w.top)
            # self.b["state"] = "normal"

        def popup_load(self, event=None):
            image = cv2.imread('../data/404.png')
            image2 = cv2.imread('../data/test.jpg')
            self.w = PopupConfirm5080(self.master, image, image2)

            # self.b["state"] = "disabled"
            # self.master.wait_window(self.w.top)
            # self.b["state"] = "normal"

        def popup_setConf(self):
            data = ["None a b c d e f g h i j k l m n o p q"] * 4
            im = cv2.imread('../data/404.png')
            image = cv2.resize(im, image_resize_size(im.shape))
            self.w = PopupResult80(self.master, image, data)
            # self.b["state"] = "disabled"
            # self.master.wait_window(self.w.top)
            # self.b["state"] = "normal"

        def popup_confirm(self):
            self.w = ConfirmBox(self.master, )  # "Do you want to reset confidence to default?")
            # self.w = ConfirmBox(self.master, "Do you want to save?")
            # self.b["state"] = "disabled"
            # self.master.wait_window(self.w.top)
            # self.b["state"] = "normal"

        def popup_add(self):
            image = cv2.imread('../data/404.png')
            self.w = PopupAddObject(self.master, image)

        def popup_test(self):
            image = cv2.imread('../data/404.png')
            self.w = LoadingBox(self.master, image, open_cam=True)
            # from tkinter.filedialog import askopenfilename
            # from cv2 import cv2

            pass

        def entryValue(self):
            return self.w.value


    # print(gen_file_id())

    root = Tk()
    m = MainWindow(root)
    root.mainloop()
