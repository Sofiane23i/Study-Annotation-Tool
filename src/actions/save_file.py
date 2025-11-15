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
    print(S.list_of_files[S.pos])
    shutil.copy(S.list_of_files[S.pos], dst_dir)

    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    args = parser.parse_args([])  # avoid consuming argv of the main app/window

    net = WordDetectorNet()
    net.load_state_dict(torch.load('../model/weights', map_location=args.device))
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
    for i, (_img, _aabbs) in enumerate(zip(res.batch_imgs, res.batch_aabbs)):
        listoflist = []
        finallistoflist = []
        f = loader.get_scale_factor(i)
        aabbs = [aabb.scale(1 / f, 1 / f) for aabb in _aabbs]
        img = loader.get_original_img(i)
        immg = loader.get_original_img_rgb(i)
        print(img.shape)
        break

    for ii in aabbs:
        listoflist.append([ii.xmin, ii.ymin, ii.xmax, ii.ymax])
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
    S.label.configure(image=img2)
    S.label.image = img2

    files = glob.glob(S.directorytmp + '/*')
    for f in files:
        os.remove(f)

    if S.btn_save:
        S.btn_save["state"] = "disabled"
    if S.btn_annotate:
        S.btn_annotate["state"] = "normal"
