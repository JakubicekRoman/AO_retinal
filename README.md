# AO_retinal images analysis
Project focused on retinal images from Adaptive Optic (AO) including vessels segmetnation and analysis of their wall thickness.

## Description
For now, only vessel segmentation is included.
A tool for the vessels segmention in AO images based on segmentation neural network nnUNet second version.

General information about this tool:
* It runs only on Linux
* A GPU device is needed
* It is started from the terminal
* It works with folder containing png images
* A "Input path" to a folder containing png files is required as input
* Output segmentation masks are saved into user's given "Output path" as set of png images

## Requirements
* PC with Linux and GPU
* virtual enviroment
* python version 3.11 (or 3.10)
* pytorch version 2.0.1
* cuda-toolkit 11.8
* trained model (donwload ...)

## Virtual eviroment
in the terminal:
* clone git repositary from github
* set current folder in terminal of AO_retinal
* check Python version (major version ```python3 --version``` and all installed versions ```ls -ls /usr/bin/python*```)

Create virtual enviroment
```python3.11 -m venv "env/AO_retinal"```

activate venv
```source "./env/AO_retinal/bin/activate"```

Install packages:
```
pip install -r requirements.txt
```

The main packages are:
```
numpy 
SimpleITK 
torch
nnunet
```

## Prerequisities and Running the Program

Set path to folder with donwloaded models:
```
export nnUNet_results="./nnUNet_trained_models"
```

