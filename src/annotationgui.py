from http.client import OK
import os
import tkinter as tk
from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import Image, ImageTk
import argparse
from net import WordDetectorNet
import torch
from dataloader import DataLoaderImgFile
from path import Path
from eval import evaluate
from visualization import visualize_and_plot, visualize
import numpy as np
from tkinter import filedialog
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
#from pathlib import Path

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
else:    
    nbrout = 0
    nbr = 0
    ind2 = 0 #having same name of image in IAM txt file

pos = 0 #order listfile
    
#pathDirectory = '../data/testpng/'


def init_pathandfolders():
    folder_selected = filedialog.askdirectory()
    print(folder_selected)
    global pathDirectory
    global pos
    global list_of_files
    
    global directoryout
    global directorytmp
    global directorydone
    
    
    pathDirectory = folder_selected
    
    for filename in os.listdir(pathDirectory):
        print(filename)

    list_of_files = sorted( filter( os.path.isfile, glob.glob(pathDirectory + '/*.jpg' ) ))
    #list_of_files = sorted( filter( os.path.isfile, glob.glob(pathDirectory + '/*.png' ) ))
    for file_path in list_of_files:
        print(file_path)
    
    print(list_of_files[0])

    print(os.listdir(pathDirectory)[0])
    print(len(os.listdir(pathDirectory)))
    
    print(list_of_files[pos])
    #img1= ImageTk.PhotoImage(Image.open('../data/testpng/'+os.listdir(pathDirectory)[pos]).resize((800,800)))
    img2=ImageTk.PhotoImage(Image.open(list_of_files[pos]).resize((800,800)))
    label.configure(image=img2)
    label.image=img2
    
    directoryout = pathDirectory+"_data/out/"
    if not os.path.exists(directoryout):
        os.makedirs(directoryout)
        
    directorytmp = pathDirectory+"_data/tmp/"
    if not os.path.exists(directorytmp):
        os.makedirs(directorytmp)
        
    directorydone = pathDirectory+"_data/done/"
    if not os.path.exists(directorydone):
        os.makedirs(directorydone)         
    
    btn_open["state"] = "disabled"
    btn_annotate["state"] = "disabled"
    btn_save["state"] = "normal"

