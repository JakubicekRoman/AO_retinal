# AO Retinal – Segmentation & Vessel Wall Analysis

Automated vessel segmentation and wall thickness analysis of Adaptive Optics (AO) retinal images using nnUNet.

## What it does

1. **Segmentation** – nnUNet model (V3.2) detects vessels and walls in AO images (`.png`).
2. **Wall analysis** – measures vessel wall thickness, computes WLR, and exports results to Excel.

## Requirements

- **Windows** (batch scripts)
- **Python 3.12** (the installer downloads it automatically via `winget` if missing)
- **CUDA GPU** (optional; works on CPU as well, but slower)

## Trained model

Download the trained nnUNet model [**here**](https://drive.google.com/file/d/1O4tYjqxwVhOZDt4KAdA4Q_IZt4kwU-6H/view?usp=drive_link), unzip it and place the contents into the `nnUNet_trained_models` folder in the project root.

## Installation

Run the installer by double-clicking or from the command line:

```
install_environment.bat
```

The script will automatically:
- install Python 3.12 (if not found)
- create a virtual environment (`.venv`)
- install PyTorch, nnUNet, and all dependencies from `requirements_pipeline.txt`

## Sample data

Download sample data [**here**](https://drive.google.com/file/d/1Vh6YbeOGG9dOEjrUav0qICemMKqGn-ym/view?usp=sharing).

## Data preparation

Create a data folder with an `images` subfolder containing the input PNG images:

```
my_data/
  └── images/
        ├── image_001.png
        ├── image_002.png
        └── ...
```

## Running the pipeline

Double-click `vessel_pipeline.bat` (it will prompt for the data path), or run from the command line:

```
vessel_pipeline.bat "C:\path\to\my_data"
```

The pipeline performs:
1. **Segmentation** – saves output masks to `my_data/masks/`
2. **Wall analysis** – saves results (Excel, images) to `my_data/results_analysis_Py/`

If masks already exist and match the input images, segmentation is skipped.

## Project structure

| File | Description |
|---|---|
| `install_environment.bat` | Environment and dependency installer |
| `vessel_pipeline.bat` | Main pipeline (segmentation + analysis) |
| `AO_segm.py` | nnUNet-based segmentation |
| `vessel_analysis.py` | Vessel wall analysis (Python port from MATLAB) |
| `comp_wall_Pred.py` | Wall prediction comparison |
| `compare_masks.py` | Mask-to-image consistency check |
| `requirements_pipeline.txt` | Python dependencies |
