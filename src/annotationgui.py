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
import cv2
import numpy as np
#from pathlib import Path

# shared state and separated actions
import state as S
from actions.open_folder import init_pathandfolders
from actions.save_file import save_file
from actions.annotate import annotate
from actions.generate_htr import generate_htr
from actions.line_annotate import detect_text_lines

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

# ============================================
# LINE DETECTION FUNCTION
# ============================================
def detect_lines_with_autofill():
    """
    Detect text lines in the current image and open annotation window 
    with auto-filled text from input area.
    """
    from tkinter import messagebox
    
    # Check if image is loaded
    image_path = None
    if hasattr(S, 'list_of_files') and S.list_of_files and S.pos < len(S.list_of_files):
        image_path = S.list_of_files[S.pos]
    elif hasattr(S, 'gan_batch_images') and S.gan_batch_images:
        # Use GAN generated images
        gan_batch_dir = os.path.join(os.path.dirname(__file__), 'gan_output_data', 'batch')
        if os.path.exists(gan_batch_dir):
            batch_files = sorted([f for f in os.listdir(gan_batch_dir) if f.endswith(('.png', '.jpg'))])
            if batch_files and S.gan_batch_index < len(batch_files):
                image_path = os.path.join(gan_batch_dir, batch_files[S.gan_batch_index])
    
    if not image_path or not os.path.exists(image_path):
        messagebox.showwarning("No Image", "Please load an image first:\n• Open Folder to load images\n• Generate HTR to create synthetic images")
        return
    
    # Get input text for auto-fill
    input_text = ""
    if hasattr(S, 'input_text') and S.input_text:
        input_text = S.input_text.strip()
    elif hasattr(S, 'input_text_area') and S.input_text_area:
        input_text = S.input_text_area.get("1.0", "end-1c").strip()
    
    # Load and process image
    try:
        img = cv2.imread(image_path)
        if img is None:
            messagebox.showerror("Error", f"Could not read image:\n{image_path}")
            return
        
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect lines
        lines = detect_text_lines(img_gray)
        
        if not lines:
            messagebox.showinfo("No Lines Detected", "No text lines detected in the image.\nTry adjusting the image or using manual annotation.")
            return
        
        # Parse input text into lines for auto-fill
        text_lines = input_text.splitlines() if input_text else []
        
        # Open line annotation window with detected lines
        from actions.line_annotate import LineAnnotationWindow
        S.input_text = input_text  # Ensure it's in state for the annotation window
        LineAnnotationWindow(image_path, detected_lines=lines, auto_text=text_lines)
        
        if hasattr(S, 'update_status') and S.update_status:
            S.update_status(f"Detected {len(lines)} lines")
        
    except Exception as e:
        messagebox.showerror("Error", f"Line detection failed:\n{str(e)}")
        import traceback
        traceback.print_exc()

# Section 2: Detection
section2 = tk.LabelFrame(fr_buttons, text=" 🔍 Detection ", font=('Segoe UI', 10, 'bold'),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], 
                         relief=tk.FLAT, bd=1, padx=10, pady=10)
section2.pack(fill=tk.X, pady=(0, 10))

btn_line_detect = create_styled_button(section2, "📄 Detect Lines", detect_lines_with_autofill, 'warning')
btn_line_detect.pack(fill=tk.X, pady=3)

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

# Section 3: Annotation (after detection)
section3 = tk.LabelFrame(fr_buttons, text=" ✏️ Annotation ", font=('Segoe UI', 10, 'bold'),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], 
                         relief=tk.FLAT, bd=1, padx=10, pady=10)
section3.pack(fill=tk.X, pady=(0, 10))

btn_annotate = create_styled_button(section3, "📝 Word Annotation", annotate, 'success')
btn_annotate.pack(fill=tk.X, pady=3)

from actions.line_annotate import line_annotate
btn_line_annotate = create_styled_button(section3, "📄 Line Annotation", line_annotate, 'success')
btn_line_annotate.pack(fill=tk.X, pady=3)

