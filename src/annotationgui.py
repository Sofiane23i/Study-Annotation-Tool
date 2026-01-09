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
S.segmentation_mode = None
S.auto_detect_on_navigation = False
    
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
window.configure(bg='#f7f9fc')
# Open in full-screen (maximized) for better workspace
try:
    window.state('zoomed')
except Exception:
    pass

# Define a simple two-tone palette (light base + blue accent)
COLORS = {
    'bg_dark': '#f4f7fb',       # main background
    'bg_panel': '#ffffff',      # panels/cards
    'bg_section': '#ffffff',    # sections inside panels
    'accent': '#6cb6ff',        # light blue accent
    'accent_hover': '#4f8fe6',
    'success': '#6cb6ff',       # keep within blue family
    'warning': '#6cb6ff',       # keep within blue family
    'danger': '#6cb6ff',        # keep within blue family
    'text_light': '#0f172a',
    'text_muted': '#60708a',
    'border': '#e5e7eb',
    'secondary_bg': '#e8f1fb',
    'secondary_hover': '#d8e8f8'
}

# Custom button style function
def create_styled_button(parent, text, command=None, style='normal', width=18):
    colors = {
        'normal': (COLORS['accent'], COLORS['accent_hover'], 'white'),
        'success': (COLORS['accent'], COLORS['accent_hover'], 'white'),
        'warning': (COLORS['accent'], COLORS['accent_hover'], 'white'),
        'danger': (COLORS['accent'], COLORS['accent_hover'], 'white'),
        'secondary': (COLORS['secondary_bg'], COLORS['secondary_hover'], COLORS['text_light'])
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

# Section 1: Input Mode Toggle
section1 = tk.LabelFrame(fr_buttons, text=" 📂 Input Mode ", font=('Segoe UI', 10, 'bold'),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], 
                         relief=tk.FLAT, bd=1, padx=10, pady=10)
section1.pack(fill=tk.X, pady=(0, 10))

# Mode toggle variable
input_mode_var = tk.StringVar(value="load")  # "load" or "generate"
segmentation_mode_var = tk.StringVar(value="Segmentation mode: not chosen")

# Toggle button frame
toggle_frame = tk.Frame(section1, bg=COLORS['bg_section'])
toggle_frame.pack(fill=tk.X, pady=6, padx=4)

mode_status = tk.Label(section1, textvariable=segmentation_mode_var,
                       font=('Segoe UI', 9), anchor='w', justify='left',
                       bg=COLORS['bg_section'], fg=COLORS['text_muted'])
mode_status.pack(fill=tk.X, pady=(4, 0))
S.segmentation_mode_var = segmentation_mode_var

def widget_exists(widget):
    """Check if a tkinter widget still exists."""
    try:
        return widget is not None and widget.winfo_exists()
    except:
        return False


def images_available():
    """Return True if a folder is loaded or GAN images exist."""
    has_loaded = hasattr(S, 'list_of_files') and S.list_of_files
    has_gan = getattr(S, 'gan_generated_ready', False) and getattr(S, 'gan_batch_images', [])
    return bool(has_loaded or has_gan)


def ensure_images_available():
    """Guard actions that require images; show guidance if none."""
    if images_available():
        return True
    from tkinter import messagebox
    messagebox.showinfo(
        "No images available",
        "Load an image folder or generate HTR images before using detection or annotation."
    )
    return False

