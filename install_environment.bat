@echo off

set "PAUSE_ON_EXIT=1"
if /I "%~1"=="--no-pause" (
    set "PAUSE_ON_EXIT=0"
    shift
)

call :main
set "INSTALL_EXIT=%ERRORLEVEL%"

echo.
if "%INSTALL_EXIT%"=="0" (
    echo ================================================
    echo Environment installation finished successfully.
    echo ================================================
) else (
    echo ================================================
    echo Environment installation failed with code %INSTALL_EXIT%.
    echo ================================================
)

if "%PAUSE_ON_EXIT%"=="1" (
    echo Press any key to close this window...
    pause >nul
)

exit /b %INSTALL_EXIT%

:main
setlocal EnableDelayedExpansion

set "BASE_DIR=%~dp0"
if "%BASE_DIR:~-1%"=="\" set "BASE_DIR=%BASE_DIR:~0,-1%"
set "VENV_DIR=%BASE_DIR%\.venv"
set "REQ_FILE=%BASE_DIR%\requirements_pipeline.txt"
set "TORCH_VERSION=2.5.1"
set "TORCHVISION_VERSION=0.20.1"
set "NNUNET_VERSION=2.4.1"
set "TORCH_INDEX_CPU=https://download.pytorch.org/whl/cpu"
set "TORCH_INDEX_CU118=https://download.pytorch.org/whl/cu118"
set "TORCH_INDEX_CU121=https://download.pytorch.org/whl/cu121"
set "TORCH_INDEX_CU124=https://download.pytorch.org/whl/cu124"
set "TORCH_INDEX_CU126=https://download.pytorch.org/whl/cu126"

if not exist "%REQ_FILE%" (
    echo ERROR: Requirements file not found: %REQ_FILE%
    exit /b 1
)

title AO_retinal - Environment installer
echo.
echo ================================================
echo AO Retinal Environment Installer
echo ================================================
echo Project folder: %BASE_DIR%
echo Virtual env:    %VENV_DIR%
echo Requirements:   %REQ_FILE%
echo.

echo [1/10] Checking Python 3.12...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 was not found.
    echo Attempting to install Python 3.12 via winget...
    where winget >nul 2>&1
    if errorlevel 1 (
        echo ERROR: winget is not available on this system.
        echo Please install Python 3.12 manually, then run this script again.
        exit /b 1
    )

    winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo ERROR: Automatic Python 3.12 installation failed.
        echo Please install Python 3.12 manually, then run this script again.
        exit /b 1
    )

    py -3.12 --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python 3.12 was installed but is not available in this terminal yet.
        echo Close and reopen terminal/VS Code, then run the script again.
        exit /b 1
    )
)

for /f "tokens=*" %%I in ('py -3.12 --version') do set "PY312_VERSION=%%I"
echo Found: %PY312_VERSION%

if not exist "%VENV_DIR%" (
    echo [2/10] Creating virtual environment...
    echo Creating virtual environment in: %VENV_DIR%
    py -3.12 -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo Make sure Python 3.12 is installed and available as "py -3.12".
        exit /b 1
    )
) else (
    echo [2/10] Virtual environment already exists.
)

echo [3/10] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    exit /b 1
)

echo [4/10] Upgrading pip tooling...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip tooling.
    exit /b 1
)

set "TORCH_MODE=cpu"
set "TORCH_CHANNEL=cpu"
set "TORCH_INDEX_SELECTED=%TORCH_INDEX_CPU%"

echo [5/10] Detecting GPU / CUDA...
where nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo ERROR: nvidia-smi not found in PATH.
    echo        Make sure NVIDIA drivers are installed and nvidia-smi is accessible.
    echo        Typical location: C:\Windows\System32\nvidia-smi.exe
    exit /b 1
)

echo --- nvidia-smi output: ---
nvidia-smi
echo ---------------------------
echo.

