import os, glob
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import state as S

def init_pathandfolders():
    folder_selected = filedialog.askdirectory()
    if not folder_selected:
        return
    print(folder_selected)

    S.pathDirectory = folder_selected
    S.pos = 0

    # List images (support multiple formats)
    S.list_of_files = sorted(filter(os.path.isfile, 
        glob.glob(S.pathDirectory + '/*.jpg') + 
        glob.glob(S.pathDirectory + '/*.jpeg') + 
        glob.glob(S.pathDirectory + '/*.png') + 
        glob.glob(S.pathDirectory + '/*.bmp') +
        glob.glob(S.pathDirectory + '/*.tiff')
    ))
    
    if not S.list_of_files:
        messagebox.showwarning("No Images", f"No image files found in:\n{folder_selected}")
        return

    print(f"Found {len(S.list_of_files)} images")

    # Update preview using new system
    if hasattr(S, 'update_preview_image') and S.update_preview_image:
        S.update_preview_image(S.list_of_files[S.pos])
    else:
        # Fallback to old label system
        img2 = ImageTk.PhotoImage(Image.open(S.list_of_files[S.pos]).resize((800, 800)))
        S.label.configure(image=img2)
        S.label.image = img2
    
    # Update image info
    if hasattr(S, 'image_info_var'):
        S.image_info_var.set(f"Image 1 of {len(S.list_of_files)} | {os.path.basename(S.list_of_files[S.pos])}")
    
    # Update status
    if hasattr(S, 'update_status') and S.update_status:
        S.update_status(f"Loaded {len(S.list_of_files)} images from {os.path.basename(folder_selected)}")

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
    if hasattr(S, 'btn_open') and S.btn_open:
        S.btn_open["state"] = "disabled"
    if hasattr(S, 'btn_annotate') and S.btn_annotate:
        S.btn_annotate["state"] = "normal"
    if hasattr(S, 'btn_save') and S.btn_save:
        S.btn_save["state"] = "normal"
    if hasattr(S, 'scale_slider') and S.scale_slider:
        S.scale_slider["state"] = "normal"
    if hasattr(S, 'padding_slider') and S.padding_slider:
        S.padding_slider["state"] = "normal"
    if hasattr(S, 'btn_prev') and S.btn_prev:
        S.btn_prev["state"] = "disabled"
    if hasattr(S, 'btn_next') and S.btn_next:
        S.btn_next["state"] = "normal" if len(S.list_of_files) > 1 else "disabled"
    if hasattr(S, 'btn_line_detect') and S.btn_line_detect:
        S.btn_line_detect["state"] = "normal"