# Segmentation mode helpers
def set_segmentation_mode(mode):
    """Lock segmentation mode after first choice (line or word)."""
    if not hasattr(S, 'segmentation_mode') or S.segmentation_mode is None:
        S.segmentation_mode = mode
        if mode == 'line':
            if widget_exists(btn_save):
                btn_save.config(state='disabled')
            if widget_exists(btn_line_detect):
                btn_line_detect.config(state='normal')
            if widget_exists(btn_annotate):
                btn_annotate.config(state='disabled')
            if widget_exists(btn_line_annotate):
                btn_line_annotate.config(state='normal')
        elif mode == 'word':
            if widget_exists(btn_line_detect):
                btn_line_detect.config(state='disabled')
            if widget_exists(btn_save):
                btn_save.config(state='normal')
            if widget_exists(btn_line_annotate):
                btn_line_annotate.config(state='disabled')
            if widget_exists(btn_annotate):
                btn_annotate.config(state='normal')
        segmentation_mode_var.set(f"Segmentation mode: {mode.title()} (locked for remaining images)")
        S.auto_detect_on_navigation = True
    elif S.segmentation_mode != mode:
        from tkinter import messagebox
        messagebox.showinfo("Segmentation Mode Locked",
                            f"You chose {S.segmentation_mode} segmentation for the first image."
                            " The same mode will be used for all images.")
        return False
    return True

def switch_to_load_mode():
    input_mode_var.set("load")
    btn_mode_load.config(bg=COLORS['accent'], fg='white', relief=tk.SUNKEN)
    btn_mode_generate.config(bg=COLORS['bg_section'], fg=COLORS['text_light'], relief=tk.RAISED)
    # Show load interface, hide generate interface
    try:
        if widget_exists(S.word_detect_container):
            S.word_detect_container.pack_forget()
        if widget_exists(S.generate_htr_container):
            S.generate_htr_container.pack_forget()
        if widget_exists(S.load_image_container):
            S.load_image_container.pack(expand=True, fill=tk.BOTH)
        # Show load placeholder or current load image; do not surface GAN preview in load mode
        if hasattr(S, 'show_preview_placeholder'):
            S.show_preview_placeholder(DEFAULT_PREVIEW_TEXT)
        # Reset segmentation choice when returning to load mode
        S.segmentation_mode = None
        S.auto_detect_on_navigation = False
        segmentation_mode_var.set("Segmentation mode: not chosen")
        if hasattr(S, 'list_of_files') and S.list_of_files:
            if S.pos < 0 or S.pos >= len(S.list_of_files):
                S.pos = 0
            if hasattr(S, 'update_preview_image'):
                S.update_preview_image(S.list_of_files[S.pos])
            if hasattr(S, 'image_info_var'):
                S.image_info_var.set(f"Image {S.pos + 1} of {len(S.list_of_files)}")
        elif hasattr(S, 'image_info_var'):
            S.image_info_var.set("No images loaded")
        if hasattr(S, 'update_detection_visibility'):
            S.update_detection_visibility()
    except Exception as e:
        print(f"Error in switch_to_load_mode: {e}")

def switch_to_generate_mode():
    input_mode_var.set("generate")
    btn_mode_generate.config(bg=COLORS['success'], fg='white', relief=tk.SUNKEN)
    btn_mode_load.config(bg=COLORS['bg_section'], fg=COLORS['text_light'], relief=tk.RAISED)
    # Show generate interface, hide load interface
    try:
        if widget_exists(S.load_image_container):
            S.load_image_container.pack_forget()
        if widget_exists(S.generate_htr_container):
            S.generate_htr_container.pack(expand=True, fill=tk.BOTH)
        # Keep GAN preview if it exists; otherwise show generate placeholder
        if hasattr(S, 'show_preview_placeholder'):
            if getattr(S, 'gan_generated_ready', False) and getattr(S, 'gan_batch_images', []):
                idx = min(max(getattr(S, 'gan_batch_index', 0), 0), len(S.gan_batch_images) - 1)
                path = S.gan_batch_images[idx]
                if hasattr(S, 'update_preview_image') and path:
                    S.update_preview_image(path)
            else:
                S.show_preview_placeholder(GENERATE_PREVIEW_TEXT)
        if hasattr(S, 'image_info_var'):
            if getattr(S, 'gan_generated_ready', False) and getattr(S, 'gan_batch_images', []):
                S.image_info_var.set("Generate mode: preview ready")
            else:
                S.image_info_var.set("Generate mode: waiting for output")
        S.segmentation_mode = None
        S.auto_detect_on_navigation = False
        segmentation_mode_var.set("Segmentation mode: not chosen")
        # Build the HTR interface inside the container
        generate_htr()
        if hasattr(S, 'update_detection_visibility'):
            S.update_detection_visibility()
    except Exception as e:
        print(f"Error in switch_to_generate_mode: {e}")