from actions.character_annotate import character_annotate
btn_char_annotate = create_styled_button(section3, "🔤 Character Annotation", character_annotate, 'secondary')
btn_char_annotate.pack(fill=tk.X, pady=3)

# Section 4: Settings
section4 = tk.LabelFrame(fr_buttons, text=" ⚙️ Settings ", font=('Segoe UI', 10, 'bold'),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], 
                         relief=tk.FLAT, bd=1, padx=10, pady=10)
section4.pack(fill=tk.X, pady=(0, 10))

# RTL Toggle
rtl_frame = tk.Frame(section4, bg=COLORS['bg_section'])
rtl_frame.pack(fill=tk.X, pady=2)
tk.Label(rtl_frame, text="Text Direction:", font=('Segoe UI', 9),
         bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)
rtl_var = tk.StringVar(value='ltr')
def update_text_direction(*args):
    S.text_direction = rtl_var.get()
    update_status(f"Text direction: {rtl_var.get().upper()}")
rtl_menu = tk.OptionMenu(rtl_frame, rtl_var, 'ltr', 'rtl', command=update_text_direction)
rtl_menu.config(bg=COLORS['bg_section'], fg=COLORS['text_light'], highlightthickness=0)
rtl_menu.pack(side=tk.RIGHT)

# Export Format
export_frame = tk.Frame(section4, bg=COLORS['bg_section'])
export_frame.pack(fill=tk.X, pady=2)
tk.Label(export_frame, text="Export Format:", font=('Segoe UI', 9),
         bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)
export_var = tk.StringVar(value='iam')
def update_export_format(*args):
    S.export_format = export_var.get()
    update_status(f"Export format: {export_var.get().upper()}")
export_menu = tk.OptionMenu(export_frame, export_var, 'iam', 'coco', 'yolo', 'voc', 'csv', 'jsonl', command=update_export_format)
export_menu.config(bg=COLORS['bg_section'], fg=COLORS['text_light'], highlightthickness=0)
export_menu.pack(side=tk.RIGHT)

# Auto-save toggle
autosave_var = tk.BooleanVar(value=True)
def toggle_autosave():
    S.auto_save_enabled = autosave_var.get()
    status = "enabled" if S.auto_save_enabled else "disabled"
    update_status(f"Auto-save {status}")
autosave_check = tk.Checkbutton(section4, text="Auto-save annotations", 
                                 variable=autosave_var, command=toggle_autosave,
                                 bg=COLORS['bg_section'], fg=COLORS['text_light'],
                                 selectcolor=COLORS['bg_dark'], activebackground=COLORS['bg_section'])
autosave_check.pack(fill=tk.X, pady=2)

# Progress bar section
progress_frame = tk.Frame(fr_buttons, bg=COLORS['bg_panel'])
progress_frame.pack(fill=tk.X, pady=(5, 0))
from tkinter import ttk
style = ttk.Style()
style.configure("Custom.Horizontal.TProgressbar", troughcolor=COLORS['bg_dark'], background=COLORS['accent'])
progress_var = tk.DoubleVar(value=0)
progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100, 
                                style="Custom.Horizontal.TProgressbar", length=180)
progress_bar.pack(fill=tk.X, pady=2)
progress_label = tk.Label(progress_frame, text="", font=('Segoe UI', 8),
                          bg=COLORS['bg_panel'], fg=COLORS['text_muted'])
progress_label.pack()
S.progress_var = progress_var
S.progress_label = progress_label

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

# Initial button states - disable detection buttons until image is loaded
btn_annotate["state"] = "disabled"
btn_save["state"] = "disabled"
btn_line_detect["state"] = "disabled"
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
S.btn_line_annotate = btn_line_annotate
S.btn_char_annotate = btn_char_annotate
S.scale_slider = scale_slider
S.padding_slider = padding_slider
S.btn_line_detect = btn_line_detect


