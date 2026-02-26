from http.client import OK
import os
import tkinter as tk
from tkinter import *
from tkinter import messagebox
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

# Home panel for corpus statistics
from home_panel import HomePanel, create_home_button

# Workflow engine
from workflow import WorkflowManager

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

# ------------------------------------------------------------------
# Sidebar visibility helpers
# ------------------------------------------------------------------
def show_sidebar():
    """Show the left sidebar (fr_buttons) when entering non-workflow views."""
    if not fr_buttons.winfo_manager():
        fr_buttons.grid(row=0, column=0, sticky="nsew")

def hide_sidebar():
    """Hide the left sidebar when the workflow panel is the active view."""
    if fr_buttons.winfo_manager():
        fr_buttons.grid_remove()

S.show_sidebar = show_sidebar
S.hide_sidebar = hide_sidebar

# App title in sidebar
title_frame = tk.Frame(fr_buttons, bg=COLORS['bg_panel'])
title_frame.pack(fill=tk.X, pady=(0, 15))
tk.Label(title_frame, text="📝 Annotation Tool", font=('Segoe UI', 14, 'bold'), 
         bg=COLORS['bg_panel'], fg=COLORS['text_light']).pack()
tk.Label(title_frame, text="Handwriting Analysis Suite", font=('Segoe UI', 9), 
         bg=COLORS['bg_panel'], fg=COLORS['text_muted']).pack()

# Separator
tk.Frame(fr_buttons, height=2, bg=COLORS['border']).pack(fill=tk.X, pady=10)

# ============================================
# HOME DASHBOARD BUTTON
# ============================================
home_section = tk.Frame(fr_buttons, bg=COLORS['bg_panel'])
home_section.pack(fill=tk.X, pady=(0, 10))

# Home panel instance (will be created later after content_frame exists)
home_panel_instance = None

def toggle_home_panel():
    """Toggle the home dashboard panel visibility."""
    global home_panel_instance
    
    if home_panel_instance is None:
        return
    
    # Check if home panel is currently visible
    if home_panel_instance.container.winfo_manager():
        # Hide home panel, return to workflow or previous view
        home_panel_instance.hide()
        btn_home.config(text="🏠 Home Dashboard", bg=COLORS['accent'])
        if getattr(S, 'workflow_active', False) and workflow_manager_instance:
            workflow_manager_instance.container.pack(expand=True, fill=tk.BOTH)
            hide_sidebar()
        elif input_mode_var.get() == 'generate':
            if widget_exists(S.generate_htr_container):
                S.generate_htr_container.pack(expand=True, fill=tk.BOTH)
        else:
            if widget_exists(S.load_image_container):
                S.load_image_container.pack(expand=True, fill=tk.BOTH)
    else:
        # Hide all containers + workflow, show home panel
        for container in [S.load_image_container, S.generate_htr_container, 
                         S.word_detect_container, S.line_detect_container,
                         S.char_detect_container, S.annotation_container]:
            if widget_exists(container):
                container.pack_forget()
        if workflow_manager_instance and widget_exists(workflow_manager_instance.container):
            workflow_manager_instance.container.pack_forget()
        
        home_panel_instance.show()
        btn_home.config(text="✖ Close Dashboard", bg=COLORS['danger'])

def close_home_panel():
    """Callback when home panel is closed."""
    btn_home.config(text="🏠 Home Dashboard", bg=COLORS['accent'])
    # Return to workflow if active, otherwise show appropriate container
    if getattr(S, 'workflow_active', False) and workflow_manager_instance:
        workflow_manager_instance.container.pack(expand=True, fill=tk.BOTH)
        hide_sidebar()
    elif input_mode_var.get() == 'generate':
        if widget_exists(S.generate_htr_container):
            S.generate_htr_container.pack(expand=True, fill=tk.BOTH)
    else:
        if widget_exists(S.load_image_container):
            S.load_image_container.pack(expand=True, fill=tk.BOTH)

btn_home = create_home_button(home_section, COLORS, toggle_home_panel)
btn_home.pack(fill=tk.X, padx=5)

# Store in state
S.btn_home = btn_home
S.toggle_home_panel = toggle_home_panel

# ============================================
# WORKFLOW BUTTON
# ============================================
workflow_section = tk.Frame(fr_buttons, bg=COLORS['bg_panel'])
workflow_section.pack(fill=tk.X, pady=(0, 10))

workflow_manager_instance = None  # initialised later after content_frame

def toggle_workflow_panel():
    """Toggle the 5-step workflow wizard."""
    global workflow_manager_instance
    if workflow_manager_instance is None:
        return

    if workflow_manager_instance.container.winfo_manager():
        # Hide workflow, restore previous view
        workflow_manager_instance.container.pack_forget()
        btn_workflow.config(text="🔄 Workflow Wizard", bg=COLORS['accent'])
        show_sidebar()
        if input_mode_var.get() == 'generate':
            if widget_exists(S.generate_htr_container):
                S.generate_htr_container.pack(expand=True, fill=tk.BOTH)
        else:
            if widget_exists(S.load_image_container):
                S.load_image_container.pack(expand=True, fill=tk.BOTH)
        S.workflow_active = False
    else:
        # Hide everything, show workflow
        for container in [S.load_image_container, S.generate_htr_container,
                          S.word_detect_container, S.line_detect_container,
                          S.char_detect_container, S.annotation_container]:
            if widget_exists(container):
                container.pack_forget()
        if home_panel_instance and home_panel_instance.container.winfo_manager():
            home_panel_instance.hide()
            btn_home.config(text="🏠 Home Dashboard", bg=COLORS['accent'])
        workflow_manager_instance.container.pack(expand=True, fill=tk.BOTH)
        btn_workflow.config(text="✖ Close Workflow", bg=COLORS['danger'])
        S.workflow_active = True
        hide_sidebar()

def close_workflow_panel():
    """Callback when workflow panel is closed."""
    btn_workflow.config(text="🔄 Workflow Wizard", bg=COLORS['accent'])
    S.workflow_active = False
    show_sidebar()
    # Show home panel or appropriate container
    if home_panel_instance:
        home_panel_instance.show()
        btn_home.config(text="✖ Close Dashboard", bg=COLORS['danger'])
    elif input_mode_var.get() == 'generate':
        if widget_exists(S.generate_htr_container):
            S.generate_htr_container.pack(expand=True, fill=tk.BOTH)
    else:
        if widget_exists(S.load_image_container):
            S.load_image_container.pack(expand=True, fill=tk.BOTH)

btn_workflow = tk.Button(
    workflow_section, text="🔄 Workflow Wizard",
    font=('Segoe UI', 10, 'bold'), bg=COLORS['accent'], fg='white',
    activebackground=COLORS['accent_hover'], activeforeground='white',
    relief=tk.FLAT, cursor='hand2', padx=8, pady=6,
    command=toggle_workflow_panel)
btn_workflow.pack(fill=tk.X, padx=5)

S.btn_workflow = btn_workflow
S.toggle_workflow_panel = toggle_workflow_panel

# Separator
tk.Frame(fr_buttons, height=2, bg=COLORS['border']).pack(fill=tk.X, pady=5)

# ============================================
# Section 1: Input Mode Toggle
# ============================================
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
S.input_mode_var = input_mode_var

def widget_exists(widget):
    """Check if a tkinter widget still exists."""
    try:
        return widget is not None and widget.winfo_exists()
    except:
        return False


def back_to_detection_from_annotation():
    """Go back from annotation panel to the corresponding detection panel and re-enable the detection button."""
    mode = getattr(S, 'current_annotation_mode', None)
    
    # Hide annotation container
    if widget_exists(S.annotation_container):
        S.annotation_container.pack_forget()
    
    if mode == 'word':
        # Re-enable word detection button
        if widget_exists(S.btn_save):
            S.btn_save.config(state='normal')
        # Show word detection container
        if widget_exists(S.word_detect_container):
            S.word_detect_container.pack(expand=True, fill=tk.BOTH)
    elif mode == 'line':
        # Re-enable line detection button
        if widget_exists(S.btn_line_detect):
            S.btn_line_detect.config(state='normal')
        # Show line detection container
        if widget_exists(S.line_detect_container):
            S.line_detect_container.pack(expand=True, fill=tk.BOTH)
    elif mode == 'character':
        # Re-enable character detection button
        if widget_exists(S.btn_char_detect):
            S.btn_char_detect.config(state='normal')
        # Show character detection container
        if widget_exists(S.char_detect_container):
            S.char_detect_container.pack(expand=True, fill=tk.BOTH)
    else:
        # Default: return to workflow if active, otherwise show container based on input mode
        if getattr(S, 'workflow_active', False) and hasattr(S, 'workflow_manager') and widget_exists(S.workflow_manager.container):
            S.workflow_manager.container.pack(expand=True, fill=tk.BOTH)
            hide_sidebar()
        else:
            current_input_mode = S.input_mode_var.get() if hasattr(S, 'input_mode_var') else 'load'
            if current_input_mode == 'generate' and widget_exists(S.generate_htr_container):
                S.generate_htr_container.pack(expand=True, fill=tk.BOTH)
            elif widget_exists(S.load_image_container):
                S.load_image_container.pack(expand=True, fill=tk.BOTH)

# Store the function in state so it can be accessed from other modules
S.back_to_detection_from_annotation = back_to_detection_from_annotation


def update_back_button_text():
    """Update back button text based on current input mode."""
    is_generate_mode = input_mode_var.get() == 'generate'
    load_text = "⬅ Back to image view"
    generate_text = "⬅ Back to Generate GAN"
    
    btn_text = generate_text if is_generate_mode else load_text
    
    if hasattr(S, 'btn_back_view') and widget_exists(S.btn_back_view):
        S.btn_back_view.config(text=btn_text)
    if hasattr(S, 'btn_back_line_view') and widget_exists(S.btn_back_line_view):
        S.btn_back_line_view.config(text=btn_text)
    if hasattr(S, 'btn_back_char_view') and widget_exists(S.btn_back_char_view):
        S.btn_back_char_view.config(text=btn_text)


def images_available():
    """Return True if a folder is loaded or GAN images exist."""
    has_loaded = hasattr(S, 'list_of_files') and S.list_of_files
    has_gan = getattr(S, 'gan_generated_ready', False) and getattr(S, 'gan_batch_images', [])
    return bool(has_loaded or has_gan)