btn_mode_load = tk.Button(toggle_frame, text="📁 Load Image", 
                          command=switch_to_load_mode,
                          bg=COLORS['accent'], fg='white',
                          font=('Segoe UI', 9, 'bold'),
                          relief=tk.SUNKEN, bd=1, padx=12, pady=7)
btn_mode_load.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

btn_mode_generate = tk.Button(toggle_frame, text="✍️ Generate HTR", 
                              command=switch_to_generate_mode,
                              bg=COLORS['bg_section'], fg=COLORS['text_light'],
                              font=('Segoe UI', 9, 'bold'),
                              relief=tk.RAISED, bd=1, padx=12, pady=7)
btn_mode_generate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

# Store for backward compatibility
btn_open = btn_mode_load
btn_htr = btn_mode_generate

# ============================================
# LINE DETECTION FUNCTION
# ============================================
def disable_other_detection_buttons(selected_mode):
    """Disable detection buttons for modes other than the selected one."""
    if selected_mode == 'line':
        if widget_exists(btn_save):
            btn_save.config(state='disabled')
        if widget_exists(btn_annotate):
            btn_annotate.config(state='disabled')
        if widget_exists(btn_char_detect):
            btn_char_detect.config(state='disabled')
        if widget_exists(btn_char_annotate):
            btn_char_annotate.config(state='disabled')
    elif selected_mode == 'word':
        if widget_exists(btn_line_detect):
            btn_line_detect.config(state='disabled')
        if widget_exists(btn_line_annotate):
            btn_line_annotate.config(state='disabled')
        if widget_exists(btn_char_detect):
            btn_char_detect.config(state='disabled')
        if widget_exists(btn_char_annotate):
            btn_char_annotate.config(state='disabled')
    elif selected_mode == 'character':
        if widget_exists(btn_line_detect):
            btn_line_detect.config(state='disabled')
        if widget_exists(btn_line_annotate):
            btn_line_annotate.config(state='disabled')
        if widget_exists(btn_save):
            btn_save.config(state='disabled')
        if widget_exists(btn_annotate):
            btn_annotate.config(state='disabled')

def detect_lines_with_autofill():
    """
    Detect text lines in the current image and display them in the right panel.
    """
    from tkinter import messagebox

    if not ensure_images_available():
        return
    
    # Lock segmentation mode to line on first use
    if not set_segmentation_mode('line'):
        return
    
    # Disable other detection buttons
    disable_other_detection_buttons('line')

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
        
        # Store detected lines and image path for annotation
        S.detected_lines = lines
        S.line_image_path = image_path
        S.line_input_text = input_text
        
        # Switch to line detection view
        if widget_exists(S.load_image_container):
            S.load_image_container.pack_forget()
        if widget_exists(S.word_detect_container):
            S.word_detect_container.pack_forget()
        if widget_exists(S.annotation_container):
            S.annotation_container.pack_forget()
        if widget_exists(S.line_detect_container):
            S.line_detect_container.pack(expand=True, fill=tk.BOTH)
        
        # Draw lines on canvas
        display_detected_lines(img, lines)
        
        if hasattr(S, 'update_status') and S.update_status:
            S.update_status(f"Detected {len(lines)} lines")

        # Enable line annotation button
        if widget_exists(btn_line_annotate):
            btn_line_annotate.config(state='normal')
        if widget_exists(btn_annotate):
            btn_annotate.config(state='disabled')
        
    except Exception as e:
        messagebox.showerror("Error", f"Line detection failed:\n{str(e)}")
        import traceback
        traceback.print_exc()