# ============================================
# MAIN CONTENT AREA - Input Text + Image Preview
# ============================================

# Create main content frame with two sections
content_frame = tk.Frame(txt_edit, bg=COLORS['bg_dark'], padx=20, pady=20)
content_frame.pack(expand=True, fill=tk.BOTH)

# Top section: Input Text Area
input_section = tk.LabelFrame(content_frame, text=" 📝 Input Text (ASCII Transcription) ", 
                               font=('Segoe UI', 11, 'bold'),
                               bg=COLORS['bg_section'], fg=COLORS['text_light'],
                               relief=tk.FLAT, bd=2, padx=10, pady=10)
input_section.pack(fill=tk.X, pady=(0, 10))

# Text input with scrollbar
text_frame = tk.Frame(input_section, bg=COLORS['bg_section'])
text_frame.pack(fill=tk.X)

input_text_area = tk.Text(text_frame, width=80, height=6, font=('Consolas', 11),
                          bg='white', fg='black', insertbackground='black',
                          wrap=tk.WORD)
input_text_area.pack(side=tk.LEFT, fill=tk.X, expand=True)

text_scroll = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=input_text_area.yview)
text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
input_text_area.config(yscrollcommand=text_scroll.set)

# Character count and RTL toggle
text_info_frame = tk.Frame(input_section, bg=COLORS['bg_section'])
text_info_frame.pack(fill=tk.X, pady=(5, 0))

char_count_var = tk.StringVar(value="Characters: 0 | Words: 0 | Lines: 0")
char_count_label = tk.Label(text_info_frame, textvariable=char_count_var, 
                            font=('Segoe UI', 9), bg=COLORS['bg_section'], fg=COLORS['text_muted'])
char_count_label.pack(side=tk.LEFT)

# Update character count on text change
def update_text_stats(event=None):
    content = input_text_area.get("1.0", "end-1c")
    chars = len(content)
    words = len(content.split()) if content.strip() else 0
    lines = len(content.splitlines()) if content.strip() else 0
    char_count_var.set(f"Characters: {chars} | Words: {words} | Lines: {lines}")
    # Store in state for annotation use
    S.input_text = content
    S.gan_input_text = content

input_text_area.bind('<KeyRelease>', update_text_stats)
input_text_area.bind('<<Paste>>', lambda e: window.after(1, update_text_stats))
input_text_area.bind('<<Cut>>', lambda e: window.after(1, update_text_stats))

# Store input text area in state
S.input_text_area = input_text_area
S.input_text = ""

# Bottom section: Image Preview
preview_section = tk.LabelFrame(content_frame, text=" 🖼️ Image Preview ", 
                                 font=('Segoe UI', 11, 'bold'),
                                 bg=COLORS['bg_section'], fg=COLORS['text_light'],
                                 relief=tk.FLAT, bd=2, padx=10, pady=10)
preview_section.pack(fill=tk.BOTH, expand=True)

# Create canvas for image preview with scrollbars
preview_canvas_frame = tk.Frame(preview_section, bg=COLORS['bg_section'])
preview_canvas_frame.pack(fill=tk.BOTH, expand=True)

preview_v_scroll = tk.Scrollbar(preview_canvas_frame, orient=tk.VERTICAL)
preview_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

preview_h_scroll = tk.Scrollbar(preview_canvas_frame, orient=tk.HORIZONTAL)
preview_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

preview_canvas = tk.Canvas(preview_canvas_frame, bg='#2c3e50', 
                           xscrollcommand=preview_h_scroll.set,
                           yscrollcommand=preview_v_scroll.set,
                           width=700, height=400)
preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

preview_v_scroll.config(command=preview_canvas.yview)
preview_h_scroll.config(command=preview_canvas.xview)

# Initial placeholder text on canvas
preview_canvas.create_text(350, 200, text="No image loaded\n\n1. Open Folder to load handwriting images\n   OR\n2. Generate HTR to create synthetic images\n\n3. Enter corresponding text in the input area above\n4. Click 'Detect Lines' or 'Detect Words'",
                           fill='#7f8c8d', font=('Segoe UI', 12), justify=tk.CENTER)