def save_file():
    
    global pos
    global finalrowsbbx
    global pathDirectory
    global list_of_files
    
    global directoryout
    global directorytmp
    global directorydone
    
    print(pos)
    #pathDirectory = '../data/testpng/'
    
    finalrowsbbx = [] 
    src_dir = pathDirectory
    #dst_dir = '../data/testpngtmp/'
    dst_dir = directorytmp
    #shutil.copy('../data/testpng/'+os.listdir(pathDirectory)[pos], dst_dir)
    print(list_of_files[pos])
    shutil.copy(list_of_files[pos], dst_dir)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    args = parser.parse_args()

    net = WordDetectorNet()
    net.load_state_dict(torch.load('../model/weights', map_location=args.device))
    net.eval()
    net.to(args.device)
    
    #loader = DataLoaderImgFile(Path('../data/testpngtmp/'), net.input_size, args.device)
    loader = DataLoaderImgFile(Path(directorytmp), net.input_size, args.device)
    res = evaluate(net, loader, max_aabbs=1000)
    
    #print(enumerate(zip(res.batch_imgs, res.batch_aabbs)).list())
    
    print(res.batch_imgs)
    print(res.batch_aabbs)
    for i, (img, aabbs) in enumerate(zip(res.batch_imgs, res.batch_aabbs)):
           
        listoflist = []
        finallistoflist = [] 
       
        f = loader.get_scale_factor(i)
        aabbs = [aabb.scale(1 / f, 1 / f) for aabb in aabbs]
        
        img = loader.get_original_img(i)
        immg = loader.get_original_img_rgb(i)
        
        print(img.shape)
    
    for ii in aabbs:
        listoflist.append([ii.xmin,ii.ymin,ii.xmax,ii.ymax])
            
        print(listoflist)
        listoflist2 = sorted(listoflist, key = lambda x: (x[1]))  
        print(listoflist2)
        print('------------------------')
        listoflist3 = sorted(listoflist, key = lambda x: (x[0]))
        
        listoflist22 = listoflist2
        
        #for iii in range(1, len(listoflist2)):
        #    print(iii)
        
        print()
        print('head of list: '+str(listoflist2[0]))
        print('head of list y coordinate: '+str(listoflist2[0][1]))
        print('head of list x coordinate: '+str(listoflist2[0][0]))
        
        xleft = listoflist2[0][0]
            
        print('---------- begining row extraction and bbox sorintg--------------------')
        print(len(listoflist2))
        
        
    #while listoflist2 not empty loop
    while len(listoflist2)>0:
        
        #already sort by y index
        topleftbbx = []
        downrightbbx = []
        xmin = listoflist2[0][0]
        xmax = xmin
        yxmin = listoflist2[0][1]
       
        print('xmin strat: '+ str(xmin))
        print('yxmin limit: '+ str(yxmin))

        #get the topleft bbx
        for jj in listoflist2:
            #print(jj[0])
            #print(xmin)
            #print(abs(jj[1]- yxmin))
            if(jj[0]<=xmin and abs(jj[1]- yxmin)<17):
                topleftbbx = jj
                xmin = jj[0]
                ymin = jj[1]
                print('-->'+str(xmin))
                
                
        #if(jj[0]>xmax):
            #downrightbbx = jj
            #xmin = jj[0]
            #ymin = jj[1]
            #print(downrightbbx)        

        print('topleftbbx: '+str(topleftbbx))
        #print('downrightbbx: '+str(downrightbbx))
        
        #get the first row bbx
        firstrowbbx = []
        firstrowbbx.append(topleftbbx)
        #listoflist2.remove(topleftbbx)
        for jj in listoflist2:
            if(jj[0] > topleftbbx[0] and abs(jj[1]-topleftbbx[1])<17):
                firstrowbbx.append(jj)
                #listoflist2.remove(jj)
        print(firstrowbbx)
        #print(listoflist2)
        
        #soting first row bbx
        firstrowbbx = sorted(firstrowbbx, key = lambda x: (x[0]))
             
        print(firstrowbbx)
        
        for ii in firstrowbbx:
            finalrowsbbx.append(ii)
            listoflist2.remove(ii)
        
    
    #files = glob.glob('out/*')
    files = glob.glob(directoryout+'/*')
    for f in files:
        os.remove(f)
            
    for ii in finalrowsbbx:
 
        box = (ii[0], ii[1], ii[2], ii[3])
        crop = immg.crop(box)
        global nbr
        #crop.save('out/%s.png'%(nbr), 'png')
        crop.save(directoryout+'/%s.png'%(nbr), 'png')
        nbr = nbr+1
              
    imgplot = visualize(img, aabbs)
    print(type(imgplot))
    PIL_image = Image.fromarray(np.uint8(imgplot)).convert('RGB')
    #PIL_image.show()
    
    img2=ImageTk.PhotoImage(PIL_image.resize((800,800)))
    print(type(img2))
    label.configure(image=img2)
    label.image=img2 
    
    
    #files = glob.glob('../data/testpngtmp/*')
    files = glob.glob(directorytmp+'/*')
    for f in files:
        os.remove(f)
    #os.remove('../data/testpngtmp/'+os.listdir(pathDirectory)[pos])
    #os.remove('../data/testpngtmp/'+os.listdir(pathDirectory)[pos])
    btn_save["state"] = "disabled"
    btn_annotate["state"] = "normal"
    
def next_img(): 
    global pos   
    pos=pos+1
    
    if pos > len(os.listdir(pathDirectory))-1:
        btn_next["state"] = "disabled"
        pos=len(os.listdir(pathDirectory))-1
    else:
        #img2=ImageTk.PhotoImage(Image.open('../data/testpng/'+os.listdir(pathDirectory)[pos]).resize((800,800)))
        img2=ImageTk.PhotoImage(Image.open(list_of_files[pos]).resize((800,800)))
        label.configure(image=img2)
        label.image=img2 
    
    
    
def prev_img():
    global pos   
    pos=pos-1
    
    if pos < 0:
        btn_prev["state"] = "disabled"
        pos=0
    else:
    
        #img2=ImageTk.PhotoImage(Image.open('../data/testpng/'+os.listdir(pathDirectory)[pos-1]).resize((800,800)))
        img2=ImageTk.PhotoImage(Image.open(list_of_files[pos-1]).resize((800,800)))
        label.configure(image=img2)
        label.image=img2 


