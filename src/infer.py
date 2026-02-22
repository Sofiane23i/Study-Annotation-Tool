import argparse

import torch
from path import Path

from dataloader import DataLoaderImgFile
from eval import evaluate
from net import WordDetectorNet
from visualization import visualize_and_plot

from PIL import Image
import PIL, sys
import numpy as np


from operator import itemgetter
import operator

from WordSegmentation import wordSegmentation, prepareImg








import json
import os

# Load vocabulary from JSON file instead of hardcoding
vocab_path = os.path.join(os.path.dirname(__file__), "vocabulary.json")
if os.path.exists(vocab_path):
    try:
        with open(vocab_path, "r", encoding="utf-8") as f:
            words = json.load(f)
    except Exception as e:
        print(f"Error loading vocabulary.json: {e}")
        words = []
else:
    print("Warning: vocabulary.json not found. Using empty list.")
    words = []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cuda')
    args = parser.parse_args()

    net = WordDetectorNet()
    net.load_state_dict(torch.load('../model/weights', map_location=args.device))
    net.eval()
    net.to(args.device)

    loader = DataLoaderImgFile(Path('../data/testpng'), net.input_size, args.device)
    #loader = DataLoaderImgFile(Path('../data/bgsub'), net.input_size, args.device)
    res = evaluate(net, loader, max_aabbs=1000)
    nbr=0
    #image = Image.open('../data/testpng/bg00101.jpg')
    
    #print(image)
    

    
    fff = open("words.txt", "w")
    
    for i, (img, aabbs) in enumerate(zip(res.batch_imgs, res.batch_aabbs)):
    
        print(i)
        
        listoflist = []
        finallistoflist = [] 
        
        f = loader.get_scale_factor(i)
        aabbs = [aabb.scale(1 / f, 1 / f) for aabb in aabbs]
        
        img = loader.get_original_img(i)
        immg = loader.get_original_img_rgb(i)
        print(type(immg))        
        visualize_and_plot(img, aabbs)
        
        for ii in aabbs:
            listoflist.append([ii.xmin,ii.ymin,ii.xmax,ii.ymax])
            
        print(listoflist)
        listoflist2 = sorted(listoflist, key = lambda x: (x[1]))  
        print(listoflist2)
        print('------------------------')
        listoflist3 = sorted(listoflist, key = lambda x: (x[0]))  
        #print(listoflist3)
        
        
        listoflist22 = listoflist2
        
        #for iii in range(1, len(listoflist2)):
        #    print(iii)
        
        print()
        print('head of list: '+str(listoflist2[0]))
        print('head of list y coordinate: '+str(listoflist2[0][1]))
        print('head of list x coordinate: '+str(listoflist2[0][0]))
        
        xleft = listoflist2[0][0]
        
        #firstelt = listoflist2[0]
        #listoflist23 = listoflist2
        #listoflist23.pop(0)
        #print(firstelt)
        #print(listoflist23)
        
        print('---------- begining row extraction and bbox sorintg--------------------')
        print(len(listoflist2))
        
        finalrowsbbx = [] 
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
        
        
        
        '''
        indexbbx = 0
        for jj in listoflist23:
            if(jj[0]<xleft):
                print('a bbox found'+str(indexbbx))
                break
            else:
                print('fine')
            indexbbx = indexbbx + 1
            
        finallistoflist.insert(0, firstelt)
        print(finallistoflist)  
        '''      
        
        for ii in finalrowsbbx:
            #print (ii[0])
            #print (ii.ymin)
            #print (ii.xmax)
            #print (ii.ymax)
            #print ()
            
            
            
            box = (ii[0], ii[1], ii[2], ii[3])
            crop = immg.crop(box)
            #cropped= img[ii[0]:ii[1], ii[2]:ii[3]]
            #img = img(img, np.uint8)
            #print(img.shape)
            #print(immg)
            #img = (immg).astype(np.uint8)
            
            #import matplotlib.pyplot as plt
            #plt.imshow(img)
            #plt.show()
            #print(img)
            #imgg = Image.fromarray(img, 'RGB')
            
            #if imgg.mode != 'RGB':
            #    imgg = imgg.convert('RGB')
            #crop = imgg.crop(box)
            #if crop.mode != 'RGB':
            #    crop = crop.convert('RGB')
            
            crop.save('out/%s.png'%(nbr), 'png')
            if(words[nbr] != '-'):
                fff.write(str(nbr)+' ok X '+ str(round(ii[0]))+' '+str(round(ii[1]))+' '+str(round(ii[2]))+' '+str(round(ii[3]))+' X '+words[nbr]+'\n')
            nbr=nbr+1
        print(len(listoflist2))
        #print(listoflist)
        #listoflist2 = sorted(listoflist, key = operator.itemgetter(0, 1))  
        #print(listoflist2)  
    fff.close()


if __name__ == '__main__':
    main()