def prompt_for_input_text():
    """Show a reminder popup to fill input text in the main GUI.
    Returns True to continue with detection, False to go back to image view.
    Only shows if input text is empty."""
    
    # Check if input text is already filled - if so, skip the popup
    input_text_content = ""
    if hasattr(S, 'input_text_area') and S.input_text_area:
        input_text_content = S.input_text_area.get("1.0", "end-1c").strip()
    
    if input_text_content:
        # Text is already filled, continue without showing popup
        return True
    
    # Create a custom dialog
    dialog = tk.Toplevel(window)
    dialog.title("Input Text Reminder")
    dialog.geometry("520x250")
    dialog.transient(window)
    dialog.grab_set()
    dialog.resizable(False, False)
    dialog.configure(bg='white')
    
    # Center the dialog
    dialog.update_idletasks()
    x = window.winfo_x() + (window.winfo_width() - 520) // 2
    y = window.winfo_y() + (window.winfo_height() - 250) // 2
    dialog.geometry(f"+{x}+{y}")
    
    result = {"continue": False}
    
    # Message icon and text
    msg_frame = tk.Frame(dialog, bg='white')
    msg_frame.pack(fill=tk.X, padx=25, pady=(20, 10))
    
    tk.Label(msg_frame, text="📝", font=('Segoe UI', 28), bg='white').pack(pady=(0, 10))
    
    tk.Label(msg_frame, text="Input Text for Auto-Fill Annotation",
             font=('Segoe UI', 12, 'bold'), bg='white', fg='#333').pack(pady=(0, 8))
    
    tk.Label(msg_frame, 
             text="To automatically fill annotations for detected lines/words,\nplease enter the text content of the image in the\n'Input Text' field on the Load Image panel.",
             font=('Segoe UI', 10), fg='#555', bg='white', justify=tk.CENTER).pack(pady=(0, 5))
    
    tk.Label(msg_frame, 
             text="You can continue without text, but annotations will be empty.",
             font=('Segoe UI', 9, 'italic'), fg='#888', bg='white').pack(pady=(5, 0))
    
    # Buttons frame
    btn_frame = tk.Frame(dialog, bg='white')
    btn_frame.pack(fill=tk.X, padx=25, pady=(15, 20))
    
    def on_go_back():
        result["continue"] = False
        dialog.destroy()
    
    def on_continue():
        result["continue"] = True
        dialog.destroy()
    
    btn_back = tk.Button(btn_frame, text="⬅ Go Back to Fill Text", command=on_go_back,
              bg='#e9ecef', fg='#495057', activebackground='#dee2e6',
              font=('Segoe UI', 10), width=18, pady=6, relief=tk.GROOVE,
              cursor='hand2')
    btn_back.pack(side=tk.LEFT, padx=5)
    
    btn_continue = tk.Button(btn_frame, text="Continue Without Text ➡", command=on_continue,
              bg=COLORS['accent'], fg='white', activebackground=COLORS['accent_hover'],
              font=('Segoe UI', 10, 'bold'), width=20, pady=6, relief=tk.GROOVE,
              cursor='hand2')
    btn_continue.pack(side=tk.RIGHT, padx=5)
    
    # Handle window close (treat as go back)
    dialog.protocol("WM_DELETE_WINDOW", on_go_back)
    
    # Wait for dialog to close
    dialog.wait_window()
    
    return result["continue"]


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
            if widget_exists(btn_char_detect):
                btn_char_detect.config(state='disabled')
        elif mode == 'word':
            if widget_exists(btn_line_detect):
                btn_line_detect.config(state='disabled')
            if widget_exists(btn_save):
                btn_save.config(state='normal')
            if widget_exists(btn_char_detect):
                btn_char_detect.config(state='disabled')
        elif mode == 'character':
            if widget_exists(btn_line_detect):
                btn_line_detect.config(state='disabled')
            if widget_exists(btn_save):
                btn_save.config(state='disabled')
            if widget_exists(btn_char_detect):
                btn_char_detect.config(state='normal')
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
        if widget_exists(btn_char_detect):
            btn_char_detect.config(state='disabled')
    elif selected_mode == 'word':
        if widget_exists(btn_line_detect):
            btn_line_detect.config(state='disabled')
        if widget_exists(btn_char_detect):
            btn_char_detect.config(state='disabled')
    elif selected_mode == 'character':
        if widget_exists(btn_line_detect):
            btn_line_detect.config(state='disabled')
        if widget_exists(btn_save):
            btn_save.config(state='disabled')

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

    # Check if image is loaded - use input mode to determine source
    image_path = None
    current_mode = input_mode_var.get() if hasattr(S, 'input_mode_var') else 'load'
    
    if current_mode == 'generate':
        # Generate mode: use GAN generated images
        if hasattr(S, 'gan_batch_images') and S.gan_batch_images:
            gan_idx = getattr(S, 'gan_batch_index', 0)
            if gan_idx < len(S.gan_batch_images):
                image_path = S.gan_batch_images[gan_idx]
    else:
        # Load mode: use loaded images and prompt for input text
        if hasattr(S, 'list_of_files') and S.list_of_files and S.pos < len(S.list_of_files):
            image_path = S.list_of_files[S.pos]
            # Prompt user - if they choose to go back, reset and return
            if not prompt_for_input_text():
                # User chose to go back - reset segmentation mode and re-enable buttons
                S.segmentation_mode = None
                if widget_exists(btn_line_detect):
                    btn_line_detect.config(state='normal')
                if widget_exists(btn_save):
                    btn_save.config(state='normal')
                # Only enable char detect if word images exist
                if widget_exists(btn_char_detect):
                    word_image_paths = getattr(S, 'word_image_paths', [])
                    if word_image_paths:
                        btn_char_detect.config(state='normal')
                return
    
    if not image_path or not os.path.exists(image_path):
        messagebox.showwarning("No Image", "Please load an image first:\n• Open Folder to load images\n• Generate HTR to create synthetic images")
        return
    
    # Get input text for auto-fill (check GAN input text first for generate mode)
    input_text = ""
    if current_mode == 'generate':
        if hasattr(S, 'gan_input_text') and S.gan_input_text:
            input_text = S.gan_input_text.strip()
    else:
        # Load mode: get text from the input_text_area widget
        if hasattr(S, 'input_text_area') and S.input_text_area:
            input_text = S.input_text_area.get("1.0", "end-1c").strip()
        elif hasattr(S, 'input_text') and S.input_text:
            input_text = S.input_text.strip()
    
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
        if widget_exists(S.generate_htr_container):
            S.generate_htr_container.pack_forget()
        if widget_exists(S.word_detect_container):
            S.word_detect_container.pack_forget()
        if widget_exists(S.annotation_container):
            S.annotation_container.pack_forget()
        # Hide workflow/home panels when entering detection view
        if hasattr(S, 'workflow_manager') and widget_exists(S.workflow_manager.container):
            S.workflow_manager.container.pack_forget()
        if hasattr(S, 'home_panel') and widget_exists(S.home_panel.container):
            S.home_panel.container.pack_forget()
        show_sidebar()
        if widget_exists(S.line_detect_container):
            S.line_detect_container.pack(expand=True, fill=tk.BOTH)
        
        # Update back button text based on input mode
        update_back_button_text()
        
        # Draw lines on canvas
        display_detected_lines(img, lines)
        
        if hasattr(S, 'update_status') and S.update_status:
            S.update_status(f"Detected {len(lines)} lines")
        
    except Exception as e:
        messagebox.showerror("Error", f"Line detection failed:\n{str(e)}")
        import traceback
        traceback.print_exc()

def _unpack_line(line_t, img=None):
    """Unpack a line tuple to (x1, y1, x2, y2) regardless of format."""
    if len(line_t) == 4:
        return line_t
    y1, y2 = line_t
    img_w = img.shape[1] if img is not None else 0
    return (0, y1, img_w, y2)

