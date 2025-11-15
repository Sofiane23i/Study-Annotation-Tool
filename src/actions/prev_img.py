from PIL import Image, ImageTk
import state as S


def prev_img():
    S.pos = S.pos - 1
    if S.pos < 0:
        S.pos = 0
        if S.btn_prev:
            S.btn_prev["state"] = "disabled"
    else:
        img2 = ImageTk.PhotoImage(Image.open(S.list_of_files[S.pos-1]).resize((800, 800)))
        S.label.configure(image=img2)
        S.label.image = img2
        if S.btn_next:
            S.btn_next["state"] = "normal"