def annotation_file():
    global entries
    global os
    #global nbr
    global finalrowsbbx
    global ind2
    
    
    global pos
    fff = open(list_of_files[pos]+".txt", "w")
    ind = 0
    for iii in entries:
        if(iii.get()!='-'):
            fff.write(str(ind2)+' ok X '+ str(round(finalrowsbbx[ind][0]))+' '+str(round(finalrowsbbx[ind][1]))+' '+str(round(finalrowsbbx[ind][2]))+' '+str(round(finalrowsbbx[ind][3]))+' X '+iii.get()+'\n') 
        #nbr = nbr+1
        ind = ind+1 
        ind2 = ind2+1  
    fff.close()  
    global r
    global nbrout
    r.destroy()
        
    shutil.move(list_of_files[pos], directorydone) 
    shutil.move(list_of_files[pos]+'.txt',  directorydone)
    os.mkdir(directorydone+'/'+str(nbrout))
    for ff in os.listdir(directoryout+'/'):
        shutil.move(directoryout+'/'+ff, directorydone+'/'+str(nbrout))    
        
    nbrout = nbrout+1 
    
    pos=pos+1
    
    ffflog = open("log.txt", "w")
    ffflog.write(str(nbr)+';'+str(ind2)+';'+str(nbrout))
    ffflog.close()
    
    #if len(os.listdir('../data/testpng')) != 0:
    if len(os.listdir(pathDirectory)) != 0:
    
        btn_save["state"] = "normal"
        btn_annotate["state"] = "disabled"
    
        img2=ImageTk.PhotoImage(Image.open(list_of_files[pos]).resize((800,800)))
        label.configure(image=img2)
        label.text=img2
    else:  
        fInfos = Toplevel()		  # Popup -> Toplevel()
        fInfos.title('No image left')
        Button(fInfos, text='Exit', command=window.destroy).pack(padx=50, pady=10)
        fInfos.transient(window) 	  # Réduction popup impossible 
        fInfos.grab_set()		  # Interaction avec fenetre jeu impossible
        window.wait_window(fInfos)
     
    
def import_annotaion():

    global text_box
    global entries
    global entryText
    
    filetypes = (
        ('text files', '*.txt'),
        ('All files', '*.*')
    )

    filename = fd.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)

    #showinfo(
    #    title='Selected File',
    #    message=filename
    #)
    message = ''
    
    file1 = open(filename, 'r')
    Lines = file1.readlines()
    for line in Lines:
        print(line)
        linee = line.split('\n')
        print(linee)
        linee = linee[0].split(' ')
        print(linee)
        for ii in linee:
            message = message + ii + '\n'
    message = message[:-1]        
    print(message)
    
    text_box.insert('end', message)
    
    print(len(entries))
    jj=0
    for  ii  in message.split('\n'):
        entryText[jj].set(ii)
        jj=jj+1
    
    
    #import re
    #with open(filename) as f, open('word_list.txt', 'a') as f1:
    #    f1.write('\n'.join(set(re.findall("[a-zA-Z\-\.'/]+", f.read()))))

def refreshing():
    global text_box
    global entries
    global entryText
    
    message = text_box.get(1.0, "end-1c")
    print(message)
    
    jj=0
    for  ii  in message.split('\n'):
        entryText[jj].set(ii)
        jj=jj+1
    
    
    