def display_detected_lines(img, lines):
    """Display image with detected lines on the line detection canvas."""
    if not hasattr(S, 'line_detect_canvas'):
        return
    
    canvas = S.line_detect_canvas
    canvas.delete('all')
    
    # Draw image with line boxes
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_with_lines = img_rgb.copy()
    
    # Draw rectangles around detected lines
    for i, (y_start, y_end) in enumerate(lines):
        cv2.rectangle(img_with_lines, (0, y_start), (img.shape[1], y_end), (30, 144, 255), 2)
        cv2.putText(img_with_lines, f"Line {i+1}", (5, y_start + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 144, 255), 2)
    
    # Resize for display
    h, w = img_with_lines.shape[:2]
    canvas_w, canvas_h = 800, 600
    scale = min(canvas_w / w, canvas_h / h, 1.0)
    new_w, new_h = int(w * scale), int(h * scale)
    
    img_resized = cv2.resize(img_with_lines, (new_w, new_h), interpolation=cv2.INTER_AREA)
    pil_img = Image.fromarray(img_resized)
    S.line_detect_photo = ImageTk.PhotoImage(pil_img)
    
    # Center on canvas
    x_offset = (canvas_w - new_w) // 2
    y_offset = (canvas_h - new_h) // 2
    canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=S.line_detect_photo)
    
    # Update info label
    if hasattr(S, 'line_info_label'):
        S.line_info_label.config(text=f"Detected {len(lines)} lines - Click 'Proceed to Annotation' to annotate each line")

# Section 2: Detection
section2 = tk.LabelFrame(fr_buttons, text=" 🔍 Detection ", font=('Segoe UI', 10, 'bold'),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], 
                         relief=tk.FLAT, bd=1, padx=10, pady=10)
section2.pack(fill=tk.X, pady=(0, 10))

# Line detection row
line_row = tk.Frame(section2, bg=COLORS['bg_section'])
line_row.pack(fill=tk.X, pady=3)
btn_line_detect = create_styled_button(line_row, "📄 Detect Lines", detect_lines_with_autofill, 'warning', width=9)
btn_line_detect.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

from actions.line_annotate import line_annotate
def annotate_lines_and_advance():
    if not ensure_images_available():
        return
    if not set_segmentation_mode('line'):
        return
    if widget_exists(S.word_detect_container):
        S.word_detect_container.pack_forget()
    if widget_exists(S.load_image_container):
        S.load_image_container.pack_forget()
    if widget_exists(S.annotation_container):
        S.annotation_container.pack(expand=True, fill=tk.BOTH)
    line_annotate()

btn_line_annotate = create_styled_button(line_row, "📄 Annotate", annotate_lines_and_advance, 'success', width=9)
btn_line_annotate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
btn_line_annotate.config(state='disabled')

def detect_words_with_mode_lock():
    if not set_segmentation_mode('word'):
        return
    if not ensure_images_available():
        return
    
    # Disable other detection buttons
    disable_other_detection_buttons('word')
    
    # Require either loaded images or generated GAN previews before showing detection
    has_loaded_images = hasattr(S, 'list_of_files') and S.list_of_files
    has_gan_images = getattr(S, 'gan_generated_ready', False) and getattr(S, 'gan_batch_images', [])
    if not (has_loaded_images or has_gan_images):
        from tkinter import messagebox
        messagebox.showinfo("No images available", "Load an image folder or generate HTR images before word detection.")
        return
    # Swap to word-detection view
    if widget_exists(S.annotation_container):
        S.annotation_container.pack_forget()
    if widget_exists(S.load_image_container):
        S.load_image_container.pack_forget()
    if widget_exists(S.word_detect_container):
        S.word_detect_container.pack(expand=True, fill=tk.BOTH)
    save_file()
    if widget_exists(btn_annotate):
        btn_annotate.config(state='normal')
    if widget_exists(btn_line_annotate):
        btn_line_annotate.config(state='disabled')

# Word detection row
word_row = tk.Frame(section2, bg=COLORS['bg_section'])
word_row.pack(fill=tk.X, pady=3)
btn_save = create_styled_button(word_row, "🎯 Detect Words", detect_words_with_mode_lock, 'warning', width=9)
btn_save.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

