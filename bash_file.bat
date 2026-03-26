@echo off

call C:\Data\Jakubicek\AO_retinal\.venv\Scripts\activate.bat

set nnUNet_raw=C:\Data\Jakubicek\AO_retinal\Data
set nnUNet_preprocessed=C:\Data\Jakubicek\AO_retinal\nnUNet_trained_preprocessed
set nnUNet_results=C:\Data\Jakubicek\AO_retinal\nnUNet_trained_models

REM nnUNetv2_plan_and_preprocess -d 007 --verify_dataset_integrity

nnUNetv2_train 007 2d 0 --c
python clear_cuda.py

nnUNetv2_train 007 2d 1 --c 
python clear_cuda.py

nnUNetv2_train 007 2d 2 --c
python clear_cuda.py

nnUNetv2_train 007 2d 3 --c
python clear_cuda.py

nnUNetv2_train 007 2d 4 --c
python clear_cuda.py

nnUNetv2_train 007 2d all --c
