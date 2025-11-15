from http.client import OK
import os
import tkinter as tk
from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import Image, ImageTk
import argparse
from tkinter import filedialog
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
#from pathlib import Path

# shared state and separated actions
import state as S
from actions.open_folder import init_pathandfolders
from actions.save_file import save_file
from actions.annotate import annotate
from actions.generate_htr import generate_htr

import shutil
import glob

global pos
global nbr
global nbrout
global ind2
global pathDirectory
global list_of_files

my_log = 'log.txt'
if os.path.exists(my_log):
    file1 = open('log.txt', 'r')
    Lines = file1.readlines()
    print(Lines)
    line = str(Lines[0]).split(';')
    nbr = int(line[0])
    ind2 = int(line[1])
    nbrout = int(line[2])
    S.nbr = nbr
    S.ind2 = ind2
    S.nbrout = nbrout
else:    
    nbrout = 0
    nbr = 0
    ind2 = 0 #having same name of image in IAM txt file
    S.nbr = nbr
    S.ind2 = ind2
    S.nbrout = nbrout

pos = 0 #order listfile
S.pos = pos
    
#pathDirectory = '../data/testpng/'


def init_pathandfolders_legacy():
    # kept for reference; replaced by actions.open_folder.init_pathandfolders
    return init_pathandfolders()

def save_file_legacy():
    # replaced by actions.save_file.save_file
    return save_file()
    
## use actions.generate_htr.generate_htr (no local override)
    
# navigation hidden: no Next/Previous legacy wrappers


from actions.generate_annotation import annotation_file
     
    
from actions.import_annotation import import_annotaion
    
    
    #import re
    #with open(filename) as f, open('word_list.txt', 'a') as f1:
    #    f1.write('\n'.join(set(re.findall("[a-zA-Z\-\.'/]+", f.read()))))

from actions.refreshing import refreshing
    
    
    
def annotate_legacy():
    return annotate()
 
 

window = tk.Tk()
window.title("Simple Text Annotation")
window.rowconfigure(0, minsize=800, weight=1)
window.columnconfigure(1, minsize=800, weight=1)





txt_edit = tk.Frame(window)
fr_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
btn_open = tk.Button(fr_buttons, text="Open", command=init_pathandfolders)
btn_htr = tk.Button(fr_buttons, text="GenerateHTR", command=generate_htr)
btn_save = tk.Button(fr_buttons, text="Detect words...", command=save_file)
btn_annotate = tk.Button(fr_buttons, text="Annotate...", command=annotate)

btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
btn_htr.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
btn_save.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
btn_annotate.grid(row=3, column=0, sticky="ew", padx=5, pady=55)

fr_buttons.grid(row=0, column=0, sticky="ns")
txt_edit.grid(row=0, column=1, sticky="nsew")

btn_annotate["state"] = "disabled"
btn_save["state"] = "disabled"

# register UI elements into shared state for callbacks
S.window = window
S.txt_edit = txt_edit
S.fr_buttons = fr_buttons
S.btn_open = btn_open
S.btn_htr = btn_htr
S.btn_next = None
S.btn_prev = None
S.btn_save = btn_save
S.btn_annotate = btn_annotate


#Convert To PhotoImage
'''
img = ImageTk.PhotoImage(Image.open("../data/testpng/bg00102.jpg").resize((800, 800)))
label= tk.Label(txt_edit,image= img)
label.grid()
'''
img1= ImageTk.PhotoImage(Image.open('StudyAnnotateTool.jpg').resize((800,800)))
#Create a Label widget
label= tk.Label(txt_edit,image= img1)
label.grid()
S.label = label
'''
img = Image.open("../data/testpng/bg00102.jpg")
img = img.resize((800, 800))
tkimage = ImageTk.PhotoImage(img)
tk.Label(txt_edit, image=tkimage).grid()
''''''
if pos == 0:
    btn_prev["state"] = "disabled"
else:
    btn_prev["state"] = "enable"
'''    
        
window.mainloop()