def annotate_words_and_advance():
    if not ensure_images_available():
        return
    if not set_segmentation_mode('word'):
        return
    if widget_exists(S.word_detect_container):
        S.word_detect_container.pack_forget()
    if widget_exists(S.load_image_container):
        S.load_image_container.pack_forget()
    if widget_exists(S.annotation_container):
        S.annotation_container.pack(expand=True, fill=tk.BOTH)
    annotate()

btn_annotate = create_styled_button(word_row, "📝 Annotate", annotate_words_and_advance, 'success', width=9)
btn_annotate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
btn_annotate.config(state='disabled')

def detect_characters():
    """Open character-level annotation/detection flow."""
    if not ensure_images_available():
        return
    
    # Disable other detection buttons
    disable_other_detection_buttons('character')
    
    character_annotate()

# Character detection row
char_row = tk.Frame(section2, bg=COLORS['bg_section'])
char_row.pack(fill=tk.X, pady=3)
btn_char_detect = create_styled_button(char_row, "🔤 Detect Chars", detect_characters, 'warning', width=9)
btn_char_detect.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

from actions.character_annotate import character_annotate
def annotate_characters_with_save():
    if not ensure_images_available():
        return
    character_annotate()

btn_char_annotate = create_styled_button(char_row, "🔤 Annotate", annotate_characters_with_save, 'success', width=9)
btn_char_annotate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

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


def update_detection_visibility():
    """Show/hide detection controls based on image availability."""
    try:
        available = images_available()
        if available:
            btn_line_detect.config(state='normal')
            btn_save.config(state='normal')
            btn_char_detect.config(state='normal')
            scale_slider.config(state='normal')
            padding_slider.config(state='normal')
        else:
            btn_line_detect.config(state='disabled')
            btn_save.config(state='disabled')
            btn_char_detect.config(state='disabled')
            scale_slider.config(state='disabled')
            padding_slider.config(state='disabled')
        # ensure frame is packed
        if not section2.winfo_manager():
            section2.pack(fill=tk.X, pady=(0, 10))
    except Exception as e:
        print(f"update_detection_visibility error: {e}")

def auto_next_after_annotation():
    """Move to next image and auto-run detection for the locked mode."""
    try:
        next_image()
        if hasattr(S, 'auto_detect_on_navigation') and S.auto_detect_on_navigation:
            if getattr(S, 'segmentation_mode', None) == 'word':
                detect_words_with_mode_lock()
            elif getattr(S, 'segmentation_mode', None) == 'line':
                detect_lines_with_autofill()
    except Exception:
        pass

    # Ensure detection visibility tracked in shared state
    S.update_detection_visibility = update_detection_visibility

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
btn_char_detect["state"] = "disabled"
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
S.btn_char_detect = btn_char_detect
S.scale_slider = scale_slider
S.padding_slider = padding_slider
S.btn_line_detect = btn_line_detect

# Initialize detection visibility at startup
if hasattr(S, 'update_detection_visibility'):
    S.update_detection_visibility()


# ============================================
# MAIN CONTENT AREA - Two switchable interfaces
# ============================================

# Create main content frame
content_frame = tk.Frame(txt_edit, bg=COLORS['bg_dark'], padx=20, pady=20)
content_frame.pack(expand=True, fill=tk.BOTH)

# ============================================
# CONTAINER 1: Load Image Interface
# ============================================
load_image_container = tk.Frame(content_frame, bg=COLORS['bg_dark'])
load_image_container.pack(expand=True, fill=tk.BOTH)

# ============================================
# CONTAINER 2: Word Detection Review (hidden until word detect)
# ============================================
word_detect_container = tk.Frame(content_frame, bg=COLORS['bg_dark'])
word_detect_container.pack_forget()

word_detect_header = tk.Label(word_detect_container, text=" 🧠 Word Detection Review ",
                              font=('Segoe UI', 12, 'bold'),
                              bg=COLORS['bg_section'], fg=COLORS['text_light'],
                              relief=tk.FLAT, bd=1, padx=10, pady=8)
