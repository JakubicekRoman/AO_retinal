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
import subprocess
import sys


def resolve_nnunet_device():
    """Resolve nnUNet inference device from env, defaulting to GPU when available."""
    device = os.environ.get('NNUNET_DEVICE', 'auto').strip().lower()

    if device in ('cpu', 'cuda', 'mps'):
        return device

    if device != 'auto':
        print(f"Warning: Unknown NNUNET_DEVICE='{device}', using auto.")

    try:
        import torch
        if torch.cuda.is_available():
            return 'cuda'
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'
    except Exception as e:
        print(f"Warning: Could not probe torch device, using CPU. ({e})")

    return 'cpu'


def AO_segm(path_data, path_save, model='V2'):
    """
    Segmentace AO retinálních snímků pomocí nnUNet modelu.
    
    Args:
        path_data: Cesta k vstupním png obrázkům
        path_save: Cesta k výstupní složce
        model: Verze modelu ('V1', 'V2', 'V3.0', 'V3.1', 'V3.2')
    """
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
    elif 'V3.0' in model:
        model = '005'
        print('V3.0 Segmentation model has been chosen.')
        k = 126
    elif 'V3.1' in model:
        model = '006'
        print('V3.1 Segmentation model has been chosen.')
        k = 126
    elif 'V3.2' in model: # model na nove ucebni, vycistene databazi
        model = '007'
        print('V3.2 Segmentation model has been chosen.')
        k = 126
    else:
        model = '007'
        print('Warning: No model has been specified. The V3.2 segmentation model will be used.')
        k = 126
        
    if not os.path.exists(path_save):
        os.makedirs(path_save)
        print('Output folder has been created...')
    else:
        print('Warning: Output folder already exists!')

    png_list = glob.glob(path_data + os.sep + '**' + os.sep + '*.png', recursive=True)
    png_list.sort()

    if not png_list:
        print('No images has been found. Program has been cancelled.')
        return False
    else:
        print(str(len(png_list))+' images has been found.')
        path_tempIn = path_save + os.sep + 'temp' + os.sep + 'input'
        path_tempOut = path_save + os.sep + 'temp' + os.sep + 'output'
        
        if not os.path.exists(path_tempIn):
            os.makedirs(path_tempIn)
        if not os.path.exists(path_tempOut):
            os.makedirs(path_tempOut)
        res_list = []
        for idx, file in enumerate(png_list):
            # print(idx)
            # print(file)
            
            # print('Resaving: ' +str(idx)+ ' from '+str(len(png_list)))

            im = iio.imread(file)

            if im.ndim == 3:
                # drop alpha if present
                if im.shape[2] == 4:
                    im = im[:, :, :3]
                im = (0.299*im[...,0] + 0.587*im[...,1] + 0.114*im[...,2]).astype(np.uint8)                

            fname = path_tempIn + os.sep + 'Img_' + '{:03d}'.format(idx) + '_0000.png'    
            iio.imwrite(fname, im)
            
            res_list.append(fname)
            
        print('Calling segmentation network ... ')

        # Try to find nnUNetv2_predict in the virtual environment
        venv_python = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python):
            # Use python -m to ensure correct environment
            cmd = [venv_python, '-m', 'nnunetv2.inference.predict_from_raw_data']
        else:
            cmd = ['nnUNetv2_predict']
        
        cmd.extend([
            "-i", path_tempIn,
            "-o", path_tempOut,
            "-d", model,
            "-c", "2d",
            "-f", "all",
        ])

        device = resolve_nnunet_device()
        print(f'Using nnUNet device: {device}')
        cmd.extend(["-device", device])

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"ERROR: nnUNet inference failed with exit code {result.returncode}.")
            if os.path.exists(path_save + os.sep + 'temp'):
                shutil.rmtree(path_save + os.sep + 'temp')
            return False

        print('Segmentation is done.')
        
        print('Results resaving...')
        
        saved_count = 0
        for idx, file in enumerate(res_list):
            # print(idx)
            # print(file)
            
            # im = Image.open(file).convert('L')
        #  im = Image.open(file.replace('/input/','/output/').replace('_0000',''))
        #  im = np.array(im)*255
        #  im = Image.fromarray(im)
        
            out_path = file.replace(os.sep + 'input' + os.sep, os.sep + 'output' + os.sep).replace('_0000','')
            if not os.path.exists(out_path):
                print(f"Warning: Missing prediction for {os.path.basename(out_path)}. Skipping.")
                continue
            im = iio.imread(out_path)
            im = np.array(im)*k
        
            dname = os.path.dirname(png_list[idx]).replace(path_data, path_save)
            if not os.path.exists(dname):
                os.makedirs(dname)
            fname = os.path.basename(png_list[idx])
            
        #   im.save(dname + os.sep + fname)
            iio.imwrite(dname + os.sep + fname, im)
            saved_count += 1
            
        shutil.rmtree(path_save + os.sep + 'temp')
        if saved_count == 0:
            print('ERROR: No prediction masks were generated.')
            return False
        print('Program finished.')
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input', action='store',  help="Path to input png images")
    parser.add_argument('-o','--output', action='store',  help="Path to ouput folder")
    parser.add_argument('-m','--model', action='store', default='V2', help="selection prediction model version - older 'V1' or 'V2'-newer model for vessels, no Walls and 'V3' model for joint segmetantion of vessels and walls")

    args = parser.parse_args()

    path_data = args.input
    path_save = args.output
    model = args.model
    
    success = AO_segm(path_data, path_save, model)
    sys.exit(0 if success else 1)
    
    # # Příklad přímého volání:
    # path_data = 'C:\\Data\\Jakubicek\\AO_retinal\\Data\\Tested_data_12_2025\\images'
    # path_save = 'C:\\Data\\Jakubicek\\AO_retinal\\Data\\Tested_data_12_2025\\masks'
    # model = 'V3.2'
    # AO_segm(path_data, path_save, model)

