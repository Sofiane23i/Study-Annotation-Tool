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


'''
def open_file():
    """Open a file for editing."""
    filepath = askopenfilename(
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not filepath:
        return
    txt_edit.delete(1.0, tk.END)
    with open(filepath, "r") as input_file:
        text = input_file.read()
        txt_edit.insert(tk.END, text)
    window.title(f"Simple Text Annotation - {filepath}")
    '''




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

    #Path("../data/out/").mkdir(parents=True, exist_ok=True)
    #Path("../data/tmp/").mkdir(parents=True, exist_ok=True)
    #Path("../data/done/").mkdir(parents=True, exist_ok=True)
    
    btn_open["state"] = "disabled"
    btn_annotate["state"] = "disabled"
    btn_save["state"] = "normal"

def save_file():
    """Save the current file as a new file."""
    '''filepath = asksaveasfilename(
        defaultextension="txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
    )
    if not filepath:
        return
    with open(filepath, "w") as output_file:
        text = txt_edit.get(1.0, tk.END)
        output_file.write(text)
    window.title(f"Simple Text Editor - {filepath}")
    ''''''
    img = Image.open("../data/testpng/bg00101.jpg")
    img = img.resize((800, 800))
    tkimage = ImageTk.PhotoImage(img)
    tk.Label(txt_edit, image=tkimage).grid()  
    img = Image.open("../data/testpng/bg00101.jpg")
    img = img.resize((800, 800))'''
    
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
    
    
    
    
    #print (finalrowsbbx[0][0])
           
    #fff = open(os.listdir(pathDirectory)[pos]+".txt", "w")
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
    
    '''
    shutil.move(list_of_files[pos], '../data/doneimages/' ) 
    shutil.move(list_of_files[pos]+'.txt', '../data/doneimages/' )
    os.mkdir('../data/doneimages/'+str(nbrout))
    for ff in os.listdir('out/'):
        shutil.move('out/'+ff, '../data/doneimages/'+str(nbrout))
        '''
        
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
     
    

def annotate():
    global r
    r = Toplevel()
    r.title("Words Annotation")

      
    canvas = Canvas(r, height=1500, width=1500)
    
    
    '''
    canvas.create_oval(10, 10, 20, 20, fill="red")
    canvas.create_oval(200, 200, 220, 220, fill="blue")
    canvas.grid(row=0, column=0)

    scroll_x = tk.Scrollbar(r, orient="horizontal", command=canvas.xview)
    scroll_x.grid(row=1, column=0, sticky="ew")

    scroll_y = tk.Scrollbar(r, orient="vertical", command=canvas.yview)
    scroll_y.grid(row=0, column=1, sticky="ns")

    canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    canvas.configure(scrollregion=canvas.bbox("all"))
    '''
    canvas.pack()
    button1 = tk.Button(canvas, text="generateAnnotation", command=annotation_file)
    button1_window = canvas.create_window(300, 680, anchor=NW, window=button1)
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
    entries = []
    #for jj in range(nbr-len(os.listdir('out/')), nbr):
    for jj in range(nbr-len(os.listdir(directoryout+'/')), nbr):
        
        if cpt == 11:
            colindex = (colindex + 130)
            cpt = 0
            rowindex = 0
        img2.append(ImageTk.PhotoImage(Image.open(directoryout+'/'+str(jj)+'.png').resize((100,100))))
        canvas.create_image(rowindex, colindex, anchor=NW, image=img2[abs(nbr-len(os.listdir(directoryout+'/'))-jj)])
        
        
        entries.append(tk.Entry (r, width=13))
         
        canvas.create_window(rowindex+55, colindex+110, window=entries[abs(nbr-len(os.listdir(directoryout+'/'))-jj)])
        
        rowindex = (rowindex + 130)
        
        cpt = cpt+1
        
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

