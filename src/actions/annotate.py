import os
import tkinter as tk
from PIL import Image, ImageTk
import state as S
from .generate_annotation import annotation_file
from .import_annotation import import_annotaion
from .refreshing import refreshing


def annotate():
    S.r = tk.Toplevel()
    S.r.title("Words Annotation")

    canvas1 = tk.Canvas(S.r, height=1500, width=1500)
    canvas1.pack()

    yscrollbar = tk.Scrollbar(canvas1)
    yscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)

    canvas = tk.Canvas(canvas1, bd=0, yscrollcommand=yscrollbar.set)
    canvas.config(height=1000, width=1300, scrollregion=(0, 0, 1500, 2000))

    yscrollbar.config(command=canvas.yview)

    button1 = tk.Button(canvas, text="generateAnnotation", command=annotation_file)

    canvas2 = tk.Canvas(canvas1, bd=0, yscrollcommand=yscrollbar.set)
    button2 = tk.Button(canvas2, text="importAnnotation", command=import_annotaion)
    button2.grid(row=0, column=2, sticky="ns", padx=5, pady=55)

    S.text_box = tk.Text(canvas2, height=40, width=30)
    S.text_box.grid(row=1, column=2, sticky="ns", padx=5, pady=55)

    button3 = tk.Button(canvas2, text="refresh", command=refreshing)
    button3.grid(row=2, column=2, sticky="ns", padx=5, pady=55)

    frame = tk.Frame(canvas2)
    sb = tk.Scrollbar(frame)
    sb.pack(side=tk.RIGHT, fill=tk.BOTH)
    S.text_box.config(yscrollcommand=sb.set)
    sb.config(command=S.text_box.yview)

    canvas.grid(row=0, column=0, sticky="ew")
    canvas2.grid(row=0, column=2)

    print(len(os.listdir(S.directoryout + '/')))

    img2 = []
    rowindex = 0
    colindex = 0
    cpt = 0
    S.entries = []
    S.entryText = []

    ent = 0
    for jj in range(S.nbr - len(os.listdir(S.directoryout + '/')), S.nbr):
        if cpt == 10:
            colindex = (colindex + 130)
            cpt = 0
            rowindex = 0
        img2.append(ImageTk.PhotoImage(Image.open(S.directoryout + '/' + str(jj) + '.png').resize((100, 100))))
        canvas.create_image(rowindex, colindex, anchor=tk.NW, image=img2[abs(S.nbr - len(os.listdir(S.directoryout + '/')) - jj)])

        S.entryText.append(tk.StringVar())
        S.entries.append(tk.Entry(S.r, width=13, textvariable=S.entryText[ent]))

        canvas.create_window(rowindex + 55, colindex + 110, window=S.entries[abs(S.nbr - len(os.listdir(S.directoryout + '/')) - jj)])

        rowindex = (rowindex + 130)
        cpt = cpt + 1
        ent = ent + 1

    button1_window = canvas.create_window(rowindex + 55, colindex + 110, anchor=tk.NW, window=button1)

    S.r.mainloop()