word_detect_header.pack(fill=tk.X, pady=(0, 10))

word_canvas = tk.Canvas(word_detect_container, width=800, height=600,
                        bg='#eef2f7', highlightthickness=1, highlightbackground=COLORS['border'])
word_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

word_btn_frame = tk.Frame(word_detect_container, bg=COLORS['bg_dark'])
word_btn_frame.pack(fill=tk.X, pady=(8, 0))

def back_to_image_view():
    if widget_exists(word_detect_container):
        word_detect_container.pack_forget()
    if widget_exists(load_image_container):
        load_image_container.pack(expand=True, fill=tk.BOTH)

def proceed_to_annotation_from_word_panel():
    if hasattr(S, 'perform_cropping_current_detection'):
        S.perform_cropping_current_detection()
    if widget_exists(S.word_detect_container):
        S.word_detect_container.pack_forget()
    if widget_exists(S.load_image_container):
        S.load_image_container.pack_forget()
    if widget_exists(S.annotation_container):
        S.annotation_container.pack(expand=True, fill=tk.BOTH)
    annotate()

btn_back_view = tk.Button(word_btn_frame, text="⬅ Back to image view", command=back_to_image_view,
                          bg=COLORS['bg_section'], fg=COLORS['text_light'], padx=10, pady=6)
btn_back_view.pack(side=tk.LEFT, padx=4)

btn_proceed_annotation = tk.Button(word_btn_frame, text="Proceed to annotation", command=proceed_to_annotation_from_word_panel,
                                   bg=COLORS['accent'], fg='white', padx=12, pady=6)
btn_proceed_annotation.pack(side=tk.RIGHT, padx=4)

# store in state for detection rendering
S.word_detect_container = word_detect_container
S.word_detect_canvas = word_canvas

# ============================================
# CONTAINER 2b: Line Detection Review (hidden until line detect)
# ============================================
line_detect_container = tk.Frame(content_frame, bg=COLORS['bg_dark'])
line_detect_container.pack_forget()

line_detect_header = tk.Label(line_detect_container, text=" 📄 Line Detection Review ",
                              font=('Segoe UI', 12, 'bold'),
                              bg=COLORS['bg_section'], fg=COLORS['text_light'],
                              relief=tk.FLAT, bd=1, padx=10, pady=8)
line_detect_header.pack(fill=tk.X, pady=(0, 10))

line_canvas = tk.Canvas(line_detect_container, width=800, height=600,
                        bg='#eef2f7', highlightthickness=1, highlightbackground=COLORS['border'])
line_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

line_info_label = tk.Label(line_detect_container, text="",
                           font=('Segoe UI', 10), bg=COLORS['bg_dark'], fg=COLORS['text_light'])
line_info_label.pack(fill=tk.X, pady=(4, 0))

line_btn_frame = tk.Frame(line_detect_container, bg=COLORS['bg_dark'])
line_btn_frame.pack(fill=tk.X, pady=(8, 0))

def back_to_image_view_from_line():
    if widget_exists(line_detect_container):
        line_detect_container.pack_forget()
    if widget_exists(load_image_container):
        load_image_container.pack(expand=True, fill=tk.BOTH)

def proceed_to_line_annotation():
    """Start line-by-line annotation in the annotation panel."""
    if widget_exists(S.line_detect_container):
        S.line_detect_container.pack_forget()
    if widget_exists(S.load_image_container):
        S.load_image_container.pack_forget()
    if widget_exists(S.annotation_container):
        S.annotation_container.pack(expand=True, fill=tk.BOTH)
    
    # Start line annotation with detected lines
    from actions.line_annotate import start_embedded_line_annotation
    if hasattr(S, 'detected_lines') and hasattr(S, 'line_image_path'):
        text_lines = S.line_input_text.splitlines() if hasattr(S, 'line_input_text') and S.line_input_text else []
        start_embedded_line_annotation(S.line_image_path, S.detected_lines, text_lines)

