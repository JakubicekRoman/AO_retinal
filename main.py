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
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


# os.environ['OMP_NUM_THREADS']="4"

parser = argparse.ArgumentParser()
parser.add_argument('-i','--input', action='store',  help="Path to input png images")
parser.add_argument('-o','--output', action='store',  help="Path to ouput folder")
# parser.add_argument('-m','--model', action='store',  help="selection prediction model - '2D', '2D_joint' or '3D_joint'")

args = parser.parse_args()

path_data = args.input
path_save = args.output
# model = args.model

def rgb2gray(rgb):
    return np.dot(rgb[...,:3], [0.2989, 0.5870, 0.1140])


def AO_segm(path_data, path_save):
    
    
    if not os.path.exists(path_save):
        os.makedirs(path_save)
        print('Output folder has been created...')
    else:
        print('Warning: Output folder already exists!')

    png_list = glob.glob(path_data+'//**//*.png', recursive=True)

    if not png_list:
        print('No images has been found. Program has been cancelled.')
        return
    else:
        print(str(len(png_list))+' images has been found.')
       
    path_tempIn = path_save + '//temp//input//'
    path_tempOut = path_save + '//temp//output//'

    if not os.path.exists(path_tempIn):
        os.makedirs(path_tempIn)
    if not os.path.exists(path_tempOut):
        os.makedirs(path_tempOut)
    
    for idx, file in enumerate(png_list):
        # print(idx)
        # print(file)
        
        print('Resaving: ' +str(idx)+ ' from '+str(len(png_list)))
        
        im = plt.imread(file)
        if len(im.shape)==3:
            im = rgb2gray(im)
            
        fname = path_tempIn + 'Img_' '{:03d}'.format(idx) + '_0000.png'    
        mpimg.imsave(fname, im, cmap='gray')
        
    print('Calling segmentation network ... ')
    
    cmd = "nnUNetv2_predict " + "-i " + path_tempIn + " -o " + path_tempOut  + " -d 001 -c 2d -f all"

    os.system(cmd)
    
    

if __name__ == "__main__":
    
    path_data = '/mnt/Data/jakubicek/Ophtalmo/AO_retinal/Data/test'
    path_save = '/mnt/Data/jakubicek/Ophtalmo/AO_retinal/Data/test_results'
    AO_segm(path_data, path_save)

    