def display_detected_lines(img, lines, highlight_idx=None):
    """Display image with detected lines on the line detection canvas."""
    if not hasattr(S, 'line_detect_canvas'):
        return
    
    # Store image for redrawing
    S.line_display_img = img
    
    canvas = S.line_detect_canvas
    canvas.delete('all')
    
    # Draw image with line boxes
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_with_lines = img_rgb.copy()
    
    # Draw rectangles around detected lines
    for i, line_t in enumerate(lines):
        x1, y_start, x2, y_end = _unpack_line(line_t, img)
        if i == highlight_idx:
            color = (0, 255, 0)  # Green for selected
            thickness = 3
        else:
            color = (30, 144, 255)
            thickness = 2
        cv2.rectangle(img_with_lines, (x1, y_start), (x2, y_end), color, thickness)
        cv2.putText(img_with_lines, f"Line {i+1}", (x1 + 5, y_start + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Resize for display
    h, w = img_with_lines.shape[:2]
    canvas_w, canvas_h = 600, 450
    scale = min(canvas_w / w, canvas_h / h, 1.0)
    new_w, new_h = int(w * scale), int(h * scale)
    
    img_resized = cv2.resize(img_with_lines, (new_w, new_h), interpolation=cv2.INTER_AREA)
    pil_img = Image.fromarray(img_resized)
    S.line_detect_photo = ImageTk.PhotoImage(pil_img)
    
    # Center on canvas
    x_offset = (canvas_w - new_w) // 2
    y_offset = (canvas_h - new_h) // 2
    canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=S.line_detect_photo)
    
    # Store scale and offset for coordinate conversion
    S.line_canvas_scale = scale
    S.line_canvas_offset = (x_offset, y_offset)
    
    # Update info label
    if hasattr(S, 'line_info_label'):
        S.line_info_label.config(text=f"Detected {len(lines)} lines - Edit or add manually below")
    
    # Refresh listbox
    if hasattr(S, 'refresh_line_bbox_list'):
        S.refresh_line_bbox_list()

def redraw_line_detection(highlight_idx=None):
    """Redraw line detection with current detected_lines."""
    if hasattr(S, 'line_display_img') and hasattr(S, 'detected_lines'):
        display_detected_lines(S.line_display_img, S.detected_lines, highlight_idx)

def redraw_word_detection(highlight_idx=None):
    """Redraw word detection with current word_bboxes."""
    if hasattr(S, 'word_display_img') and hasattr(S, 'word_bboxes'):
        display_word_bboxes(S.word_display_img, S.word_bboxes, highlight_idx)

def display_word_bboxes(img, bboxes, highlight_idx=None):
    """Display image with word bounding boxes."""
    if not hasattr(S, 'word_detect_canvas'):
        return
    
    # Store image for redrawing
    S.word_display_img = img
    
    canvas = S.word_detect_canvas
    canvas.delete('all')
    
    # Draw image with word boxes
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_with_words = img_rgb.copy()
    
    # Draw rectangles around detected words
    for i, (x, y, w, h) in enumerate(bboxes):
        # Ensure coordinates are integers for OpenCV
        x, y, w, h = int(x), int(y), int(w), int(h)
        if i == highlight_idx:
            color = (0, 255, 0)  # Green for selected
            thickness = 3
        else:
            color = (255, 100, 100)
            thickness = 2
        cv2.rectangle(img_with_words, (x, y), (x + w, y + h), color, thickness)
        cv2.putText(img_with_words, f"{i+1}", (x + 2, y + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # Resize for display
    img_h, img_w = img_with_words.shape[:2]
    canvas_w, canvas_h = 600, 450
    scale = min(canvas_w / img_w, canvas_h / img_h, 1.0)
    new_w, new_h = int(img_w * scale), int(img_h * scale)
    
    img_resized = cv2.resize(img_with_words, (new_w, new_h), interpolation=cv2.INTER_AREA)
    pil_img = Image.fromarray(img_resized)
    S.word_detect_photo = ImageTk.PhotoImage(pil_img)
    
    # Center on canvas
    x_offset = (canvas_w - new_w) // 2
    y_offset = (canvas_h - new_h) // 2
    canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=S.word_detect_photo)
    
    # Store scale and offset for coordinate conversion
    S.word_canvas_scale = scale
    S.word_canvas_offset = (x_offset, y_offset)
    
    # Refresh listbox
    if hasattr(S, 'refresh_word_bbox_list'):
        S.refresh_word_bbox_list()

# Store the display function in state for use by save_file.py (avoids circular import)
S.display_word_bboxes_func = display_word_bboxes

# Section 2: Detection
section2 = tk.LabelFrame(fr_buttons, text=" 🔍 Detection ", font=('Segoe UI', 10, 'bold'),
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], 
                         relief=tk.FLAT, bd=1, padx=10, pady=10)
section2.pack(fill=tk.X, pady=(0, 10))

# Line detection row
line_row = tk.Frame(section2, bg=COLORS['bg_section'])
line_row.pack(fill=tk.X, pady=3)
btn_line_detect = create_styled_button(line_row, "📄 Detect Lines", detect_lines_with_autofill, 'warning', width=18)
btn_line_detect.pack(side=tk.LEFT, fill=tk.X, expand=True)

def detect_words_with_mode_lock():
    if not set_segmentation_mode('word'):
        return
    if not ensure_images_available():
        return
    
    # Disable other detection buttons
    disable_other_detection_buttons('word')
    
    # Check input mode to determine if we should prompt for input text
    current_mode = input_mode_var.get() if hasattr(S, 'input_mode_var') else 'load'
    
    # Require either loaded images or generated GAN previews before showing detection
    has_loaded_images = hasattr(S, 'list_of_files') and S.list_of_files
    has_gan_images = getattr(S, 'gan_generated_ready', False) and getattr(S, 'gan_batch_images', [])
    if not (has_loaded_images or has_gan_images):
        from tkinter import messagebox
        messagebox.showinfo("No images available", "Load an image folder or generate HTR images before word detection.")
        return
    
    # In load mode, prompt for input text to facilitate annotation
    if current_mode == 'load' and has_loaded_images:
        if not prompt_for_input_text():
            # User chose to go back - reset segmentation mode and re-enable buttons
            S.segmentation_mode = None
            if widget_exists(btn_line_detect):
                btn_line_detect.config(state='normal')
            if widget_exists(btn_save):
                btn_save.config(state='normal')
            if widget_exists(btn_char_detect):
                btn_char_detect.config(state='normal')
            return
    if widget_exists(S.annotation_container):
        S.annotation_container.pack_forget()
    if widget_exists(S.load_image_container):
        S.load_image_container.pack_forget()
    if widget_exists(S.generate_htr_container):
        S.generate_htr_container.pack_forget()
    # Hide workflow/home panels when entering detection view
    if hasattr(S, 'workflow_manager') and widget_exists(S.workflow_manager.container):
        S.workflow_manager.container.pack_forget()
    if hasattr(S, 'home_panel') and widget_exists(S.home_panel.container):
        S.home_panel.container.pack_forget()
    show_sidebar()
    if widget_exists(S.word_detect_container):
        S.word_detect_container.pack(expand=True, fill=tk.BOTH)
    # Update back button text based on input mode
    update_back_button_text()
    save_file()

# Word detection row
word_row = tk.Frame(section2, bg=COLORS['bg_section'])
word_row.pack(fill=tk.X, pady=3)
btn_save = create_styled_button(word_row, "🎯 Detect Words", detect_words_with_mode_lock, 'warning', width=18)
btn_save.pack(side=tk.LEFT, fill=tk.X, expand=True)

def detect_characters():
    """Detect characters via template matching on the current image.
    Works on word images if word detection has been run, otherwise
    operates directly on the full input image."""
    from tkinter import messagebox
    import json
    from utils import match_template_in_image
    
    if not ensure_images_available():
        return
    
    # Build the list of images to process for character detection.
    # Priority: word images from detection > full input image(s)
    word_image_paths = getattr(S, 'word_image_paths', [])
    
    if not word_image_paths and hasattr(S, 'directoryout') and os.path.exists(S.directoryout):
        import glob
        word_files = sorted(glob.glob(os.path.join(S.directoryout, '*.png')),
                           key=lambda x: int(os.path.splitext(os.path.basename(x))[0]) if os.path.splitext(os.path.basename(x))[0].isdigit() else 0)
        if word_files:
            word_image_paths = word_files
            S.word_image_paths = word_files
    
    # Fallback: use the current input image directly
    if not word_image_paths:
        input_path = None
        if S.list_of_files and len(S.list_of_files) > S.pos:
            input_path = S.list_of_files[S.pos]
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("No Image",
                                   "No image available for character detection.")
            return
        word_image_paths = [input_path]
        S.word_image_paths = word_image_paths
    
    # Disable other detection buttons
    disable_other_detection_buttons('character')
    
    # Initialize word selection index
    S.char_word_index = getattr(S, 'char_word_index', 0)
    if S.char_word_index >= len(word_image_paths):
        S.char_word_index = 0
    
    # Get current word image
    current_word_path = word_image_paths[S.char_word_index]
    S.char_image_path = current_word_path
    S.char_total_words = len(word_image_paths)
    
    # Try to load saved character templates
    templates_dir = os.path.join(os.path.dirname(__file__), 'character_templates')
    S.char_templates = []
    S.char_detected_boxes = []
    
    if os.path.exists(templates_dir):
        # Load all template images
        for fname in os.listdir(templates_dir):
            if fname.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                char_label = os.path.splitext(fname)[0]  # filename without extension is the label
                template_path = os.path.join(templates_dir, fname)
                S.char_templates.append({'label': char_label, 'path': template_path})
    
    # Load word image for detection
    try:
        img = cv2.imread(current_word_path)
        if img is None:
            messagebox.showerror("Error", f"Could not read word image:\n{current_word_path}")
            return
        
        pil_img = Image.open(current_word_path)
        
        # If we have templates, perform template matching
        detected_chars = []
        if S.char_templates:
            # Use threshold from slider if available
            threshold = S.char_threshold_var.get() if hasattr(S, 'char_threshold_var') else 0.6
            for tpl_info in S.char_templates:
                try:
                    template_img = Image.open(tpl_info['path'])
                    matches = match_template_in_image(pil_img, template_img, threshold=threshold)
                    for m in matches:
                        detected_chars.append({
                            'coords': (m[0], m[1], m[2], m[3]),
                            'label': tpl_info['label'],
                            'score': m[4]
                        })
                except Exception as e:
                    print(f"Template matching error for {tpl_info['label']}: {e}")
        
        S.char_detected_boxes = detected_chars
        
        # Switch to character detection view
        if widget_exists(S.load_image_container):
            S.load_image_container.pack_forget()
        if widget_exists(S.generate_htr_container):
            S.generate_htr_container.pack_forget()
        if widget_exists(S.word_detect_container):
            S.word_detect_container.pack_forget()
        if widget_exists(S.line_detect_container):
            S.line_detect_container.pack_forget()
        if widget_exists(S.annotation_container):
            S.annotation_container.pack_forget()
        # Hide workflow/home panels when entering detection view
        if hasattr(S, 'workflow_manager') and widget_exists(S.workflow_manager.container):
            S.workflow_manager.container.pack_forget()
        if hasattr(S, 'home_panel') and widget_exists(S.home_panel.container):
            S.home_panel.container.pack_forget()
        show_sidebar()
        if widget_exists(S.char_detect_container):
            S.char_detect_container.pack(expand=True, fill=tk.BOTH)
        
        # Update back button text based on input mode
        update_back_button_text()
        
        # Update word navigation label
        if hasattr(S, 'update_char_word_label'):
            S.update_char_word_label()
        
        # Draw image with detected boxes
        display_detected_characters(img, detected_chars)
        
        # Refresh character listbox
        if hasattr(S, 'refresh_char_listbox'):
            S.refresh_char_listbox()
        
        # Clear zoom canvas
        if hasattr(S, 'char_zoom_canvas'):
            S.char_zoom_canvas.delete('all')
        
        # Update info label with word navigation info
        word_info = f"Word {S.char_word_index + 1}/{S.char_total_words}"
        if S.char_templates:
            if detected_chars:
                S.char_info_label.config(text=f"{word_info} | Found {len(detected_chars)} chars using {len(S.char_templates)} templates.")
            else:
                S.char_info_label.config(text=f"{word_info} | No matches. Draw a box to create template.")
        else:
            S.char_info_label.config(text=f"{word_info} | No templates saved. Draw box around a character.")
        
        if hasattr(S, 'update_status') and S.update_status:
            S.update_status(f"Character detection on word {S.char_word_index + 1}/{S.char_total_words}: {len(detected_chars)} found")
            
    except Exception as e:
        messagebox.showerror("Error", f"Character detection failed:\n{str(e)}")
        import traceback
        traceback.print_exc()

def char_next_word():
    """Navigate to next word image for character detection."""
    word_image_paths = getattr(S, 'word_image_paths', [])
    if not word_image_paths:
        return
    
    S.char_word_index = getattr(S, 'char_word_index', 0)
    if S.char_word_index < len(word_image_paths) - 1:
        S.char_word_index += 1
        # Reload character detection on new word
        _load_char_word_image()

def char_prev_word():
    """Navigate to previous word image for character detection."""
    word_image_paths = getattr(S, 'word_image_paths', [])
    if not word_image_paths:
        return
    
    S.char_word_index = getattr(S, 'char_word_index', 0)
    if S.char_word_index > 0:
        S.char_word_index -= 1
        # Reload character detection on new word
        _load_char_word_image()

def _load_char_word_image():
    """Load current word image for character detection."""
    from utils import match_template_in_image
    
    word_image_paths = getattr(S, 'word_image_paths', [])
    if not word_image_paths:
        return
    
    idx = S.char_word_index
    if idx >= len(word_image_paths):
        return
    
    current_word_path = word_image_paths[idx]
    S.char_image_path = current_word_path
    
    try:
        img = cv2.imread(current_word_path)
        if img is None:
            return
        
        pil_img = Image.open(current_word_path)
        
        # Perform template matching if templates exist
        detected_chars = []
        if hasattr(S, 'char_templates') and S.char_templates:
            threshold = S.char_threshold_var.get() if hasattr(S, 'char_threshold_var') else 0.6
            for tpl_info in S.char_templates:
                try:
                    template_img = Image.open(tpl_info['path'])
                    matches = match_template_in_image(pil_img, template_img, threshold=threshold)
                    for m in matches:
                        detected_chars.append({
                            'coords': (m[0], m[1], m[2], m[3]),
                            'label': tpl_info['label'],
                            'score': m[4]
                        })
                except Exception as e:
                    print(f"Template matching error: {e}")
        
        S.char_detected_boxes = detected_chars
        
        # Update display
        display_detected_characters(img, detected_chars)
        
        # Refresh listbox
        if hasattr(S, 'refresh_char_listbox'):
            S.refresh_char_listbox()
        
        # Update word navigation label
        if hasattr(S, 'update_char_word_label'):
            S.update_char_word_label()
        
        # Update info label
        word_info = f"Word {idx + 1}/{S.char_total_words}"
        if S.char_templates:
            if detected_chars:
                S.char_info_label.config(text=f"{word_info} | Found {len(detected_chars)} chars using {len(S.char_templates)} templates.")
            else:
                S.char_info_label.config(text=f"{word_info} | No matches. Draw a box to create template.")
        else:
            S.char_info_label.config(text=f"{word_info} | No templates saved. Draw box around a character.")
        
        if hasattr(S, 'update_status') and S.update_status:
            S.update_status(f"Word {idx + 1}/{S.char_total_words}: {len(detected_chars)} characters")
            
    except Exception as e:
        print(f"Error loading word image: {e}")

def display_detected_characters(img, detected_chars, highlight_idx=None):
    """Display image with detected character boxes on the character detection canvas."""
    if not hasattr(S, 'char_detect_canvas'):
        return
    
    # Use zoom-aware display function
    display_detected_characters_zoomed(img, detected_chars, highlight_idx)

# Character detection row
char_row = tk.Frame(section2, bg=COLORS['bg_section'])
char_row.pack(fill=tk.X, pady=3)
btn_char_detect = create_styled_button(char_row, "🔤 Detect Chars", detect_characters, 'warning', width=18)
btn_char_detect.pack(side=tk.LEFT, fill=tk.X, expand=True)

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
        seg_mode = getattr(S, 'segmentation_mode', None)
        word_image_paths = getattr(S, 'word_image_paths', [])
        
        if available:
            # Enable line and word detection buttons
            btn_line_detect.config(state='normal')
            btn_save.config(state='normal')
            btn_char_detect.config(state='normal')
            scale_slider.config(state='normal')
            padding_slider.config(state='normal')
            
            # Then respect segmentation mode lock if set
            if seg_mode == 'line':
                btn_save.config(state='disabled')
                btn_char_detect.config(state='disabled')
            elif seg_mode == 'word':
                btn_line_detect.config(state='disabled')
                btn_char_detect.config(state='disabled')
            elif seg_mode == 'character':
                btn_line_detect.config(state='disabled')
                btn_save.config(state='disabled')
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

# Hide sidebar at startup — workflow is the main interface
fr_buttons.grid_remove()

# Initial button states - disable detection buttons until image is loaded
btn_save["state"] = "disabled"
btn_line_detect["state"] = "disabled"
btn_char_detect["state"] = "disabled"
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
# HOME PANEL INITIALIZATION
# ============================================
# Initialize home panel now that content_frame exists
home_panel_instance = HomePanel(content_frame, COLORS, close_home_panel)
S.home_panel = home_panel_instance

# ============================================
# WORKFLOW PANEL INITIALIZATION
# ============================================
workflow_manager_instance = WorkflowManager(content_frame, COLORS, close_workflow_panel)
S.workflow_manager = workflow_manager_instance

# Show workflow panel by default at startup (main interface)
workflow_manager_instance.container.pack(expand=True, fill=tk.BOTH)
btn_workflow.config(text="✖ Close Workflow", bg=COLORS['danger'])
S.workflow_active = True

# ============================================
# CONTAINER 1: Load Image Interface
# ============================================
load_image_container = tk.Frame(content_frame, bg=COLORS['bg_dark'])
# Don't pack at startup - home panel is shown first
# load_image_container.pack(expand=True, fill=tk.BOTH)

# ============================================
# CONTAINER 2: Word Detection Review (hidden until word detect)
# ============================================
word_detect_container = tk.Frame(content_frame, bg=COLORS['bg_dark'])
word_detect_container.pack_forget()

word_detect_header = tk.Label(word_detect_container, text=" 🧠 Word Detection Review ",
                              font=('Segoe UI', 12, 'bold'),
                              bg=COLORS['bg_section'], fg=COLORS['text_light'],
                              relief=tk.FLAT, bd=1, padx=10, pady=8)
word_detect_header.pack(fill=tk.X, pady=(0, 5))

# Main frame with left (canvas) and right (bbox list) panels
word_main_frame = tk.Frame(word_detect_container, bg=COLORS['bg_dark'])
word_main_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

# Left panel: canvas for image display
word_left_panel = tk.Frame(word_main_frame, bg=COLORS['bg_dark'])
word_left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

word_canvas = tk.Canvas(word_left_panel, width=600, height=450,
                        bg='#eef2f7', highlightthickness=1, highlightbackground=COLORS['border'])
word_canvas.pack(fill=tk.BOTH, expand=True)

# Right panel: bounding box list
word_right_panel = tk.Frame(word_main_frame, bg=COLORS['bg_section'], width=280)
word_right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
word_right_panel.pack_propagate(False)

tk.Label(word_right_panel, text="📋 Detected Bounding Boxes",
         font=('Segoe UI', 10, 'bold'), bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(fill=tk.X, pady=5)

# Listbox for word bboxes
word_bbox_list_frame = tk.Frame(word_right_panel, bg=COLORS['bg_section'])
word_bbox_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

word_bbox_scroll = tk.Scrollbar(word_bbox_list_frame)
word_bbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)

word_bbox_listbox = tk.Listbox(word_bbox_list_frame, font=('Segoe UI', 9),
                               bg='white', fg=COLORS['text_light'],
                               selectbackground=COLORS['accent'], selectforeground='white',
                               yscrollcommand=word_bbox_scroll.set, height=12)
word_bbox_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
word_bbox_scroll.config(command=word_bbox_listbox.yview)

# Edit controls for word bbox
word_edit_frame = tk.Frame(word_right_panel, bg=COLORS['bg_section'])
word_edit_frame.pack(fill=tk.X, padx=5, pady=5)

tk.Label(word_edit_frame, text="Edit Selected BBox:", font=('Segoe UI', 9, 'bold'),
         bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(anchor='w')

word_coord_frame = tk.Frame(word_edit_frame, bg=COLORS['bg_section'])
word_coord_frame.pack(fill=tk.X, pady=3)

tk.Label(word_coord_frame, text="X:", bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)
word_x_var = tk.StringVar()
word_x_entry = tk.Entry(word_coord_frame, textvariable=word_x_var, width=5, font=('Segoe UI', 9))
word_x_entry.pack(side=tk.LEFT, padx=2)

tk.Label(word_coord_frame, text="Y:", bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)
word_y_var = tk.StringVar()
word_y_entry = tk.Entry(word_coord_frame, textvariable=word_y_var, width=5, font=('Segoe UI', 9))
word_y_entry.pack(side=tk.LEFT, padx=2)

tk.Label(word_coord_frame, text="W:", bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)
word_w_var = tk.StringVar()
word_w_entry = tk.Entry(word_coord_frame, textvariable=word_w_var, width=5, font=('Segoe UI', 9))
word_w_entry.pack(side=tk.LEFT, padx=2)

tk.Label(word_coord_frame, text="H:", bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)
word_h_var = tk.StringVar()
word_h_entry = tk.Entry(word_coord_frame, textvariable=word_h_var, width=5, font=('Segoe UI', 9))
word_h_entry.pack(side=tk.LEFT, padx=2)

word_bbox_btn_frame = tk.Frame(word_edit_frame, bg=COLORS['bg_section'])
word_bbox_btn_frame.pack(fill=tk.X, pady=3)

def update_word_bbox():
    """Update selected word bbox coordinates."""
    sel = word_bbox_listbox.curselection()
    if not sel or not hasattr(S, 'word_bboxes'):
        return
    idx = sel[0]
    try:
        x, y, w, h = int(word_x_var.get()), int(word_y_var.get()), int(word_w_var.get()), int(word_h_var.get())
        S.word_bboxes[idx] = (x, y, w, h)
        refresh_word_bbox_list()
        redraw_word_detection()
    except ValueError:
        messagebox.showerror("Error", "Please enter valid integer coordinates.")

def delete_word_bbox():
    """Delete selected word bbox."""
    sel = word_bbox_listbox.curselection()
    if not sel or not hasattr(S, 'word_bboxes'):
        return
    idx = sel[0]
    if messagebox.askyesno("Delete", f"Delete bounding box #{idx+1}?"):
        S.word_bboxes.pop(idx)
        refresh_word_bbox_list()
        redraw_word_detection()

tk.Button(word_bbox_btn_frame, text="✏️ Update", command=update_word_bbox,
          bg=COLORS['accent'], fg='white', font=('Segoe UI', 9), padx=8).pack(side=tk.LEFT, padx=2)
tk.Button(word_bbox_btn_frame, text="🗑️ Delete", command=delete_word_bbox,
          bg='#dc3545', fg='white', font=('Segoe UI', 9), padx=8).pack(side=tk.LEFT, padx=2)

def on_word_bbox_select(event):
    """Handle word bbox selection."""
    sel = word_bbox_listbox.curselection()
    if not sel or not hasattr(S, 'word_bboxes'):
        return
    idx = sel[0]
    x, y, w, h = S.word_bboxes[idx]
    word_x_var.set(str(x))
    word_y_var.set(str(y))
    word_w_var.set(str(w))
    word_h_var.set(str(h))
    redraw_word_detection(highlight_idx=idx)

word_bbox_listbox.bind('<<ListboxSelect>>', on_word_bbox_select)

def refresh_word_bbox_list():
    """Refresh the word bbox listbox."""
    word_bbox_listbox.delete(0, tk.END)
    if hasattr(S, 'word_bboxes'):
        for i, (x, y, w, h) in enumerate(S.word_bboxes):
            word_bbox_listbox.insert(tk.END, f"#{i+1}: ({x}, {y}, {w}×{h})")

# Manual annotation section at bottom
word_manual_frame = tk.LabelFrame(word_detect_container, text=" ✏️ Manual Annotation ",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=COLORS['bg_section'], fg=COLORS['text_light'])
word_manual_frame.pack(fill=tk.X, padx=4, pady=5)

word_manual_inner = tk.Frame(word_manual_frame, bg=COLORS['bg_section'])
word_manual_inner.pack(fill=tk.X, padx=10, pady=8)

tk.Label(word_manual_inner, text="Add bbox manually (x, y, w, h):", 
         font=('Segoe UI', 9), bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)

word_manual_x = tk.Entry(word_manual_inner, width=5, font=('Segoe UI', 9))
word_manual_x.pack(side=tk.LEFT, padx=2)
word_manual_y = tk.Entry(word_manual_inner, width=5, font=('Segoe UI', 9))
word_manual_y.pack(side=tk.LEFT, padx=2)
word_manual_w = tk.Entry(word_manual_inner, width=5, font=('Segoe UI', 9))
word_manual_w.pack(side=tk.LEFT, padx=2)
word_manual_h = tk.Entry(word_manual_inner, width=5, font=('Segoe UI', 9))
word_manual_h.pack(side=tk.LEFT, padx=2)

def add_word_bbox_manual():
    """Add a manual word bbox."""
    try:
        x = int(word_manual_x.get())
        y = int(word_manual_y.get())
        w = int(word_manual_w.get())
        h = int(word_manual_h.get())
        if not hasattr(S, 'word_bboxes'):
            S.word_bboxes = []
        S.word_bboxes.append((x, y, w, h))
        refresh_word_bbox_list()
        redraw_word_detection()
        word_manual_x.delete(0, tk.END)
        word_manual_y.delete(0, tk.END)
        word_manual_w.delete(0, tk.END)
        word_manual_h.delete(0, tk.END)
    except ValueError:
        messagebox.showerror("Error", "Please enter valid integer coordinates.")

tk.Button(word_manual_inner, text="➕ Add BBox", command=add_word_bbox_manual,
          bg=COLORS['success'], fg='white', font=('Segoe UI', 9, 'bold'), padx=10).pack(side=tk.LEFT, padx=10)

tk.Label(word_manual_inner, text="Or draw on canvas with mouse", 
         font=('Segoe UI', 8), bg=COLORS['bg_section'], fg=COLORS['text_muted']).pack(side=tk.LEFT, padx=10)

# Mouse drawing on word canvas
word_draw_state = {'start': None, 'rect': None}

def on_word_canvas_press(event):
    word_draw_state['start'] = (event.x, event.y)
    word_draw_state['rect'] = word_canvas.create_rectangle(event.x, event.y, event.x, event.y, 
                                                            outline='blue', width=2, dash=(4, 2))

def on_word_canvas_drag(event):
    if word_draw_state['rect']:
        word_canvas.coords(word_draw_state['rect'], 
                          word_draw_state['start'][0], word_draw_state['start'][1], 
                          event.x, event.y)

def on_word_canvas_release(event):
    if not word_draw_state['rect'] or not word_draw_state['start']:
        return
    word_canvas.delete(word_draw_state['rect'])
    x1, y1 = word_draw_state['start']
    x2, y2 = event.x, event.y
    word_draw_state['start'] = None
    word_draw_state['rect'] = None
    
    # Convert canvas coords to image coords
    if hasattr(S, 'word_canvas_scale') and hasattr(S, 'word_canvas_offset'):
        scale = S.word_canvas_scale
        ox, oy = S.word_canvas_offset
        ix1 = int((min(x1, x2) - ox) / scale)
        iy1 = int((min(y1, y2) - oy) / scale)
        ix2 = int((max(x1, x2) - ox) / scale)
        iy2 = int((max(y1, y2) - oy) / scale)
        w, h = ix2 - ix1, iy2 - iy1
        if w > 5 and h > 5:
            if not hasattr(S, 'word_bboxes'):
                S.word_bboxes = []
            S.word_bboxes.append((ix1, iy1, w, h))
            refresh_word_bbox_list()
            redraw_word_detection()

word_canvas.bind('<ButtonPress-1>', on_word_canvas_press)
word_canvas.bind('<B1-Motion>', on_word_canvas_drag)
word_canvas.bind('<ButtonRelease-1>', on_word_canvas_release)

word_btn_frame = tk.Frame(word_detect_container, bg=COLORS['bg_dark'])
word_btn_frame.pack(fill=tk.X, pady=(8, 0))

def back_to_image_view():
    if widget_exists(word_detect_container):
        word_detect_container.pack_forget()
    # Return to workflow if active, otherwise show appropriate container
    if getattr(S, 'workflow_active', False) and hasattr(S, 'workflow_manager') and widget_exists(S.workflow_manager.container):
        S.workflow_manager.container.pack(expand=True, fill=tk.BOTH)
        hide_sidebar()
    elif input_mode_var.get() == 'generate':
        if widget_exists(S.generate_htr_container):
            S.generate_htr_container.pack(expand=True, fill=tk.BOTH)
    else:
        if widget_exists(load_image_container):
            load_image_container.pack(expand=True, fill=tk.BOTH)
    # Enable all detection buttons
    if widget_exists(btn_save):
        btn_save.config(state='normal')
    if widget_exists(btn_line_detect):
        btn_line_detect.config(state='normal')
    if widget_exists(btn_char_detect):
        btn_char_detect.config(state='normal')
    # Reset segmentation mode to allow switching
    S.segmentation_mode = None
    segmentation_mode_var.set("Segmentation mode: Not selected")

def proceed_to_annotation_from_word_panel():
    if hasattr(S, 'perform_cropping_current_detection'):
        S.perform_cropping_current_detection()
    if widget_exists(S.word_detect_container):
        S.word_detect_container.pack_forget()
    if widget_exists(S.load_image_container):
        S.load_image_container.pack_forget()
    if widget_exists(S.generate_htr_container):
        S.generate_htr_container.pack_forget()
    if widget_exists(S.annotation_container):
        S.annotation_container.pack(expand=True, fill=tk.BOTH)
    # Disable word detection button while in annotation
    if widget_exists(btn_save):
        btn_save.config(state='disabled')
    S.current_annotation_mode = 'word'
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
S.btn_back_view = btn_back_view
S.word_bbox_listbox = word_bbox_listbox
S.refresh_word_bbox_list = refresh_word_bbox_list

# ============================================
# CONTAINER 2b: Line Detection Review (hidden until line detect)
# ============================================
line_detect_container = tk.Frame(content_frame, bg=COLORS['bg_dark'])
line_detect_container.pack_forget()

line_detect_header = tk.Label(line_detect_container, text=" 📄 Line Detection Review ",
                              font=('Segoe UI', 12, 'bold'),
                              bg=COLORS['bg_section'], fg=COLORS['text_light'],
                              relief=tk.FLAT, bd=1, padx=10, pady=8)
line_detect_header.pack(fill=tk.X, pady=(0, 5))

# Main frame with left (canvas) and right (bbox list) panels
line_main_frame = tk.Frame(line_detect_container, bg=COLORS['bg_dark'])
line_main_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

# Left panel: canvas for image display
line_left_panel = tk.Frame(line_main_frame, bg=COLORS['bg_dark'])
line_left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

line_canvas = tk.Canvas(line_left_panel, width=600, height=450,
                        bg='#eef2f7', highlightthickness=1, highlightbackground=COLORS['border'])
line_canvas.pack(fill=tk.BOTH, expand=True)

# Right panel: bounding box list
line_right_panel = tk.Frame(line_main_frame, bg=COLORS['bg_section'], width=280)
line_right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
line_right_panel.pack_propagate(False)

tk.Label(line_right_panel, text="📋 Detected Lines",
         font=('Segoe UI', 10, 'bold'), bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(fill=tk.X, pady=5)

# Listbox for line bboxes
line_bbox_list_frame = tk.Frame(line_right_panel, bg=COLORS['bg_section'])
line_bbox_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

line_bbox_scroll = tk.Scrollbar(line_bbox_list_frame)
line_bbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)

line_bbox_listbox = tk.Listbox(line_bbox_list_frame, font=('Segoe UI', 9),
                               bg='white', fg=COLORS['text_light'],
                               selectbackground=COLORS['accent'], selectforeground='white',
                               yscrollcommand=line_bbox_scroll.set, height=12)
line_bbox_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
line_bbox_scroll.config(command=line_bbox_listbox.yview)

# Edit controls for line bbox
line_edit_frame = tk.Frame(line_right_panel, bg=COLORS['bg_section'])
line_edit_frame.pack(fill=tk.X, padx=5, pady=5)

tk.Label(line_edit_frame, text="Edit Selected Line:", font=('Segoe UI', 9, 'bold'),
         bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(anchor='w')

line_coord_frame = tk.Frame(line_edit_frame, bg=COLORS['bg_section'])
line_coord_frame.pack(fill=tk.X, pady=3)

tk.Label(line_coord_frame, text="Y Start:", bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)
line_y1_var = tk.StringVar()
line_y1_entry = tk.Entry(line_coord_frame, textvariable=line_y1_var, width=6, font=('Segoe UI', 9))
line_y1_entry.pack(side=tk.LEFT, padx=2)

tk.Label(line_coord_frame, text="Y End:", bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)
line_y2_var = tk.StringVar()
line_y2_entry = tk.Entry(line_coord_frame, textvariable=line_y2_var, width=6, font=('Segoe UI', 9))
line_y2_entry.pack(side=tk.LEFT, padx=2)

line_bbox_btn_frame = tk.Frame(line_edit_frame, bg=COLORS['bg_section'])
line_bbox_btn_frame.pack(fill=tk.X, pady=3)

def update_line_bbox():
    """Update selected line bbox coordinates."""
    sel = line_bbox_listbox.curselection()
    if not sel or not hasattr(S, 'detected_lines'):
        return
    idx = sel[0]
    try:
        y1, y2 = int(line_y1_var.get()), int(line_y2_var.get())
        old = S.detected_lines[idx]
        x1, _, x2, _ = _unpack_line(old)
        S.detected_lines[idx] = (x1, y1, x2, y2)
        refresh_line_bbox_list()
        redraw_line_detection()
    except ValueError:
        messagebox.showerror("Error", "Please enter valid integer coordinates.")

def delete_line_bbox():
    """Delete selected line bbox."""
    sel = line_bbox_listbox.curselection()
    if not sel or not hasattr(S, 'detected_lines'):
        return
    idx = sel[0]
    if messagebox.askyesno("Delete", f"Delete line #{idx+1}?"):
        S.detected_lines.pop(idx)
        refresh_line_bbox_list()
        redraw_line_detection()

tk.Button(line_bbox_btn_frame, text="✏️ Update", command=update_line_bbox,
          bg=COLORS['accent'], fg='white', font=('Segoe UI', 9), padx=8).pack(side=tk.LEFT, padx=2)
tk.Button(line_bbox_btn_frame, text="🗑️ Delete", command=delete_line_bbox,
          bg='#dc3545', fg='white', font=('Segoe UI', 9), padx=8).pack(side=tk.LEFT, padx=2)

def on_line_bbox_select(event):
    """Handle line bbox selection."""
    sel = line_bbox_listbox.curselection()
    if not sel or not hasattr(S, 'detected_lines'):
        return
    idx = sel[0]
    x1, y1, x2, y2 = _unpack_line(S.detected_lines[idx])
    line_y1_var.set(str(y1))
    line_y2_var.set(str(y2))
    redraw_line_detection(highlight_idx=idx)

line_bbox_listbox.bind('<<ListboxSelect>>', on_line_bbox_select)

def refresh_line_bbox_list():
    """Refresh the line bbox listbox."""
    line_bbox_listbox.delete(0, tk.END)
    if hasattr(S, 'detected_lines'):
        for i, line_t in enumerate(S.detected_lines):
            x1, y1, x2, y2 = _unpack_line(line_t)
            line_bbox_listbox.insert(tk.END, f"Line #{i+1}: ({x1},{y1})→({x2},{y2})")

line_info_label = tk.Label(line_right_panel, text="",
                           font=('Segoe UI', 9), bg=COLORS['bg_section'], fg=COLORS['text_light'],
                           wraplength=250)
line_info_label.pack(fill=tk.X, pady=5, padx=5)

# Manual annotation section at bottom
line_manual_frame = tk.LabelFrame(line_detect_container, text=" ✏️ Manual Line Annotation ",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=COLORS['bg_section'], fg=COLORS['text_light'])
line_manual_frame.pack(fill=tk.X, padx=4, pady=5)

line_manual_inner = tk.Frame(line_manual_frame, bg=COLORS['bg_section'])
line_manual_inner.pack(fill=tk.X, padx=10, pady=8)

tk.Label(line_manual_inner, text="Add line manually (Y start, Y end):", 
         font=('Segoe UI', 9), bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)

line_manual_y1 = tk.Entry(line_manual_inner, width=6, font=('Segoe UI', 9))
line_manual_y1.pack(side=tk.LEFT, padx=2)
line_manual_y2 = tk.Entry(line_manual_inner, width=6, font=('Segoe UI', 9))
line_manual_y2.pack(side=tk.LEFT, padx=2)

def add_line_bbox_manual():
    """Add a manual line bbox."""
    try:
        y1 = int(line_manual_y1.get())
        y2 = int(line_manual_y2.get())
        if not hasattr(S, 'detected_lines'):
            S.detected_lines = []
        # Use full image width for manually added lines
        img_w = S.line_display_img.shape[1] if hasattr(S, 'line_display_img') and S.line_display_img is not None else 0
        S.detected_lines.append((0, y1, img_w, y2))
        # Sort lines by y1
        S.detected_lines.sort(key=lambda x: x[1] if len(x) == 4 else x[0])
        refresh_line_bbox_list()
        redraw_line_detection()
        line_manual_y1.delete(0, tk.END)
        line_manual_y2.delete(0, tk.END)
    except ValueError:
        messagebox.showerror("Error", "Please enter valid integer coordinates.")

tk.Button(line_manual_inner, text="➕ Add Line", command=add_line_bbox_manual,
          bg=COLORS['success'], fg='white', font=('Segoe UI', 9, 'bold'), padx=10).pack(side=tk.LEFT, padx=10)

tk.Label(line_manual_inner, text="Or draw horizontal line on canvas with mouse", 
         font=('Segoe UI', 8), bg=COLORS['bg_section'], fg=COLORS['text_muted']).pack(side=tk.LEFT, padx=10)

# Mouse drawing on line canvas
line_draw_state = {'start': None, 'rect': None}

def on_line_canvas_press(event):
    line_draw_state['start'] = (event.x, event.y)
    line_draw_state['rect'] = line_canvas.create_rectangle(0, event.y, line_canvas.winfo_width(), event.y, 
                                                            outline='blue', width=2, dash=(4, 2))

def on_line_canvas_drag(event):
    if line_draw_state['rect']:
        y1, y2 = line_draw_state['start'][1], event.y
        line_canvas.coords(line_draw_state['rect'], 
                          0, min(y1, y2), line_canvas.winfo_width(), max(y1, y2))

def on_line_canvas_release(event):
    if not line_draw_state['rect'] or not line_draw_state['start']:
        return
    line_canvas.delete(line_draw_state['rect'])
    y1_canvas = line_draw_state['start'][1]
    y2_canvas = event.y
    line_draw_state['start'] = None
    line_draw_state['rect'] = None
    
    # Convert canvas coords to image coords
    if hasattr(S, 'line_canvas_scale') and hasattr(S, 'line_canvas_offset'):
        scale = S.line_canvas_scale
        oy = S.line_canvas_offset[1]
        iy1 = int((min(y1_canvas, y2_canvas) - oy) / scale)
        iy2 = int((max(y1_canvas, y2_canvas) - oy) / scale)
        if iy2 - iy1 > 5:
            if not hasattr(S, 'detected_lines'):
                S.detected_lines = []
            # Use full image width for mouse-drawn lines
            img_w = S.line_display_img.shape[1] if hasattr(S, 'line_display_img') and S.line_display_img is not None else 0
            S.detected_lines.append((0, iy1, img_w, iy2))
            S.detected_lines.sort(key=lambda x: x[1] if len(x) == 4 else x[0])
            refresh_line_bbox_list()
            redraw_line_detection()

line_canvas.bind('<ButtonPress-1>', on_line_canvas_press)
line_canvas.bind('<B1-Motion>', on_line_canvas_drag)
line_canvas.bind('<ButtonRelease-1>', on_line_canvas_release)

line_btn_frame = tk.Frame(line_detect_container, bg=COLORS['bg_dark'])
line_btn_frame.pack(fill=tk.X, pady=(8, 0))

def back_to_image_view_from_line():
    if widget_exists(line_detect_container):
        line_detect_container.pack_forget()
    # Return to workflow if active, otherwise show appropriate container
    if getattr(S, 'workflow_active', False) and hasattr(S, 'workflow_manager') and widget_exists(S.workflow_manager.container):
        S.workflow_manager.container.pack(expand=True, fill=tk.BOTH)
        hide_sidebar()
    elif input_mode_var.get() == 'generate':
        if widget_exists(S.generate_htr_container):
            S.generate_htr_container.pack(expand=True, fill=tk.BOTH)
    else:
        if widget_exists(load_image_container):
            load_image_container.pack(expand=True, fill=tk.BOTH)
    # Enable all detection buttons
    if widget_exists(btn_save):
        btn_save.config(state='normal')
    if widget_exists(btn_line_detect):
        btn_line_detect.config(state='normal')
    if widget_exists(btn_char_detect):
        btn_char_detect.config(state='normal')
    # Reset segmentation mode to allow switching
    S.segmentation_mode = None
    segmentation_mode_var.set("Segmentation mode: Not selected")

def proceed_to_line_annotation():
    """Start line-by-line annotation in the annotation panel."""
    if widget_exists(S.line_detect_container):
        S.line_detect_container.pack_forget()
    if widget_exists(S.load_image_container):
        S.load_image_container.pack_forget()
    if widget_exists(S.generate_htr_container):
        S.generate_htr_container.pack_forget()
    if widget_exists(S.annotation_container):
        S.annotation_container.pack(expand=True, fill=tk.BOTH)
    
    # Disable line detection button while in annotation
    if widget_exists(btn_line_detect):
        btn_line_detect.config(state='disabled')
    S.current_annotation_mode = 'line'
    
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
S.btn_back_line_view = btn_back_line_view
S.line_info_label = line_info_label
S.line_bbox_listbox = line_bbox_listbox
S.refresh_line_bbox_list = refresh_line_bbox_list

# ============================================
# CONTAINER 2c: Character Detection Review (hidden until char detect)
# ============================================
char_detect_container = tk.Frame(content_frame, bg=COLORS['bg_dark'])
char_detect_container.pack_forget()

char_detect_header = tk.Label(char_detect_container, text=" 🔤 Character Detection ",
                              font=('Segoe UI', 12, 'bold'),
                              bg=COLORS['bg_section'], fg=COLORS['text_light'],
                              relief=tk.FLAT, bd=1, padx=10, pady=8)
char_detect_header.pack(fill=tk.X, pady=(0, 5))

# Word navigation frame
char_word_nav_frame = tk.Frame(char_detect_container, bg=COLORS['bg_section'])
char_word_nav_frame.pack(fill=tk.X, pady=(0, 10), padx=4)

tk.Label(char_word_nav_frame, text="📝 Word Image:", font=('Segoe UI', 10, 'bold'),
         bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT, padx=5)

char_word_label = tk.Label(char_word_nav_frame, text="0/0", font=('Segoe UI', 10),
                           bg=COLORS['bg_section'], fg=COLORS['accent'])
char_word_label.pack(side=tk.LEFT, padx=5)

def update_char_word_label():
    """Update the word navigation label."""
    idx = getattr(S, 'char_word_index', 0)
    total = getattr(S, 'char_total_words', 0)
    char_word_label.config(text=f"{idx + 1}/{total}")

S.update_char_word_label = update_char_word_label

btn_char_prev_word = tk.Button(char_word_nav_frame, text="◀ Prev Word", 
                               command=lambda: (char_prev_word(), update_char_word_label()),
                               bg=COLORS['accent'], fg='white', font=('Segoe UI', 9, 'bold'),
                               padx=10, pady=3, relief=tk.GROOVE)
btn_char_prev_word.pack(side=tk.LEFT, padx=5)

btn_char_next_word = tk.Button(char_word_nav_frame, text="Next Word ▶", 
                               command=lambda: (char_next_word(), update_char_word_label()),
                               bg=COLORS['accent'], fg='white', font=('Segoe UI', 9, 'bold'),
                               padx=10, pady=3, relief=tk.GROOVE)
btn_char_next_word.pack(side=tk.LEFT, padx=5)

# Main content area with image on left, zoom+list on right
char_main_frame = tk.Frame(char_detect_container, bg=COLORS['bg_dark'])
char_main_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

# Left panel: main image canvas
char_left_panel = tk.Frame(char_main_frame, bg=COLORS['bg_dark'])
char_left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Zoom and pan controls frame
char_zoom_controls = tk.Frame(char_left_panel, bg=COLORS['bg_dark'])
char_zoom_controls.pack(fill=tk.X, pady=(0, 5))

char_zoom_level = tk.DoubleVar(value=1.0)
char_pan_offset = {'x': 0, 'y': 0}
char_pan_mode = tk.BooleanVar(value=False)  # Pan/displace mode toggle

def char_zoom_in():
    """Zoom in on the character detection canvas."""
    current = char_zoom_level.get()
    if current < 5.0:
        char_zoom_level.set(min(current + 0.25, 5.0))
        update_char_canvas_zoom()

def char_zoom_out():
    """Zoom out on the character detection canvas."""
    current = char_zoom_level.get()
    if current > 0.25:
        char_zoom_level.set(max(current - 0.25, 0.25))
        update_char_canvas_zoom()

def char_zoom_reset():
    """Reset zoom to 100%."""
    char_zoom_level.set(1.0)
    char_pan_offset['x'] = 0
    char_pan_offset['y'] = 0
    update_char_canvas_zoom()

def toggle_pan_mode():
    """Toggle pan/displace mode."""
    if char_pan_mode.get():
        char_canvas.config(cursor='fleur')
        char_pan_btn.config(bg=COLORS['success'], relief=tk.SUNKEN)
    else:
        char_canvas.config(cursor='')
        char_pan_btn.config(bg=COLORS['bg_section'], relief=tk.RAISED)

def update_char_canvas_zoom():
    """Redraw the character canvas with current zoom level."""
    if not hasattr(S, 'char_image_path') or not S.char_image_path:
        return
    if not hasattr(S, 'char_detected_boxes'):
        S.char_detected_boxes = []
    
    img = cv2.imread(S.char_image_path)
    if img is not None:
        display_detected_characters_zoomed(img, S.char_detected_boxes)
    char_zoom_label.config(text=f"{int(char_zoom_level.get() * 100)}%")

def display_detected_characters_zoomed(img, detected_chars, highlight_idx=None):
    """Display image with zoom and pan support."""
    from PIL import ImageDraw, ImageFont
    
    canvas = S.char_detect_canvas
    canvas.delete('all')
    
    zoom = char_zoom_level.get()
    
    # Draw image with character boxes
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_with_chars = img_rgb.copy()
    
    # Draw rectangles around detected characters using OpenCV
    for i, char_info in enumerate(detected_chars):
        x1, y1, x2, y2 = char_info['coords']
        
        if i == highlight_idx:
            color = (0, 255, 0)
            thickness = 3
        else:
            color = (255, 100, 100)
            thickness = 2
        
        cv2.rectangle(img_with_chars, (x1, y1), (x2, y2), color, thickness)
    
    # Convert to PIL for text drawing (supports Arabic/Unicode)
    pil_img_for_text = Image.fromarray(img_with_chars)
    draw = ImageDraw.Draw(pil_img_for_text)
    
    # Try to load a font that supports Arabic, fall back to default
    try:
        font = ImageFont.truetype("segoeui.ttf", 14)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
    
    # Draw text labels using PIL
    for i, char_info in enumerate(detected_chars):
        x1, y1, x2, y2 = char_info['coords']
        label = char_info['label']
        
        if i == highlight_idx:
            text_color = (0, 255, 0)
        else:
            text_color = (255, 100, 100)
        
        # Draw text with background for better visibility
        text_y = max(0, y1 - 18)
        draw.text((x1, text_y), label, font=font, fill=text_color)
    
    img_with_chars = np.array(pil_img_for_text)
    
    h, w = img_with_chars.shape[:2]
    canvas_w, canvas_h = 600, 500
    
    # Apply zoom
    base_scale = min(canvas_w / w, canvas_h / h, 1.0)
    scale = base_scale * zoom
    new_w, new_h = int(w * scale), int(h * scale)
    
    img_resized = cv2.resize(img_with_chars, (new_w, new_h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    pil_img = Image.fromarray(img_resized)
    S.char_detect_photo = ImageTk.PhotoImage(pil_img)
    
    # Center with pan offset
    x_offset = (canvas_w - new_w) // 2 + char_pan_offset['x']
    y_offset = (canvas_h - new_h) // 2 + char_pan_offset['y']
    canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=S.char_detect_photo)
    
    # Store scale info for coordinate conversion
    S.char_canvas_scale = scale
    S.char_canvas_offset = (x_offset, y_offset)
    S.char_img_size = (w, h)
    
    if 'refresh_char_listbox' in dir():
        refresh_char_listbox()

# Zoom buttons
tk.Button(char_zoom_controls, text="➕", command=char_zoom_in,
          bg=COLORS['accent'], fg='white', font=('Segoe UI', 10, 'bold'),
          width=3, relief=tk.GROOVE).pack(side=tk.LEFT, padx=2)

tk.Button(char_zoom_controls, text="➖", command=char_zoom_out,
          bg=COLORS['accent'], fg='white', font=('Segoe UI', 10, 'bold'),
          width=3, relief=tk.GROOVE).pack(side=tk.LEFT, padx=2)

char_zoom_label = tk.Label(char_zoom_controls, text="100%", font=('Segoe UI', 10, 'bold'),
                           bg=COLORS['bg_dark'], fg=COLORS['text_light'], width=5)
char_zoom_label.pack(side=tk.LEFT, padx=5)

tk.Button(char_zoom_controls, text="⟲ Reset", command=char_zoom_reset,
          bg=COLORS['bg_section'], fg=COLORS['text_light'], font=('Segoe UI', 9),
          padx=8, relief=tk.GROOVE).pack(side=tk.LEFT, padx=5)

# Pan/Displace mode button
char_pan_btn = tk.Button(char_zoom_controls, text="✋ Pan", 
                         command=lambda: [char_pan_mode.set(not char_pan_mode.get()), toggle_pan_mode()],
                         bg=COLORS['bg_section'], fg=COLORS['text_light'], font=('Segoe UI', 9),
                         padx=8, relief=tk.RAISED)
char_pan_btn.pack(side=tk.LEFT, padx=5)

tk.Label(char_zoom_controls, text="(Scroll to zoom)", font=('Segoe UI', 8),
         bg=COLORS['bg_dark'], fg=COLORS['text_muted']).pack(side=tk.LEFT, padx=10)

char_canvas = tk.Canvas(char_left_panel, width=600, height=500,
                        bg='#eef2f7', highlightthickness=1, highlightbackground=COLORS['border'])
char_canvas.pack(fill=tk.BOTH, expand=True)

# Mouse wheel zoom on canvas
def on_char_canvas_scroll(event):
    if event.delta > 0:
        char_zoom_in()
    else:
        char_zoom_out()

char_canvas.bind('<MouseWheel>', on_char_canvas_scroll)

# Right panel: zoom window + character list
char_right_panel = tk.Frame(char_main_frame, bg=COLORS['bg_section'], width=280)
char_right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
char_right_panel.pack_propagate(False)

# Zoom window section
zoom_section = tk.LabelFrame(char_right_panel, text=" 🔍 Zoom View ", 
                             font=('Segoe UI', 10, 'bold'),
                             bg=COLORS['bg_section'], fg=COLORS['text_light'],
                             relief=tk.GROOVE, bd=1, padx=5, pady=5)
zoom_section.pack(fill=tk.X, padx=5, pady=5)

char_zoom_canvas = tk.Canvas(zoom_section, width=250, height=120,
                             bg='white', highlightthickness=1, highlightbackground=COLORS['border'])
char_zoom_canvas.pack(pady=5)

zoom_info_label = tk.Label(zoom_section, text="Click on a character to zoom",
                           font=('Segoe UI', 8), bg=COLORS['bg_section'], fg=COLORS['text_muted'])
zoom_info_label.pack()

# Character list section
list_section = tk.LabelFrame(char_right_panel, text=" 📋 Detected Characters ", 
                             font=('Segoe UI', 10, 'bold'),
                             bg=COLORS['bg_section'], fg=COLORS['text_light'],
                             relief=tk.GROOVE, bd=1, padx=5, pady=5)
list_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Listbox with scrollbar
char_list_frame = tk.Frame(list_section, bg=COLORS['bg_section'])
char_list_frame.pack(fill=tk.BOTH, expand=True)

char_list_scroll = tk.Scrollbar(char_list_frame)
char_list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

char_listbox = tk.Listbox(char_list_frame, font=('Segoe UI', 10), height=12,
                          yscrollcommand=char_list_scroll.set, selectmode=tk.SINGLE,
                          bg='white', fg=COLORS['text_light'], selectbackground=COLORS['accent'])
char_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
char_list_scroll.config(command=char_listbox.yview)

# Edit character label section
edit_frame = tk.Frame(list_section, bg=COLORS['bg_section'])
edit_frame.pack(fill=tk.X, pady=(5, 0))

tk.Label(edit_frame, text="Label:", font=('Segoe UI', 9),
         bg=COLORS['bg_section'], fg=COLORS['text_light']).pack(side=tk.LEFT)

char_edit_var = tk.StringVar()
char_edit_entry = tk.Entry(edit_frame, textvariable=char_edit_var, font=('Segoe UI', 10), width=10)
char_edit_entry.pack(side=tk.LEFT, padx=5)

def update_selected_char():
    """Update the label of the selected character."""
    selection = char_listbox.curselection()
    if not selection:
        from tkinter import messagebox
        messagebox.showinfo("Select Character", "Please select a character from the list first.")
        return
    
    idx = selection[0]
    new_label = char_edit_var.get().strip()
    if not new_label:
        from tkinter import messagebox
        messagebox.showwarning("Empty Label", "Please enter a label for the character.")
        return
    
    if hasattr(S, 'char_detected_boxes') and idx < len(S.char_detected_boxes):
        S.char_detected_boxes[idx]['label'] = new_label
        # Update listbox
        refresh_char_listbox()
        # Redraw image
        if hasattr(S, 'char_image_path'):
            img = cv2.imread(S.char_image_path)
            display_detected_characters(img, S.char_detected_boxes)
        from tkinter import messagebox
        messagebox.showinfo("Updated", f"Character label updated to '{new_label}'")

def delete_selected_char():
    """Delete the selected character from the list."""
    selection = char_listbox.curselection()
    if not selection:
        from tkinter import messagebox
        messagebox.showinfo("Select Character", "Please select a character from the list first.")
        return
    
    idx = selection[0]
    if hasattr(S, 'char_detected_boxes') and idx < len(S.char_detected_boxes):
        deleted = S.char_detected_boxes.pop(idx)
        # Update listbox
        refresh_char_listbox()
        # Redraw image
        if hasattr(S, 'char_image_path'):
            img = cv2.imread(S.char_image_path)
            display_detected_characters(img, S.char_detected_boxes)
        # Clear zoom
        char_zoom_canvas.delete('all')
        zoom_info_label.config(text="Character deleted")
        S.char_info_label.config(text=f"Deleted '{deleted['label']}'. {len(S.char_detected_boxes)} characters remaining.")

def refresh_char_listbox():
    """Refresh the character listbox with current detected boxes."""
    char_listbox.delete(0, tk.END)
    if hasattr(S, 'char_detected_boxes'):
        for i, char_info in enumerate(S.char_detected_boxes):
            label = char_info['label']
            score = char_info.get('score', 0)
            x1, y1, x2, y2 = char_info['coords']
            char_listbox.insert(tk.END, f"{i+1}. '{label}' ({x2-x1}x{y2-y1})")

def on_char_listbox_select(event):
    """Handle character selection from listbox - show zoom view."""
    selection = char_listbox.curselection()
    if not selection:
        return
    
    idx = selection[0]
    if hasattr(S, 'char_detected_boxes') and idx < len(S.char_detected_boxes):
        char_info = S.char_detected_boxes[idx]
        char_edit_var.set(char_info['label'])
        
        # Show zoomed view of the character
        show_char_zoom(char_info)
        
        # Highlight on main canvas
        highlight_char_on_canvas(idx)

def show_char_zoom(char_info):
    """Display zoomed view of a character in the zoom canvas."""
    if not hasattr(S, 'char_image_path') or not S.char_image_path:
        return
    
    try:
        x1, y1, x2, y2 = char_info['coords']
        label = char_info['label']
        
        # Load and crop the character region with some padding
        pil_img = Image.open(S.char_image_path)
        pad = 10
        crop_x1 = max(0, x1 - pad)
        crop_y1 = max(0, y1 - pad)
        crop_x2 = min(pil_img.width, x2 + pad)
        crop_y2 = min(pil_img.height, y2 + pad)
        
        char_crop = pil_img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        
        # Resize to fit zoom canvas while maintaining aspect ratio
        canvas_w, canvas_h = 250, 120
        crop_w, crop_h = char_crop.size
        scale = min(canvas_w / crop_w, canvas_h / crop_h, 3.0)  # Max 3x zoom
        new_w, new_h = int(crop_w * scale), int(crop_h * scale)
        
        char_resized = char_crop.resize((new_w, new_h), Image.LANCZOS)
        S.char_zoom_photo = ImageTk.PhotoImage(char_resized)
        
        char_zoom_canvas.delete('all')
        x_off = (canvas_w - new_w) // 2
        y_off = (canvas_h - new_h) // 2
        char_zoom_canvas.create_image(x_off, y_off, anchor=tk.NW, image=S.char_zoom_photo)
        
        # Draw bounding box contour on zoom view (accounting for padding)
        box_x1 = x_off + int((x1 - crop_x1) * scale)
        box_y1 = y_off + int((y1 - crop_y1) * scale)
        box_x2 = x_off + int((x2 - crop_x1) * scale)
        box_y2 = y_off + int((y2 - crop_y1) * scale)
        char_zoom_canvas.create_rectangle(
            box_x1, box_y1, box_x2, box_y2,
            outline='red', width=2
        )
        
        zoom_info_label.config(text=f"'{label}' - {x2-x1}x{y2-y1}px")
        
    except Exception as e:
        print(f"Zoom error: {e}")

def highlight_char_on_canvas(idx):
    """Highlight a specific character on the main canvas."""
    if not hasattr(S, 'char_detected_boxes') or idx >= len(S.char_detected_boxes):
        return
    
    # Redraw with highlight
    if hasattr(S, 'char_image_path'):
        img = cv2.imread(S.char_image_path)
        display_detected_characters(img, S.char_detected_boxes, highlight_idx=idx)

char_listbox.bind('<<ListboxSelect>>', on_char_listbox_select)

# Buttons frame for update/delete
char_edit_btn_frame = tk.Frame(list_section, bg=COLORS['bg_section'])
char_edit_btn_frame.pack(fill=tk.X, pady=(5, 0))

tk.Button(char_edit_btn_frame, text="✏️ Update", command=update_selected_char,
          bg=COLORS['accent'], fg='white', font=('Segoe UI', 9, 'bold'),
          padx=8, pady=3, relief=tk.GROOVE).pack(side=tk.LEFT, padx=2)

tk.Button(char_edit_btn_frame, text="🗑️ Delete", command=delete_selected_char,
          bg='#dc3545', fg='white', font=('Segoe UI', 9, 'bold'),
          padx=8, pady=3, relief=tk.GROOVE).pack(side=tk.LEFT, padx=2)

char_info_label = tk.Label(char_detect_container, text="",
                           font=('Segoe UI', 10), bg=COLORS['bg_dark'], fg=COLORS['text_light'])
char_info_label.pack(fill=tk.X, pady=(4, 0))

# Template drawing controls
char_controls_frame = tk.Frame(char_detect_container, bg=COLORS['bg_dark'])
char_controls_frame.pack(fill=tk.X, pady=(4, 0))

char_draw_mode = tk.BooleanVar(value=False)
char_threshold_var = tk.DoubleVar(value=0.6)

def toggle_char_draw_mode():
    if char_draw_mode.get():
        char_canvas.config(cursor='crosshair')
        S.char_info_label.config(text="Draw mode ON: Click and drag to draw a bounding box around a character.")
    else:
        char_canvas.config(cursor='')
        if hasattr(S, 'char_detected_boxes'):
            count = len(S.char_detected_boxes)
            S.char_info_label.config(text=f"Draw mode OFF. {count} characters detected.")

tk.Checkbutton(char_controls_frame, text="✏️ Draw Template Box", variable=char_draw_mode,
               command=toggle_char_draw_mode, bg=COLORS['bg_dark'], fg=COLORS['text_light'],
               selectcolor=COLORS['bg_section'], activebackground=COLORS['bg_dark'],
               font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=10)

tk.Label(char_controls_frame, text="Threshold:", font=('Segoe UI', 9),
         bg=COLORS['bg_dark'], fg=COLORS['text_light']).pack(side=tk.LEFT, padx=(20, 5))
tk.Scale(char_controls_frame, from_=0.3, to=0.95, resolution=0.05, orient=tk.HORIZONTAL,
         variable=char_threshold_var, length=120, bg=COLORS['bg_dark'], fg=COLORS['text_light'],
         troughcolor=COLORS['bg_section'], highlightthickness=0).pack(side=tk.LEFT)

def rematch_characters():
    """Re-run template matching with current threshold."""
    if hasattr(S, 'char_image_path') and S.char_image_path:
        detect_characters()

tk.Button(char_controls_frame, text="🔄 Re-match", command=rematch_characters,
          bg=COLORS['bg_section'], fg=COLORS['text_light'], padx=8, pady=2).pack(side=tk.LEFT, padx=10)

char_btn_frame = tk.Frame(char_detect_container, bg=COLORS['bg_dark'])
char_btn_frame.pack(fill=tk.X, pady=(8, 0))

def back_to_image_view_from_char():
    if widget_exists(char_detect_container):
        char_detect_container.pack_forget()
    # Return to workflow if active, otherwise show appropriate container
    if getattr(S, 'workflow_active', False) and hasattr(S, 'workflow_manager') and widget_exists(S.workflow_manager.container):
        S.workflow_manager.container.pack(expand=True, fill=tk.BOTH)
        hide_sidebar()
    elif input_mode_var.get() == 'generate':
        if widget_exists(S.generate_htr_container):
            S.generate_htr_container.pack(expand=True, fill=tk.BOTH)
    else:
        if widget_exists(load_image_container):
            load_image_container.pack(expand=True, fill=tk.BOTH)
    # Enable all detection buttons
    if widget_exists(btn_save):
        btn_save.config(state='normal')
    if widget_exists(btn_line_detect):
        btn_line_detect.config(state='normal')
    if widget_exists(btn_char_detect):
        btn_char_detect.config(state='normal')
    # Reset segmentation mode to allow switching
    S.segmentation_mode = None
    segmentation_mode_var.set("Segmentation mode: Not selected")

def proceed_to_char_annotation():
    """Start character annotation in the annotation panel."""
    if widget_exists(S.char_detect_container):
        S.char_detect_container.pack_forget()
    if widget_exists(S.load_image_container):
        S.load_image_container.pack_forget()
    if widget_exists(S.generate_htr_container):
        S.generate_htr_container.pack_forget()
    if widget_exists(S.annotation_container):
        S.annotation_container.pack(expand=True, fill=tk.BOTH)
    
    # Disable character detection button while in annotation
    if widget_exists(btn_char_detect):
        btn_char_detect.config(state='disabled')
    S.current_annotation_mode = 'character'
    
    # Start embedded character annotation
    from actions.character_annotate import start_embedded_character_annotation
    if hasattr(S, 'char_image_path') and hasattr(S, 'char_detected_boxes'):
        start_embedded_character_annotation(S.char_image_path, S.char_detected_boxes, S.char_templates)

btn_back_char_view = tk.Button(char_btn_frame, text="⬅ Back to image view", command=back_to_image_view_from_char,
                          bg=COLORS['bg_section'], fg=COLORS['text_light'], padx=10, pady=6)
btn_back_char_view.pack(side=tk.LEFT, padx=4)

btn_proceed_char_annotation = tk.Button(char_btn_frame, text="Proceed to annotation", command=proceed_to_char_annotation,
                                   bg=COLORS['accent'], fg='white', padx=12, pady=6)
btn_proceed_char_annotation.pack(side=tk.RIGHT, padx=4)

S.btn_back_char_view = btn_back_char_view

# Bounding box drawing on char canvas
char_drag_state = {'rect': None, 'start': None}
char_pan_state = {'dragging': False, 'start_x': 0, 'start_y': 0}

def char_canvas_to_image_coords(canvas_x, canvas_y):
    """Convert canvas coordinates to image coordinates."""
    if not hasattr(S, 'char_canvas_scale') or not hasattr(S, 'char_canvas_offset'):
        return canvas_x, canvas_y
    scale = S.char_canvas_scale
    x_off, y_off = S.char_canvas_offset
    img_x = int((canvas_x - x_off) / scale)
    img_y = int((canvas_y - y_off) / scale)
    return img_x, img_y

def on_char_canvas_press(event):
    # Handle pan mode first
    if char_pan_mode.get():
        char_pan_state['dragging'] = True
        char_pan_state['start_x'] = event.x
        char_pan_state['start_y'] = event.y
        return
    
    if not char_draw_mode.get():
        # Click to select character when not in draw mode
        img_x, img_y = char_canvas_to_image_coords(event.x, event.y)
        
        # Find which character was clicked
        if hasattr(S, 'char_detected_boxes'):
            for i, char_info in enumerate(S.char_detected_boxes):
                x1, y1, x2, y2 = char_info['coords']
                if x1 <= img_x <= x2 and y1 <= img_y <= y2:
                    # Select this character in listbox
                    char_listbox.selection_clear(0, tk.END)
                    char_listbox.selection_set(i)
                    char_listbox.see(i)
                    # Trigger selection event
                    on_char_listbox_select(None)
                    break
        return
    
    char_drag_state['start'] = (event.x, event.y)
    char_drag_state['rect'] = char_canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)

def on_char_canvas_drag(event):
    # Handle pan mode
    if char_pan_mode.get() and char_pan_state['dragging']:
        dx = event.x - char_pan_state['start_x']
        dy = event.y - char_pan_state['start_y']
        char_pan_offset['x'] += dx
        char_pan_offset['y'] += dy
        char_pan_state['start_x'] = event.x
        char_pan_state['start_y'] = event.y
        update_char_canvas_zoom()
        return
    
    if not char_draw_mode.get() or not char_drag_state['rect']:
        return
    char_canvas.coords(char_drag_state['rect'], char_drag_state['start'][0], char_drag_state['start'][1], event.x, event.y)
    
    # Show live preview in zoom view while drawing
    try:
        x1d, y1d = char_drag_state['start']
        x2d, y2d = event.x, event.y
        
        # Convert to image coordinates
        ix1, iy1 = char_canvas_to_image_coords(x1d, y1d)
        ix2, iy2 = char_canvas_to_image_coords(x2d, y2d)
        x1i, y1i = min(ix1, ix2), min(iy1, iy2)
        x2i, y2i = max(ix1, ix2), max(iy1, iy2)
        
        # Only update if box is big enough
        if x2i - x1i > 3 and y2i - y1i > 3 and hasattr(S, 'char_image_path') and S.char_image_path:
            pil_img = Image.open(S.char_image_path)
            
            # Clamp to image bounds
            x1i = max(0, x1i)
            y1i = max(0, y1i)
            x2i = min(pil_img.width, x2i)
            y2i = min(pil_img.height, y2i)
            
            char_crop = pil_img.crop((x1i, y1i, x2i, y2i))
            
            # Resize to fit zoom canvas
            canvas_w, canvas_h = 250, 120
            crop_w, crop_h = char_crop.size
            if crop_w > 0 and crop_h > 0:
                scale = min(canvas_w / crop_w, canvas_h / crop_h, 3.0)
                new_w, new_h = int(crop_w * scale), int(crop_h * scale)
                
                char_resized = char_crop.resize((new_w, new_h), Image.LANCZOS)
                S.char_zoom_photo = ImageTk.PhotoImage(char_resized)
                
                char_zoom_canvas.delete('all')
                x_off = (canvas_w - new_w) // 2
                y_off = (canvas_h - new_h) // 2
                char_zoom_canvas.create_image(x_off, y_off, anchor=tk.NW, image=S.char_zoom_photo)
                
                # Draw bounding box contour on zoom view
                char_zoom_canvas.create_rectangle(
                    x_off, y_off, x_off + new_w, y_off + new_h,
                    outline='red', width=2
                )
                
                zoom_info_label.config(text=f"Drawing: {x2i-x1i}x{y2i-y1i}px")
    except Exception as e:
        pass  # Ignore errors during live preview

def on_char_canvas_release(event):
    # Handle pan mode release
    if char_pan_mode.get():
        char_pan_state['dragging'] = False
        return
    
    if not char_draw_mode.get() or not char_drag_state['rect']:
        return
    
    from tkinter import simpledialog
    
    x1d, y1d = char_drag_state['start']
    x2d, y2d = event.x, event.y
    char_canvas.delete(char_drag_state['rect'])
    char_drag_state['rect'] = None
    char_drag_state['start'] = None
    
    # Convert to image coordinates
    ix1, iy1 = char_canvas_to_image_coords(x1d, y1d)
    ix2, iy2 = char_canvas_to_image_coords(x2d, y2d)
    x1i, y1i = min(ix1, ix2), min(iy1, iy2)
    x2i, y2i = max(ix1, ix2), max(iy1, iy2)
    
    # Validate box size
    if x2i - x1i < 5 or y2i - y1i < 5:
        return
    
    # Ask for character label
    label = simpledialog.askstring("Character Label", "Enter character for this template:")
    if not label:
        return
    
    # Save template image
    try:
        templates_dir = os.path.join(os.path.dirname(__file__), 'character_templates')
        os.makedirs(templates_dir, exist_ok=True)
        
        pil_img = Image.open(S.char_image_path)
        template_crop = pil_img.crop((x1i, y1i, x2i, y2i))
        
        # Save with label as filename (handle special chars)
        safe_label = label.replace('/', '_').replace('\\', '_').replace(':', '_')
        template_path = os.path.join(templates_dir, f"{safe_label}.png")
        template_crop.save(template_path)
        
        # Add to detected boxes
        if not hasattr(S, 'char_detected_boxes'):
            S.char_detected_boxes = []
        S.char_detected_boxes.append({
            'coords': (x1i, y1i, x2i, y2i),
            'label': label,
            'score': 1.0
        })
        
        # Add to templates list
        if not hasattr(S, 'char_templates'):
            S.char_templates = []
        S.char_templates.append({'label': label, 'path': template_path})
        
        # Redraw
        img = cv2.imread(S.char_image_path)
        display_detected_characters(img, S.char_detected_boxes)
        
        # Refresh listbox
        refresh_char_listbox()
        
        S.char_info_label.config(text=f"Template '{label}' saved! {len(S.char_detected_boxes)} characters total. Click Re-match to find more.")
        
        from tkinter import messagebox
        messagebox.showinfo("Template Saved", f"Character template '{label}' saved.\nClick 'Re-match' to find similar characters.")
        
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Error", f"Failed to save template: {e}")

char_canvas.bind('<ButtonPress-1>', on_char_canvas_press)
char_canvas.bind('<B1-Motion>', on_char_canvas_drag)
char_canvas.bind('<ButtonRelease-1>', on_char_canvas_release)

# Store in state
S.char_detect_container = char_detect_container
S.char_detect_canvas = char_canvas
S.char_info_label = char_info_label
S.char_threshold_var = char_threshold_var
S.char_zoom_canvas = char_zoom_canvas
S.char_listbox = char_listbox
S.refresh_char_listbox = refresh_char_listbox
S.show_char_zoom = show_char_zoom
S.char_zoom_level = char_zoom_level
S.char_pan_offset = char_pan_offset
S.char_pan_mode = char_pan_mode

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
                             font=('Segoe UI', 10), bg='white', fg='#333',
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

input_text_area = tk.Text(text_frame, width=80, height=6, font=('Segoe UI', 11),
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
        if S.shortcuts_enabled:
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
            from actions.character_annotate import character_annotate
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

# Export detection functions so the workflow annotation panel can call them
S._workflow_detect_words = detect_words_with_mode_lock
S._workflow_detect_lines = detect_lines_with_autofill
S._workflow_detect_chars = detect_characters

# Show startup message
update_status("Ready | Press F1 for shortcuts")
        
window.mainloop()