S.preview_canvas = preview_canvas
S.current_preview_image = None

# Function to update preview image
def update_preview_image(image_path=None, pil_image=None):
    """Update the preview canvas with an image."""
    preview_canvas.delete('all')
    
    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path)
        except Exception as e:
            preview_canvas.create_text(350, 200, text=f"Error loading image:\n{e}", 
                                       fill='red', font=('Segoe UI', 11))
            return
    elif pil_image:
        img = pil_image
    else:
        preview_canvas.create_text(350, 200, text="No image to display", 
                                   fill='#7f8c8d', font=('Segoe UI', 12))
        return
    
    # Resize to fit canvas while maintaining aspect ratio
    canvas_w, canvas_h = 700, 400
    img_w, img_h = img.size
    scale = min(canvas_w / img_w, canvas_h / img_h, 1.5)
    new_w, new_h = int(img_w * scale), int(img_h * scale)
    
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)
    S.current_preview_image = ImageTk.PhotoImage(img_resized)
    
    # Center image on canvas
    x_offset = max(0, (canvas_w - new_w) // 2)
    y_offset = max(0, (canvas_h - new_h) // 2)
    
    preview_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=S.current_preview_image)
    preview_canvas.config(scrollregion=(0, 0, max(canvas_w, new_w), max(canvas_h, new_h)))
    
    # Store original image path
    S.current_image_path = image_path

S.update_preview_image = update_preview_image

# Navigation buttons for multiple images
nav_frame = tk.Frame(preview_section, bg=COLORS['bg_section'])
nav_frame.pack(fill=tk.X, pady=(5, 0))

def prev_image():
    if S.list_of_files and S.pos > 0:
        S.pos -= 1
        update_preview_image(S.list_of_files[S.pos])
        update_status(f"Image {S.pos + 1} of {len(S.list_of_files)}")

def next_image():
    if S.list_of_files and S.pos < len(S.list_of_files) - 1:
        S.pos += 1
        update_preview_image(S.list_of_files[S.pos])
        update_status(f"Image {S.pos + 1} of {len(S.list_of_files)}")

btn_prev_img = tk.Button(nav_frame, text="◀ Previous", command=prev_image,
                         bg=COLORS['accent'], fg='white', font=('Segoe UI', 9))
btn_prev_img.pack(side=tk.LEFT, padx=2)

btn_next_img = tk.Button(nav_frame, text="Next ▶", command=next_image,
                         bg=COLORS['accent'], fg='white', font=('Segoe UI', 9))
btn_next_img.pack(side=tk.LEFT, padx=2)

image_info_var = tk.StringVar(value="No images loaded")
image_info_label = tk.Label(nav_frame, textvariable=image_info_var,
                            font=('Segoe UI', 9), bg=COLORS['bg_section'], fg=COLORS['text_muted'])
image_info_label.pack(side=tk.LEFT, padx=20)

S.image_info_var = image_info_var
S.btn_prev_img = btn_prev_img
S.btn_next_img = btn_next_img

# Create a dummy label for backward compatibility
label = tk.Label(content_frame)
S.label = label

# ============================================
# KEYBOARD SHORTCUTS
# ============================================
def setup_keyboard_shortcuts():
    """Setup global keyboard shortcuts for the application."""
    
    def on_ctrl_o(event):
        """Ctrl+O: Open folder"""
        if S.shortcuts_enabled and btn_open['state'] != 'disabled':
            init_pathandfolders()
            return 'break'
    
    def on_ctrl_s(event):
        """Ctrl+S: Save/Detect words"""
        if S.shortcuts_enabled and btn_save['state'] != 'disabled':
            save_file()
            return 'break'
    
    def on_ctrl_g(event):
        """Ctrl+G: Generate HTR"""
        if S.shortcuts_enabled:
            generate_htr()
            return 'break'
    
    def on_ctrl_a(event):
        """Ctrl+A: Word annotation"""
        if S.shortcuts_enabled and btn_annotate['state'] != 'disabled':
            annotate()
            return 'break'
    
    def on_ctrl_l(event):
        """Ctrl+L: Line annotation"""
        if S.shortcuts_enabled:
            from actions.line_annotate import line_annotate
            line_annotate()
            return 'break'
    
    def on_ctrl_k(event):
        """Ctrl+K: Character annotation"""
        if S.shortcuts_enabled:
            character_annotate()
            return 'break'
    
    def on_f1(event):
        """F1: Show keyboard shortcuts help"""
        shortcuts_help = """
        ⌨️ Keyboard Shortcuts:
        
        Ctrl+O  →  Open folder
        Ctrl+S  →  Detect words / Save
        Ctrl+G  →  Generate HTR
        Ctrl+A  →  Word annotation
        Ctrl+L  →  Line annotation
        Ctrl+K  →  Character annotation
        F1      →  Show this help
        Escape  →  Close popup windows
        """
        from tkinter import messagebox
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_help)
        return 'break'
    
    def on_escape(event):
        """Escape: Close popup windows"""
        if S.r:
            try:
                S.r.destroy()
                S.r = None
            except:
                pass
        return 'break'
    
    # Bind shortcuts to main window
    window.bind('<Control-o>', on_ctrl_o)
    window.bind('<Control-O>', on_ctrl_o)
    window.bind('<Control-s>', on_ctrl_s)
    window.bind('<Control-S>', on_ctrl_s)
    window.bind('<Control-g>', on_ctrl_g)
    window.bind('<Control-G>', on_ctrl_g)
    window.bind('<Control-a>', on_ctrl_a)
    window.bind('<Control-A>', on_ctrl_a)
    window.bind('<Control-l>', on_ctrl_l)
    window.bind('<Control-L>', on_ctrl_l)
    window.bind('<Control-k>', on_ctrl_k)
    window.bind('<Control-K>', on_ctrl_k)
    window.bind('<F1>', on_f1)
    window.bind('<Escape>', on_escape)
    
    print("Keyboard shortcuts enabled. Press F1 for help.")