btn_back_line_view = tk.Button(line_btn_frame, text="⬅ Back to image view", command=back_to_image_view_from_line,
                          bg=COLORS['bg_section'], fg=COLORS['text_light'], padx=10, pady=6)
btn_back_line_view.pack(side=tk.LEFT, padx=4)

btn_proceed_line_annotation = tk.Button(line_btn_frame, text="Proceed to annotation", command=proceed_to_line_annotation,
                                   bg=COLORS['accent'], fg='white', padx=12, pady=6)
btn_proceed_line_annotation.pack(side=tk.RIGHT, padx=4)

# store in state for line detection rendering
S.line_detect_container = line_detect_container
S.line_detect_canvas = line_canvas
S.line_info_label = line_info_label

# ============================================
# CONTAINER 3: Annotation Interface (hidden until annotation)
# ============================================
annotation_container = tk.Frame(content_frame, bg=COLORS['bg_dark'])
annotation_container.pack_forget()

annotation_header = tk.Label(annotation_container, text=" 📝 Annotation ",
                              font=('Segoe UI', 12, 'bold'),
                              bg=COLORS['bg_section'], fg=COLORS['text_light'],
                              relief=tk.FLAT, bd=1, padx=10, pady=8)
annotation_header.pack(fill=tk.X, pady=(0, 10))

annotation_body = tk.Frame(annotation_container, bg=COLORS['bg_dark'])
annotation_body.pack(expand=True, fill=tk.BOTH)

S.annotation_container = annotation_container
S.annotation_body = annotation_body

# Load Image Folder Section
load_image_frame = tk.LabelFrame(load_image_container, text=" 📂 Load Image Folder ", 
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=COLORS['bg_section'], fg=COLORS['text_light'],
                                  relief=tk.FLAT, bd=2, padx=10, pady=10)
load_image_frame.pack(fill=tk.X, pady=(0, 10))

load_inner_frame = tk.Frame(load_image_frame, bg=COLORS['bg_section'])
load_inner_frame.pack(fill=tk.X)

# Folder path display
folder_path_var = tk.StringVar(value="No folder selected")
folder_path_label = tk.Label(load_inner_frame, textvariable=folder_path_var,
                             font=('Consolas', 10), bg='white', fg='#333',
                             anchor='w', padx=10, pady=5, relief=tk.SUNKEN)
folder_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

def load_image_folder_action():
    """Load images from a folder and update the display."""
    init_pathandfolders()
    # Update folder path display
    if S.pathDirectory:
        folder_path_var.set(S.pathDirectory)
    if S.list_of_files:
        folder_info_var.set(f"Found {len(S.list_of_files)} images")
    if hasattr(S, 'update_detection_visibility'):
        S.update_detection_visibility()

btn_load_folder = tk.Button(load_inner_frame, text="📁 Browse Folder",
                            command=load_image_folder_action,
                            bg=COLORS['accent'], fg='white',
                            font=('Segoe UI', 10, 'bold'),
                            padx=15, pady=5)
btn_load_folder.pack(side=tk.RIGHT)

# Folder info
folder_info_var = tk.StringVar(value="Select a folder containing handwriting images")
folder_info_label = tk.Label(load_image_frame, textvariable=folder_info_var,
                             font=('Segoe UI', 9), bg=COLORS['bg_section'], 
                             fg=COLORS['text_muted'])
folder_info_label.pack(anchor='w', pady=(5, 0))

S.load_image_frame = load_image_frame
S.folder_path_var = folder_path_var
S.folder_info_var = folder_info_var
S.load_image_container = load_image_container

# Top section: Input Text Area (inside load_image_container)
input_section = tk.LabelFrame(load_image_container, text=" 📝 Input Text (ASCII Transcription) ", 
                               font=('Segoe UI', 11, 'bold'),
                               bg=COLORS['bg_section'], fg=COLORS['text_light'],
                               relief=tk.FLAT, bd=2, padx=10, pady=10)
input_section.pack(fill=tk.X, pady=(0, 10))

# Store input_section in state for the toggle functions
S.input_section = input_section

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

