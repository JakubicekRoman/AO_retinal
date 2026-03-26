@echo off

call C:\Data\Jakubicek\AO_retinal\.venv\Scripts\activate.bat

set nnUNet_raw=C:\Data\Jakubicek\AO_retinal\Data
set nnUNet_preprocessed=C:\Data\Jakubicek\AO_retinal\nnUNet_trained_preprocessed
set nnUNet_results=C:\Data\Jakubicek\AO_retinal\nnUNet_trained_models

REM Nastavte cestu ke vstupnim obrazkum a vystupni slozce
set INPUT_PATH=C:\Data\Jakubicek\AO_retinal\Data\Stack_12_2025\images
set OUTPUT_PATH=C:\Data\Jakubicek\AO_retinal\Data\Stack_12_2025\masks
set MODEL_VERSION=V3.2


REM Spusteni segmentace pomoci AO_segm funkce
python AO_segm.py -i %INPUT_PATH% -o %OUTPUT_PATH% -m %MODEL_VERSION%

echo Segmentace dokoncena!

