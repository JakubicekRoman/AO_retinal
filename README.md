# AO_retinal images analysis
Project focused on retinal images from Adaptive Optic (AO) including vessels segmentation and analysis of their wall thickness.

## Description
For now, only vessel segmentation is included.
A tool for the vessel segmentation in AO images based on segmentation neural network nnUNet second version.

General information about this tool:
* It runs only on Linux
* A GPU device is needed
* It is started from the terminal
* It works with folder containing png images
* A "Input path" to a folder containing png files is required as input
* Output segmentation masks are saved into user's given "Output path" as set of png images
* There are three segmentation models
  * 'V1' - old version for vessels only
  * 'V2' - newer version for vessels without vessel walls
  * 'V3.1' - model (beta) for vessels and walls segmentation
  * 'V3.2' - model for vessels and walls segmentation (with cross validation)

## Requirements
* PC with Linux and GPU
* virtual environment
* python version 3.10
* installed pip and venv
* pytorch version 2.0.1
* cuda-toolkit 11.8
* trained model (download [**here**](https://drive.google.com/file/d/1O4tYjqxwVhOZDt4KAdA4Q_IZt4kwU-6H/view?usp=drive_link))

## Virtual environment
in the terminal:
* clone git repository from github
```
git clone https://github.com/JakubicekRoman/AO_retinal.git
```
* set current folder of AO_retinal in the terminal
```
cd AO_retinal/
```
* for PIP installation, check Python version (major version ```python3 --version``` and all installed versions ```ls -ls /usr/bin/python*```)

Install python, pip and venv (if not already)
```
sudo apt install python3.10
sudo apt install python3-pip
sudo apt install python3.10-venv
```

Create virtual environment
```
python3.10 -m venv "./env/AO_segm"
```

Activate venv
```
source "./env/AO_segm/bin/activate"
```

Install the packages in this order!!!
```
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir
python3 -m pip install -r requirements.txt
```



## Prerequisites and Running the Program

Download the model [**here**](https://drive.google.com/file/d/1O4tYjqxwVhOZDt4KAdA4Q_IZt4kwU-6H/view?usp=drive_link), unzip and save to current folders

Set folder path to downloaded and unzipped model -> call in terminal:
```
export nnUNet_results="./nnUNet_trained_models"
```

Calling of the program:
```
python3 AO_segm.py -h
python3 AO_segm.py --input folder_with_images --output folder_for_saving --model 'model_version'
```

Example of calling:
```
python3 AO_segm.py -i /mnt/DATA/jakubicek/AO_segmentation/Data/test -o /mnt/DATA/jakubicek/AO_segmentation/Data/test_results -m 'V2'
```


## New calling of the program in the new terminal
* Set the AO_retinal folder as the current folder in the terminal
* Activate venv - AO_segm
```
source "./env/AO_segm/bin/activate"
```
* Set folder path to nUNet_trained_models
```
export nnUNet_results="./nnUNet_trained_models"
```
* call the program
```
python3 AO_segm.py -h
```
