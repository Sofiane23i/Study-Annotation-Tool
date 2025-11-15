import os, glob
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import state as S

def init_pathandfolders():
    folder_selected = filedialog.askdirectory()
    if not folder_selected:
        return
    print(folder_selected)

    S.pathDirectory = folder_selected
    S.pos = 0

    # List images
    for filename in os.listdir(S.pathDirectory):
        print(filename)

    S.list_of_files = sorted(filter(os.path.isfile, glob.glob(S.pathDirectory + '/*.jpg')))
    for file_path in S.list_of_files:
        print(file_path)

    if not S.list_of_files:
        return

    print(S.list_of_files[0])
    print(os.listdir(S.pathDirectory)[0])
    print(len(os.listdir(S.pathDirectory)))

    print(S.list_of_files[S.pos])
    img2 = ImageTk.PhotoImage(Image.open(S.list_of_files[S.pos]).resize((800, 800)))
    S.label.configure(image=img2)
    S.label.image = img2

    S.directoryout = S.pathDirectory + "_data/out/"
    if not os.path.exists(S.directoryout):
        os.makedirs(S.directoryout)

    S.directorytmp = S.pathDirectory + "_data/tmp/"
    if not os.path.exists(S.directorytmp):
        os.makedirs(S.directorytmp)

    S.directorydone = S.pathDirectory + "_data/done/"
    if not os.path.exists(S.directorydone):
        os.makedirs(S.directorydone)

    # Update button states
    if S.btn_open:
        S.btn_open["state"] = "disabled"
    if S.btn_annotate:
        S.btn_annotate["state"] = "disabled"
    if S.btn_save:
        S.btn_save["state"] = "normal"
    if S.btn_prev:
        S.btn_prev["state"] = "disabled"
    if S.btn_next:
        S.btn_next["state"] = "normal" if len(S.list_of_files) > 1 else "disabled"