for /f %%I in ('powershell -NoProfile -Command "$o=nvidia-smi 2>$null; $m=[regex]::Match(($o -join \"`n\"), 'CUDA Version:\s*(\d+)\.(\d+)'); if(-not $m.Success){'cpu'} elseif([int]$m.Groups[1].Value -gt 12 -or ([int]$m.Groups[1].Value -eq 12 -and [int]$m.Groups[2].Value -ge 6)){'cu126'} elseif([int]$m.Groups[1].Value -eq 12 -and [int]$m.Groups[2].Value -ge 4){'cu124'} elseif([int]$m.Groups[1].Value -eq 12 -and [int]$m.Groups[2].Value -ge 1){'cu121'} elseif([int]$m.Groups[1].Value -eq 11 -and [int]$m.Groups[2].Value -ge 8){'cu118'} else {'cpu'}"') do set "TORCH_CHANNEL=%%I"

echo Detected torch channel: !TORCH_CHANNEL!

if /I "!TORCH_CHANNEL!"=="cpu" (
    echo ERROR: Could not detect a supported CUDA version from nvidia-smi output.
    echo        Expected CUDA >= 11.8 for cu118, >= 12.1 for cu121, >= 12.4 for cu124, or >= 12.6 for cu126.
    echo        Check the nvidia-smi output above for the 'CUDA Version' line.
    echo        If the line is missing, update your NVIDIA driver.
    exit /b 1
)

if /I "!TORCH_CHANNEL!"=="cu126" set "TORCH_INDEX_SELECTED=%TORCH_INDEX_CU126%"
if /I "!TORCH_CHANNEL!"=="cu124" set "TORCH_INDEX_SELECTED=%TORCH_INDEX_CU124%"
if /I "!TORCH_CHANNEL!"=="cu121" set "TORCH_INDEX_SELECTED=%TORCH_INDEX_CU121%"
if /I "!TORCH_CHANNEL!"=="cu118" set "TORCH_INDEX_SELECTED=%TORCH_INDEX_CU118%"

if /I "!TORCH_CHANNEL!"=="cu126" (
    set "TORCH_VERSION=2.6.0"
    set "TORCHVISION_VERSION=0.21.0"
)

echo [6/10] Installing CUDA-enabled PyTorch from !TORCH_INDEX_SELECTED! ...
python -m pip install --force-reinstall torch==%TORCH_VERSION% torchvision==%TORCHVISION_VERSION% --index-url "!TORCH_INDEX_SELECTED!"
if errorlevel 1 (
    echo ERROR: CUDA PyTorch installation failed for channel !TORCH_CHANNEL!.
    echo        Index URL: !TORCH_INDEX_SELECTED!
    echo        Check your internet connection or try running pip manually:
    echo          python -m pip install torch==%TORCH_VERSION% torchvision==%TORCHVISION_VERSION% --index-url "!TORCH_INDEX_SELECTED!"
    exit /b 1
)
set "TORCH_MODE=gpu"

echo [7/10] Verifying PyTorch installation...
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
if errorlevel 1 (
    echo ERROR: PyTorch verification failed.
    exit /b 1
)

echo [8/10] Installing nnUNet v%NNUNET_VERSION%...
python -m pip install --force-reinstall nnunetv2==%NNUNET_VERSION%
if errorlevel 1 (
    echo ERROR: nnUNet installation failed.
    exit /b 1
)

echo [9/10] Installing project dependencies from: %REQ_FILE%
python -m pip install --no-deps -r "%REQ_FILE%"
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    exit /b 1
)

echo [10/10] Verifying nnUNet command...
python -m nnunetv2.inference.predict_from_raw_data -h
if errorlevel 1 (
    echo ERROR: nnUNet command verification failed.
    echo Continuing anyway - nnUNet may still work.
    echo.
)

echo.
echo Environment is ready.
echo PyTorch mode: !TORCH_MODE!
echo PyTorch channel: !TORCH_CHANNEL!
echo You can run pipeline with:
echo   vessel_pipeline.bat "C:\path\to\data_folder"
echo.

endlocal & exit /b 0