# Bottom section: Image Preview (inside load_image_container)
preview_section = tk.LabelFrame(load_image_container, text=" 🖼️ Image Preview ", 
                                 font=('Segoe UI', 11, 'bold'),
                                 bg=COLORS['bg_section'], fg=COLORS['text_light'],
                                 relief=tk.FLAT, bd=2, padx=12, pady=12)
preview_section.pack(fill=tk.BOTH, expand=True, pady=(4, 0), padx=2)

# Store preview_section in state for the toggle functions
S.preview_section = preview_section

# Create canvas for image preview with scrollbars
preview_canvas_frame = tk.Frame(preview_section, bg=COLORS['bg_section'])
preview_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 6))

preview_v_scroll = tk.Scrollbar(preview_canvas_frame, orient=tk.VERTICAL)
preview_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

preview_h_scroll = tk.Scrollbar(preview_canvas_frame, orient=tk.HORIZONTAL)
preview_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

preview_canvas = tk.Canvas(preview_canvas_frame, bg='#eef2f7', 
                           xscrollcommand=preview_h_scroll.set,
                           yscrollcommand=preview_v_scroll.set,
                           width=700, height=400)
preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

preview_v_scroll.config(command=preview_canvas.yview)
preview_h_scroll.config(command=preview_canvas.xview)

# Initial placeholder text on canvas
DEFAULT_PREVIEW_TEXT = "No image loaded\n\n1. Open Folder to load handwriting images\n   OR\n2. Generate HTR to create synthetic images\n\n3. Pick LINE or WORD detection for the first image\n   (the choice stays for all images)\n4. Annotate, then move to the next image"
GENERATE_PREVIEW_TEXT = "Generate mode active\n\nUse the Generate HTR panel to create synthetic handwriting"

def show_preview_placeholder(text):
    """Clear the preview canvas and show a placeholder message."""
    preview_canvas.delete('all')
    preview_canvas.create_text(350, 200, text=text,
                               fill='#7f8c8d', font=('Segoe UI', 12), justify=tk.CENTER)
    S.current_preview_image = None
    S.current_image_path = None

show_preview_placeholder(DEFAULT_PREVIEW_TEXT)

S.preview_canvas = preview_canvas
S.current_preview_image = None
S.show_preview_placeholder = show_preview_placeholder

def auto_detect_for_current():
    """Automatically run the locked segmentation mode on the current image."""
    if not getattr(S, 'auto_detect_on_navigation', False):
        return
    mode = getattr(S, 'segmentation_mode', None)
    if mode == 'word':
        detect_words_with_mode_lock()
    elif mode == 'line':
        detect_lines_with_autofill()

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
nav_frame.pack(fill=tk.X, pady=(8, 4), padx=2)

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
                         bg=COLORS['accent'], fg='white', font=('Segoe UI', 9), width=10)
btn_prev_img.pack(side=tk.LEFT, padx=3, pady=2)

btn_next_img = tk.Button(nav_frame, text="Next ▶", command=next_image,
                         bg=COLORS['accent'], fg='white', font=('Segoe UI', 9), width=10)
btn_next_img.pack(side=tk.LEFT, padx=3, pady=2)

image_info_var = tk.StringVar(value="No images loaded")
image_info_label = tk.Label(nav_frame, textvariable=image_info_var,
                            font=('Segoe UI', 9), bg=COLORS['bg_section'], fg=COLORS['text_muted'])
image_info_label.pack(side=tk.LEFT, padx=20)

S.image_info_var = image_info_var
S.btn_prev_img = btn_prev_img
S.btn_next_img = btn_next_img

# Create a dummy label for backward compatibility
label = tk.Label(load_image_container)
S.label = label

# ============================================
# CONTAINER 2: Generate HTR Interface (hidden by default)
# ============================================
generate_htr_container = tk.Frame(content_frame, bg=COLORS['bg_dark'])
# Don't pack it initially - it will be shown when user clicks "Generate HTR"

S.generate_htr_container = generate_htr_container
S.content_frame = content_frame

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
            switch_to_generate_mode()
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
