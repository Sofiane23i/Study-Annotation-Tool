import os, shutil, argparse, glob
import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
import torch
from dataloader import DataLoaderImgFile
from net import WordDetectorNet
from eval import evaluate
from path import Path
import state as S
from actions.annotate import annotate


def save_file():
    print(S.pos)
    
    # Show progress
    if hasattr(S, 'show_progress'):
        S.show_progress(5, "Starting word detection...")

    S.finalrowsbbx = []
    src_dir = S.pathDirectory
    dst_dir = S.directorytmp
    
    # Check input mode to determine image source
    current_mode = S.input_mode_var.get() if hasattr(S, 'input_mode_var') else 'load'
    
    use_gan_image = False
    source_image_path = None

    if current_mode == 'generate':
        # Generate mode: use GAN generated images
        if hasattr(S, 'gan_batch_images') and S.gan_batch_images:
            gan_idx = getattr(S, 'gan_batch_index', 0)
            if gan_idx < len(S.gan_batch_images):
                source_image_path = S.gan_batch_images[gan_idx]
                print(f"Using GAN batch image: {source_image_path}")
                use_gan_image = True
        
        # Fallback to temp_handwriting.jpg if no batch images
        if not source_image_path:
            gan_jpg_path = os.path.join(os.path.dirname(__file__), '..', 'temp_handwriting.jpg')
            gan_jpg_path = os.path.abspath(gan_jpg_path)
            if os.path.exists(gan_jpg_path):
                source_image_path = gan_jpg_path
                print(f"Using GAN-generated image: {gan_jpg_path}")
                use_gan_image = True
    else:
        # Load mode: use loaded images
        if S.list_of_files and len(S.list_of_files) > S.pos:
            source_image_path = S.list_of_files[S.pos]
            print(f"Using loaded image: {source_image_path}")
    
    if not source_image_path or not os.path.exists(source_image_path):
        print("No image available for word detection")
        return
    
    # Create temp directories if not already set up
    if not S.directorytmp or not os.path.exists(S.directorytmp):
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'gan_output_data')
        S.directorytmp = os.path.abspath(os.path.join(base_dir, 'tmp'))
        S.directoryout = os.path.abspath(os.path.join(base_dir, 'out'))
        os.makedirs(S.directorytmp, exist_ok=True)
        os.makedirs(S.directoryout, exist_ok=True)
        dst_dir = S.directorytmp
    
    # Apply scale to image before saving to temp directory
    scale = getattr(S, 'image_scale', 1.0)
    print(f"Applying image scale: {scale}")
    
    # Load and scale the image
    source_img = Image.open(source_image_path)
    if scale != 1.0:
        new_width = int(source_img.width * scale)
        new_height = int(source_img.height * scale)
        source_img = source_img.resize((new_width, new_height), Image.LANCZOS)
    
    # Save scaled image to temp directory (convert to RGB to ensure
    # compatibility — JPEG does not support alpha / palette modes)
    scaled_img_path = os.path.join(dst_dir, 'scaled_input.jpg')
    if source_img.mode not in ('RGB', 'L'):
        source_img = source_img.convert('RGB')
    source_img.save(scaled_img_path, 'JPEG', quality=95)

    # Update progress
    if hasattr(S, 'show_progress'):
        S.show_progress(20, "Loading detection model...")

    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    args = parser.parse_args([])  # avoid consuming argv of the main app/window

    # Use absolute path for model weights
    model_weights_path = os.path.join(os.path.dirname(__file__), '..', '..', 'model', 'weights')
    model_weights_path = os.path.abspath(model_weights_path)
    
    net = WordDetectorNet()
    net.load_state_dict(torch.load(model_weights_path, map_location=args.device))
    net.eval()
    net.to(args.device)

    # Update progress
    if hasattr(S, 'show_progress'):
        S.show_progress(40, "Detecting words...")

    loader = DataLoaderImgFile(Path(S.directorytmp), net.input_size, args.device)
    res = evaluate(net, loader, max_aabbs=1000)

    # Update progress
    if hasattr(S, 'show_progress'):
        S.show_progress(60, "Processing bounding boxes...")

    print(res.batch_imgs)
    print(res.batch_aabbs)
    # take the first (and only) image from loader
    img = None
    aabbs = None
    immg = None
    
    # Get padding value from state
    padding = getattr(S, 'bbox_padding', 0)
    print(f"Applying bounding box padding: {padding}")
    
    for i, (_img, _aabbs) in enumerate(zip(res.batch_imgs, res.batch_aabbs)):
        listoflist = []
        finallistoflist = []
        f = loader.get_scale_factor(i)
        aabbs = [aabb.scale(1 / f, 1 / f) for aabb in _aabbs]
        img = loader.get_original_img(i)
        immg = loader.get_original_img_rgb(i)
        print(img.shape)
        break

    # Get image dimensions for bounds checking
    img_height, img_width = img.shape[:2]

    for ii in aabbs:
        # Apply padding to bounding boxes
        xmin = max(0, ii.xmin - padding)
        ymin = max(0, ii.ymin - padding)
        xmax = min(img_width, ii.xmax + padding)
        ymax = min(img_height, ii.ymax + padding)
        listoflist.append([xmin, ymin, xmax, ymax])
        listoflist2 = sorted(listoflist, key=lambda x: (x[1]))
        listoflist3 = sorted(listoflist, key=lambda x: (x[0]))
        listoflist22 = listoflist2

    while len(listoflist2) > 0:
        topleftbbx = []
        downrightbbx = []
        xmin = listoflist2[0][0]
        xmax = xmin
        yxmin = listoflist2[0][1]
        for jj in listoflist2:
            if (jj[0] <= xmin and abs(jj[1] - yxmin) < 17):
                topleftbbx = jj
                xmin = jj[0]
                ymin = jj[1]
        firstrowbbx = []
        firstrowbbx.append(topleftbbx)
        for jj in listoflist2:
            if (jj[0] > topleftbbx[0] and abs(jj[1] - topleftbbx[1]) < 17):
                firstrowbbx.append(jj)
        # Sort based on text direction (RTL vs LTR)
        if getattr(S, 'text_direction', 'ltr') == 'rtl':
            firstrowbbx = sorted(firstrowbbx, key=lambda x: -x[0])  # Right to left
        else:
            firstrowbbx = sorted(firstrowbbx, key=lambda x: x[0])   # Left to right
        for ii in firstrowbbx:
            S.finalrowsbbx.append(ii)
            listoflist2.remove(ii)

    # Update progress
    if hasattr(S, 'show_progress'):
        S.show_progress(80, "Previewing results...")

    from visualization import visualize
    imgplot = visualize(img, aabbs)
    PIL_image = Image.fromarray(np.uint8(imgplot)).convert('RGB')

    def perform_cropping(boxes):
        # Save cropped words based on current boxes selection
        if hasattr(S, 'show_progress'):
            S.show_progress(85, "Cropping words...")
        files = glob.glob(S.directoryout + '/*')
        for f in files:
            os.remove(f)
        for ii in boxes:
            if len(ii) == 4:
                # Check if format is (x, y, w, h) or (xmin, ymin, xmax, ymax)
                if ii[2] < img_width // 2 and ii[3] < img_height // 2:
                    # Likely (x, y, w, h) format
                    box = (ii[0], ii[1], ii[0] + ii[2], ii[1] + ii[3])
                else:
                    # Likely (xmin, ymin, xmax, ymax) format
                    box = (ii[0], ii[1], ii[2], ii[3])
                crop = immg.crop(box)
                S.nbr = S.nbr + 1
                crop.save(S.directoryout + '/%s.png' % (S.nbr - 1), 'png')
        if hasattr(S, 'show_progress'):
            S.show_progress(90, f"Cropped {len(boxes)} words")

    # Convert bboxes to (x, y, w, h) format for the new interface
    word_bboxes = []
    for bbox in S.finalrowsbbx:
        xmin, ymin, xmax, ymax = bbox
        word_bboxes.append((xmin, ymin, xmax - xmin, ymax - ymin))
    
    S.word_bboxes = word_bboxes
    S.word_detect_boxes = S.finalrowsbbx[:]
    S.detection_scale = scale  # remember scale used during detection

    # Use the new display function if available (stored in state to avoid circular import)
    if hasattr(S, 'word_detect_canvas') and S.word_detect_canvas:
        # Store the original image (BGR) for the display function
        import cv2
        S.word_display_img = cv2.cvtColor(np.array(immg), cv2.COLOR_RGB2BGR)
        
        # Call the display function from state (set by annotationgui.py)
        if hasattr(S, 'display_word_bboxes_func') and S.display_word_bboxes_func:
            S.display_word_bboxes_func(S.word_display_img, S.word_bboxes)
        else:
            # Fallback to old display method
            canvas = S.word_detect_canvas
            canvas.delete('all')
            display = PIL_image.resize((600, 450))
            photo = ImageTk.PhotoImage(display)
            canvas.photo = photo
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            S.word_detect_photo = photo

    S.word_detect_image = PIL_image
    
    def perform_cropping_from_bboxes():
        # Convert current word_bboxes back to xmin,ymin,xmax,ymax format
        boxes = []
        for (x, y, w, h) in S.word_bboxes:
            boxes.append([x, y, x + w, y + h])
        perform_cropping(boxes)
    
    S.perform_cropping_current_detection = perform_cropping_from_bboxes

    files = glob.glob(S.directorytmp + '/*')
    for f in files:
        os.remove(f)

    # Update progress - complete
    if hasattr(S, 'show_progress'):
        S.show_progress(100, f"Detected {len(S.finalrowsbbx)} words")
    if hasattr(S, 'update_status') and S.update_status:
        S.update_status(f"Detected {len(S.finalrowsbbx)} words | Ready to annotate")

    # Keep detect words enabled so user can retry with different scale
    if S.btn_annotate:
        S.btn_annotate["state"] = "normal"
    if S.btn_htr:
        S.btn_htr["state"] = "disabled"
    if S.btn_open:
        S.btn_open["state"] = "disabled"
    
    # Enable character detection button now that words are detected
    if hasattr(S, 'btn_char_detect') and S.btn_char_detect:
        S.btn_char_detect["state"] = "normal"
    
    # Store word image paths for character detection
    S.word_image_paths = []
    if hasattr(S, 'directoryout') and os.path.exists(S.directoryout):
        word_files = sorted(glob.glob(os.path.join(S.directoryout, '*.png')),
                           key=lambda x: int(os.path.splitext(os.path.basename(x))[0]) if os.path.splitext(os.path.basename(x))[0].isdigit() else 0)
        S.word_image_paths = word_files
