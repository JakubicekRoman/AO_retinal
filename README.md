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
* python version 3.10
* pytorch version 2.0.1
* cuda-toolkit 11.8
* trained model (download ...)

## Virtual eviroment
in the terminal:
* clone git repositary from github
* set current folder in terminal of AO_retinal
* for PIP instalation, check Python version (major version ```python3 --version``` and all installed versions ```ls -ls /usr/bin/python*```)

Create virtual enviroment via PIP
```python3.10 -m venv "./env/AO_segm"```

activate venv
```source "./env/AO_segm/bin/activate"```

Install packages:
```pip install -r requirements.txt```

or Create virtual enviroment via CONDA
```conda env create --file environment.yml```
activate venv
```conda activate AO_segm```


## Prerequisities and Running the Program

Download the model and save to current folders
link: 

Set path to folder with donwloaded models - call in terminal:
```
export nnUNet_results="./nnUNet_trained_models"
```

Calling program:
```
AO_segm --input folder_with_images --output folder_for_saving
```

Example of calling:
```
AO_segm -i /mnt/Data/jakubicek/Ophtalmo/AO_retinal/Data/test -o /mnt/Data/jakubicek/Ophtalmo/AO_retinal/Data/test_results
```

