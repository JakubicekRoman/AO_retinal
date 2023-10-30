#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 23 09:37:22 2023

@author: jakubicek
"""

import os
import numpy as np
import glob
import argparse
# import matplotlib.pyplot as plt
# import matplotlib.image as mpimg
from PIL import Image
import shutil
import imageio.v3 as iio


parser = argparse.ArgumentParser()
parser.add_argument('-i','--input', action='store',  help="Path to input png images")
parser.add_argument('-o','--output', action='store',  help="Path to ouput folder")
parser.add_argument('-m','--model', action='store', default='V2', help="selection prediction model version - older 'V1' or 'V2'-newer model for vessels, no Walls and 'V3' model for joint segmetantion of vessels and walls")

args = parser.parse_args()

path_data = args.input
path_save = args.output
model = args.model

if path_data[-1]==os.sep:
    path_data = path_data[0:-1]
if path_save[-1]==os.sep:
    path_save = path_save[0:-1]
    
if 'V1' in model:
    model = '002'
    print('V1 Segmentation model has been chosen.')
    k = 255 
elif 'V2' in model:
    model = '003'
    print('V2 Segmentation model has been chosen.')
    k = 255
elif 'V3' in model:
    model = '005'
    print('V3 Segmentation model has been chosen.')
    k = 126
else:
    model = '003'
    print('Warning: No model has been specified. The V2 segmentation model will be used.')
    k = 255
# def AO_segm(path_data, path_save):
     
if not os.path.exists(path_save):
    os.makedirs(path_save)
    print('Output folder has been created...')
else:
    print('Warning: Output folder already exists!')

png_list = glob.glob(path_data+'//**//*.png', recursive=True)
png_list.sort()

if not png_list:
    print('No images has been found. Program has been cancelled.')
    # return
else:
    print(str(len(png_list))+' images has been found.')
       
    path_tempIn = path_save + '//temp//input//'
    path_tempOut = path_save + '//temp//output//'
    
    if not os.path.exists(path_tempIn):
        os.makedirs(path_tempIn)
    if not os.path.exists(path_tempOut):
        os.makedirs(path_tempOut)
    
    res_list = []
    for idx, file in enumerate(png_list):
        # print(idx)
        # print(file)
        
        # print('Resaving: ' +str(idx)+ ' from '+str(len(png_list)))
        
        # im = Image.open(file).convert('L')
        # im = Image.open(file)
        im = iio.imread(file)
        # numpy_array = np.array(im)
       
        fname = path_tempIn + 'Img_' '{:03d}'.format(idx) + '_0000.png'    
     #    im.save(fname)
        iio.imwrite(fname, im)
        
        res_list.append(fname)
        
    print('Calling segmentation network ... ')
    
    cmd = "nnUNetv2_predict " + "-i " + path_tempIn + " -o " + path_tempOut  + " -d " + model + " -c 2d -f all"
    
    os.system(cmd)
    
    print('Segmentation is done.')
    
    print('Results resaving...')
    
    for idx, file in enumerate(res_list):
        # print(idx)
        # print(file)
        
        # im = Image.open(file).convert('L')
       #  im = Image.open(file.replace('/input/','/output/').replace('_0000',''))
       #  im = np.array(im)*255
       #  im = Image.fromarray(im)
       
        im = iio.imread(file.replace('/input/','/output/').replace('_0000',''))
        im = np.array(im)*k
       
        dname = os.path.dirname(png_list[idx]).replace(path_data, path_save)
        if not os.path.exists(dname):
            os.makedirs(dname)
        fname = os.path.basename(png_list[idx])
        
      #   im.save(dname + os.sep + fname)
        iio.imwrite(dname + os.sep + fname, im)
    	
    shutil.rmtree(path_save+'//temp//')
    print('Program finished.')
    

# if __name__ == "__main__":
#     
#     path_data = '/mnt/DATA/jakubicek/AO_segmentation/Data/test'
#     path_save = '/mnt/DATA/jakubicek/AO_segmentation/Data/test_results'
#     AO_segm(path_data, path_save)

    