# Setup shortcuts
setup_keyboard_shortcuts()

# ============================================
# AUTO-SAVE FUNCTIONALITY
# ============================================
import json
from datetime import datetime

def auto_save():
    """Auto-save current state periodically."""
    if not S.auto_save_enabled:
        window.after(S.auto_save_interval, auto_save)
        return
    
    try:
        # Save state to JSON file
        state_file = os.path.join(os.path.dirname(__file__), 'autosave_state.json')
        state_data = {
            'timestamp': datetime.now().isoformat(),
            'pos': S.pos,
            'nbr': S.nbr,
            'nbrout': S.nbrout,
            'ind2': S.ind2,
            'text_direction': S.text_direction,
            'export_format': S.export_format,
            'image_scale': S.image_scale,
            'bbox_padding': S.bbox_padding,
        }
        
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
        
        S.last_save_time = datetime.now()
        if progress_label:
            progress_label.config(text=f"Auto-saved: {S.last_save_time.strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"Auto-save failed: {e}")
    
    # Schedule next auto-save
    window.after(S.auto_save_interval, auto_save)

# Start auto-save timer
window.after(S.auto_save_interval, auto_save)

# ============================================
# PROGRESS HELPER FUNCTIONS
# ============================================
def show_progress(value, message=""):
    """Update progress bar and label."""
    if S.progress_var:
        S.progress_var.set(value)
    if S.progress_label:
        S.progress_label.config(text=message)
    window.update_idletasks()

def reset_progress():
    """Reset progress bar."""
    show_progress(0, "")

# Export progress functions to state
S.show_progress = show_progress
S.reset_progress = reset_progress

# Show startup message
update_status("Ready | Press F1 for shortcuts")
        
window.mainloop()
