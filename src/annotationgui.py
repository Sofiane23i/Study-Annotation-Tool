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
window.title("Study Annotation Tool - Handwriting Analysis")
window.rowconfigure(0, minsize=800, weight=1)
window.columnconfigure(1, minsize=800, weight=1)
window.configure(bg='#2c3e50')

# Define colors for modern look
COLORS = {
    'bg_dark': '#2c3e50',
    'bg_panel': '#34495e',
    'bg_section': '#3d566e',
    'accent': '#3498db',
    'accent_hover': '#2980b9',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'text_light': '#ecf0f1',
    'text_muted': '#95a5a6',
    'border': '#4a6785'
}

# Custom button style function
def create_styled_button(parent, text, command=None, style='normal', width=18):
    colors = {
        'normal': ('#3498db', '#2980b9', 'white'),
        'success': ('#27ae60', '#219a52', 'white'),
        'warning': ('#f39c12', '#d68910', 'white'),
        'danger': ('#e74c3c', '#c0392b', 'white'),
        'secondary': ('#7f8c8d', '#6c7a7b', 'white')
    }
    bg, hover, fg = colors.get(style, colors['normal'])
    
    btn = tk.Button(parent, text=text, command=command,
                    bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
                    font=('Segoe UI', 10, 'bold'), relief=tk.FLAT,
                    cursor='hand2', width=width, pady=8)
    
    def on_enter(e):
        if btn['state'] != 'disabled':
            btn['bg'] = hover
    def on_leave(e):
        if btn['state'] != 'disabled':
            btn['bg'] = bg
    
    btn.bind('<Enter>', on_enter)
    btn.bind('<Leave>', on_leave)
    return btn

# Main content area
txt_edit = tk.Frame(window, bg=COLORS['bg_dark'])

# Sidebar panel with sections
fr_buttons = tk.Frame(window, bg=COLORS['bg_panel'], relief=tk.FLAT, bd=0, padx=10, pady=10)

# App title in sidebar
title_frame = tk.Frame(fr_buttons, bg=COLORS['bg_panel'])
title_frame.pack(fill=tk.X, pady=(0, 15))
tk.Label(title_frame, text="📝 Annotation Tool", font=('Segoe UI', 14, 'bold'), 
         bg=COLORS['bg_panel'], fg=COLORS['text_light']).pack()
tk.Label(title_frame, text="Handwriting Analysis Suite", font=('Segoe UI', 9), 
         bg=COLORS['bg_panel'], fg=COLORS['text_muted']).pack()

# Separator
tk.Frame(fr_buttons, height=2, bg=COLORS['border']).pack(fill=tk.X, pady=10)

# Section 1: Input Sources
section1 = tk.LabelFrame(fr_buttons, text=" 📂 Input Source ", font=('Segoe UI', 10, 'bold'),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], 
                         relief=tk.FLAT, bd=1, padx=10, pady=10)
section1.pack(fill=tk.X, pady=(0, 10))

btn_open = create_styled_button(section1, "📁 Open Folder", init_pathandfolders, 'normal')
btn_open.pack(fill=tk.X, pady=3)

btn_htr = create_styled_button(section1, "✍️ Generate HTR", generate_htr, 'success')
btn_htr.pack(fill=tk.X, pady=3)

# Section 2: Word Detection
section2 = tk.LabelFrame(fr_buttons, text=" 🔍 Word Detection ", font=('Segoe UI', 10, 'bold'),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], 
                         relief=tk.FLAT, bd=1, padx=10, pady=10)
section2.pack(fill=tk.X, pady=(0, 10))

btn_save = create_styled_button(section2, "🎯 Detect Words", save_file, 'warning')
btn_save.pack(fill=tk.X, pady=3)

# Detection parameters frame
params_frame = tk.Frame(section2, bg=COLORS['bg_section'])
params_frame.pack(fill=tk.X, pady=(10, 5))

# Scale slider with label
scale_frame = tk.Frame(params_frame, bg=COLORS['bg_section'])
scale_frame.pack(fill=tk.X, pady=2)
scale_label = tk.Label(scale_frame, text="🔎 Scale: 1.0x", font=('Segoe UI', 9),
                       bg=COLORS['bg_section'], fg=COLORS['text_light'], anchor='w')
scale_label.pack(fill=tk.X)
scale_slider = tk.Scale(scale_frame, from_=0.5, to=3.0, resolution=0.1, 
                        orient=tk.HORIZONTAL, length=150,
                        bg=COLORS['bg_section'], fg=COLORS['text_light'],
                        troughcolor=COLORS['bg_dark'], activebackground=COLORS['accent'],
                        highlightthickness=0, sliderrelief=tk.FLAT)
scale_slider.set(1.0)
scale_slider.pack(fill=tk.X)

def update_scale_label(val):
    S.image_scale = float(val)
    scale_label.config(text=f"🔎 Scale: {float(val):.1f}x")

scale_slider.config(command=update_scale_label)