def annotate():
    global r
    global text_box
    
    r = Toplevel()
    r.title("Words Annotation")

      
    #canvas = Canvas(r, height=1500, width=1500) 
    canvas1 = Canvas(r, height=1500, width=1500) 
    
        
    canvas1.pack()
    
    yscrollbar = Scrollbar(canvas1)
    yscrollbar.grid(row=0, column=1, sticky=N+S)
    
    canvas = Canvas(canvas1, bd=0, yscrollcommand=yscrollbar.set)
    
    canvas.config(height=1000, width=1300, scrollregion=(0, 0, 1500, 2000))
    
    #canvas.rowconfigure(0, minsize=1000, weight=1)
    #canvas.columnconfigure(1, minsize=1500, weight=1)
    #canvas.grid(row=0, column=0, sticky=E+W)

    yscrollbar.config( command = canvas.yview)
    
    
    
    
    button1 = tk.Button(canvas, text="generateAnnotation", command=annotation_file)
    
    canvas2 = Canvas(canvas1, bd=0, yscrollcommand=yscrollbar.set)
    button2 = tk.Button(canvas2, text="importAnnotation", command=import_annotaion)
    button2.grid(row=0, column=2, sticky="ns", padx=5, pady=55)
 
       
    text_box = Text(canvas2, height=40, width=30)
    text_box.grid(row=1, column=2, sticky="ns", padx=5, pady=55)
    
    button3 = tk.Button(canvas2, text="refresh", command=refreshing)
    button3.grid(row=2, column=2, sticky="ns", padx=5, pady=55)
    
    #text_box.insert('end', message)
    #text_box.pack(side=LEFT,expand=True)
    
    
    
    frame = Frame(canvas2)
    sb = Scrollbar(frame)
    sb.pack(side=RIGHT, fill=BOTH)
    text_box.config(yscrollcommand=sb.set)
    sb.config(command=text_box.yview)
    #frame.pack(expand=True)
    

    
    canvas.grid(row=0, column=0, sticky="ew")
    canvas2.grid(row=0, column=2)
    #yscrollbar.grid(row=0, column=0, sticky=N+S)
    #button1_window = canvas.create_window(0, 680, anchor=NW, window=button1)
    
    #for filename in os.listdir('out/'):
    #    print(filename)
    directoryout
    #print(len(os.listdir('out/')))
    print(len(os.listdir(directoryout+'/')))
    
    img2 = []
    inputs= []
    rowindex = 0
    colindex = 0
    cpt = 0
    global entries
    global nbr
    global entryText
    entries = []
    entryText = []
    
    #entryText = tk.StringVar()
    ent = 0
    #for jj in range(nbr-len(os.listdir('out/')), nbr):
    for jj in range(nbr-len(os.listdir(directoryout+'/')), nbr):
        
        if cpt == 10: #11:
            colindex = (colindex + 130)
            cpt = 0
            rowindex = 0
        img2.append(ImageTk.PhotoImage(Image.open(directoryout+'/'+str(jj)+'.png').resize((100,100))))
        canvas.create_image(rowindex, colindex, anchor=NW, image=img2[abs(nbr-len(os.listdir(directoryout+'/'))-jj)])
        
        entryText.append(tk.StringVar())
        entries.append(tk.Entry (r, width=13, textvariable=entryText[ent]))
         
        canvas.create_window(rowindex+55, colindex+110, window=entries[abs(nbr-len(os.listdir(directoryout+'/'))-jj)])
        
        
        rowindex = (rowindex + 130)
        
        cpt = cpt+1
        ent=ent+1
    button1_window = canvas.create_window(rowindex+55, colindex+110, anchor=NW, window=button1)    
        
    #img22=ImageTk.PhotoImage(Image.open('out/2.png').resize((100,100)))
    #canvas.create_image(0, 120, anchor=NW, image=img22) 
    #img222=ImageTk.PhotoImage(Image.open('out/4.png').resize((100,100)))
    #canvas.create_image(0, 240, anchor=NW, image=img222)  
    
    r.mainloop() 
 
 

window = tk.Tk()
window.title("Simple Text Annotation")
window.rowconfigure(0, minsize=800, weight=1)
window.columnconfigure(1, minsize=800, weight=1)





txt_edit = tk.Text(window)
fr_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
btn_open = tk.Button(fr_buttons, text="Open", command=init_pathandfolders)
#btn_next = tk.Button(fr_buttons, text="Next", command=next_img)
#btn_prev = tk.Button(fr_buttons, text="Previous", command=prev_img)
btn_save = tk.Button(fr_buttons, text="Detect words...", command=save_file)
btn_annotate = tk.Button(fr_buttons, text="Annotate...", command=annotate)

btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
#btn_next.grid(row=1, column=0, sticky="ew", padx=5)
#btn_prev.grid(row=2, column=0, sticky="ew", padx=5)
btn_save.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
btn_annotate.grid(row=4, column=0, sticky="ew", padx=5, pady=55)

fr_buttons.grid(row=0, column=0, sticky="ns")
txt_edit.grid(row=0, column=1, sticky="nsew")

btn_annotate["state"] = "disabled"
btn_save["state"] = "disabled"


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
