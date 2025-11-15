from PIL import Image, ImageTk
import os
import state as S


def next_img():
    S.pos = S.pos + 1
    if S.pos > len(os.listdir(S.pathDirectory)) - 1:
        S.pos = len(os.listdir(S.pathDirectory)) - 1
        if S.btn_next:
            S.btn_next["state"] = "disabled"
    else:
        img2 = ImageTk.PhotoImage(Image.open(S.list_of_files[S.pos]).resize((800, 800)))
        S.label.configure(image=img2)
        S.label.image = img2
        if S.btn_prev:
            S.btn_prev["state"] = "normal"