# Padding slider with label  
padding_frame = tk.Frame(params_frame, bg=COLORS['bg_section'])
padding_frame.pack(fill=tk.X, pady=2)
padding_label = tk.Label(padding_frame, text="📏 Padding: 0px", font=('Segoe UI', 9),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], anchor='w')
padding_label.pack(fill=tk.X)
padding_slider = tk.Scale(padding_frame, from_=-20, to=50, resolution=1,
                          orient=tk.HORIZONTAL, length=150,
                          bg=COLORS['bg_section'], fg=COLORS['text_light'],
                          troughcolor=COLORS['bg_dark'], activebackground=COLORS['accent'],
                          highlightthickness=0, sliderrelief=tk.FLAT)
padding_slider.set(0)
padding_slider.pack(fill=tk.X)

def update_padding_label(val):
    S.bbox_padding = int(float(val))
    padding_label.config(text=f"📏 Padding: {int(float(val))}px")

padding_slider.config(command=update_padding_label)

# Section 3: Annotation
section3 = tk.LabelFrame(fr_buttons, text=" ✏️ Annotation ", font=('Segoe UI', 10, 'bold'),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], 
                         relief=tk.FLAT, bd=1, padx=10, pady=10)
section3.pack(fill=tk.X, pady=(0, 10))

btn_annotate = create_styled_button(section3, "📝 Word Annotation", annotate, 'success')
btn_annotate.pack(fill=tk.X, pady=3)

from actions.character_annotate import character_annotate
btn_char_annotate = create_styled_button(section3, "🔤 Character Annotation", character_annotate, 'secondary')
btn_char_annotate.pack(fill=tk.X, pady=3)

# Status bar at bottom of sidebar
status_frame = tk.Frame(fr_buttons, bg=COLORS['bg_panel'])
status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))
tk.Frame(status_frame, height=1, bg=COLORS['border']).pack(fill=tk.X, pady=(0, 10))
status_label = tk.Label(status_frame, text="Ready", font=('Segoe UI', 9),
                        bg=COLORS['bg_panel'], fg=COLORS['text_muted'])
status_label.pack()

# Grid layout
fr_buttons.grid(row=0, column=0, sticky="nsew")
txt_edit.grid(row=0, column=1, sticky="nsew")

# Initial button states
btn_annotate["state"] = "disabled"
btn_save["state"] = "disabled"
btn_char_annotate["state"] = "normal"
scale_slider["state"] = "disabled"
padding_slider["state"] = "disabled"

# Update status helper function
def update_status(message):
    status_label.config(text=message)

S.update_status = update_status

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
S.btn_char_annotate = btn_char_annotate
S.scale_slider = scale_slider
S.padding_slider = padding_slider


# Load background image with proper error handling
try:
    # Try different possible paths for the image
    image_paths = [
        'StudyAnnotateTool.jpg',  # Current directory
        os.path.join(os.path.dirname(__file__), 'StudyAnnotateTool.jpg'),  # Same as script
        os.path.join(os.path.dirname(__file__), '..', 'images', 'screen1.png'),  # Images folder
    ]
    
    img1 = None
    for image_path in image_paths:
        try:
            if os.path.exists(image_path):
                img1 = ImageTk.PhotoImage(Image.open(image_path).resize((800,800)))
                print(f"Successfully loaded image from: {image_path}")
                break
        except Exception as e:
            print(f"Failed to load image from {image_path}: {e}")
            continue
    
    if img1 is None:
        # Create a styled placeholder image
        from PIL import ImageDraw, ImageFont
        placeholder = Image.new('RGB', (800, 800), color='#34495e')
        draw = ImageDraw.Draw(placeholder)
        
        # Add welcome text
        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            font_large = ImageFont.load_default()
            font_small = font_large
        
        # Center text
        draw.text((400, 350), "📝 Study Annotation Tool", fill='#ecf0f1', anchor='mm', font=font_large)
        draw.text((400, 400), "Select an input source to begin", fill='#95a5a6', anchor='mm', font=font_small)
        draw.text((400, 440), "• Open Folder - Load images from disk", fill='#7f8c8d', anchor='mm', font=font_small)
        draw.text((400, 470), "• Generate HTR - Create synthetic handwriting", fill='#7f8c8d', anchor='mm', font=font_small)
        
        img1 = ImageTk.PhotoImage(placeholder)
        print("Created styled placeholder image")
        
except Exception as e:
    print(f"Image loading error: {e}")
    placeholder = Image.new('RGB', (800, 800), color='#34495e')
    img1 = ImageTk.PhotoImage(placeholder)

# Create main content label with styled background
content_frame = tk.Frame(txt_edit, bg=COLORS['bg_dark'], padx=20, pady=20)
content_frame.pack(expand=True, fill=tk.BOTH)

label = tk.Label(content_frame, image=img1, bg=COLORS['bg_dark'])
label.pack(expand=True)
S.label = label
        
window.mainloop()
