import os, shutil, argparse, glob
from PIL import Image, ImageTk
import numpy as np
import torch
from dataloader import DataLoaderImgFile
from net import WordDetectorNet
from eval import evaluate
from path import Path
import state as S


def save_file():
    print(S.pos)

    S.finalrowsbbx = []
    src_dir = S.pathDirectory
    dst_dir = S.directorytmp
    
    # Check if we have a loaded image or if we should use GAN-generated image
    gan_jpg_path = os.path.join(os.path.dirname(__file__), '..', 'temp_handwriting.jpg')
    gan_jpg_path = os.path.abspath(gan_jpg_path)

    # Prefer first JPG from gan_output_data/batch if available
    batch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gan_output_data', 'batch'))
    batch_jpgs = sorted(glob.glob(os.path.join(batch_dir, '*.jpg')))

    use_gan_image = False
    source_image_path = None

    if S.list_of_files and len(S.list_of_files) > S.pos:
        # Use loaded image
        source_image_path = S.list_of_files[S.pos]
        print(source_image_path)
    elif batch_jpgs:
        # Use first GAN batch JPG
        source_image_path = os.path.abspath(batch_jpgs[0])
        print(f"Using GAN batch image: {source_image_path}")
        use_gan_image = True
    elif os.path.exists(gan_jpg_path):
        # Use fallback GAN temporary image
        source_image_path = gan_jpg_path
        print(f"Using GAN-generated image: {gan_jpg_path}")
        use_gan_image = True
    else:
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
    
    # Save scaled image to temp directory
    scaled_img_path = os.path.join(dst_dir, 'scaled_input.jpg')
    source_img.save(scaled_img_path, 'JPEG', quality=95)

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

    loader = DataLoaderImgFile(Path(S.directorytmp), net.input_size, args.device)
    res = evaluate(net, loader, max_aabbs=1000)

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
        firstrowbbx = sorted(firstrowbbx, key=lambda x: (x[0]))
        for ii in firstrowbbx:
            S.finalrowsbbx.append(ii)
            listoflist2.remove(ii)

    files = glob.glob(S.directoryout + '/*')
    for f in files:
        os.remove(f)

    for ii in S.finalrowsbbx:
        box = (ii[0], ii[1], ii[2], ii[3])
        crop = immg.crop(box)
        S.nbr = S.nbr + 1
        crop.save(S.directoryout + '/%s.png' % (S.nbr - 1), 'png')

    from visualization import visualize
    imgplot = visualize(img, aabbs)
    PIL_image = Image.fromarray(np.uint8(imgplot)).convert('RGB')

    img2 = ImageTk.PhotoImage(PIL_image.resize((800, 800)))
    
    # Create or recreate label if it doesn't exist or was destroyed
    import tkinter as tk
    try:
        if S.label is None:
            raise ValueError("Label is None")
        # Check if widget still exists
        S.label.winfo_exists()
        S.label.configure(image=img2)
    except (tk.TclError, ValueError):
        # Label was destroyed or doesn't exist, create a new one
        # Clear any existing children in txt_edit
        for widget in S.txt_edit.winfo_children():
            widget.destroy()
        S.label = tk.Label(S.txt_edit, image=img2)
        S.label.grid(row=0, column=0)
    
    S.label.image = img2

    files = glob.glob(S.directorytmp + '/*')
    for f in files:
        os.remove(f)

    # Keep detect words enabled so user can retry with different scale
    if S.btn_annotate:
        S.btn_annotate["state"] = "normal"
    if S.btn_htr:
        S.btn_htr["state"] = "disabled"
    if S.btn_open:
        S.btn_open["state"] = "disabled"
