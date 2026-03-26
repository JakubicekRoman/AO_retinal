@echo off

set "BASE_DIR=%~dp0"
if "%BASE_DIR:~-1%"=="\" set "BASE_DIR=%BASE_DIR:~0,-1%"

set "PIPE_TOTAL_STEPS=2"

goto :main

:show_step
echo [Step %~1/%PIPE_TOTAL_STEPS%] %~2
goto :eof

:main

if /I not "%~1"=="__run__" (
	setlocal EnableDelayedExpansion
	set "RUN_ROOT=%~1"
	if "!RUN_ROOT!"=="" (
		echo.
		echo Enter data folder path ^(must contain an "images" subfolder^):
		set /p RUN_ROOT=Data path: 
		set "RUN_ROOT=!RUN_ROOT:"=!"
	)
	if "!RUN_ROOT!"=="" (
		echo ERROR: Missing data path.
		echo Usage: %~nx0 "C:\path\to\data_folder"
		echo The data folder must contain at least an "images" subfolder.
		endlocal & exit /b 1
	)
	if not exist "!RUN_ROOT!" (
		echo ERROR: Data path not found: !RUN_ROOT!
		endlocal & exit /b 1
	)
	set "LOG_DIR=!RUN_ROOT!"
	if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"
	set "RUN_TS=%DATE%_%TIME%"
	set "RUN_TS=!RUN_TS: =0!"
	set "RUN_TS=!RUN_TS:.=-!"
	set "RUN_TS=!RUN_TS:/=-!"
	set "RUN_TS=!RUN_TS::=-!"
	set "RUN_TS=!RUN_TS:,=-!"
	set "LOG_FILE=!LOG_DIR!\vessel_pipeline_!RUN_TS!.log"
	echo Data path: !RUN_ROOT!
	echo Log file: !LOG_FILE!
	call "%~f0" __run__ "!RUN_ROOT!" "!LOG_FILE!" 2>&1 | powershell -NoProfile -Command "$OutputEncoding=[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $input | ForEach-Object { $_; $_ | Out-File -Append -Encoding utf8 -FilePath '!LOG_FILE!' }"
	set "PIPE_EXIT=!ERRORLEVEL!"
	echo.
	echo Log saved to: !LOG_FILE!
	if not "!PIPE_EXIT!"=="0" (
		echo Pipeline failed with exit code !PIPE_EXIT!.
	)
	echo Press any key to close...
	pause >nul
	endlocal & exit /b !PIPE_EXIT!
)

shift

setlocal

set "RUN_ROOT=%~1"
set "LOG_FILE=%~2"
set "VENV_ACTIVATE=%BASE_DIR%\.venv\Scripts\activate.bat"

if "%RUN_ROOT%"=="" (
	echo ERROR: Missing data path.
	if not "%LOG_FILE%"=="" >> "%LOG_FILE%" echo ERROR: Missing data path.
	exit /b 1
)

if not exist "%RUN_ROOT%" (
	echo ERROR: Data path not found: %RUN_ROOT%
	if not "%LOG_FILE%"=="" >> "%LOG_FILE%" echo ERROR: Data path not found: %RUN_ROOT%
	exit /b 1
)

if not exist "%VENV_ACTIVATE%" (
	echo ERROR: Virtual environment not found: %VENV_ACTIVATE%
	echo Expected project structure in: %BASE_DIR%
	if not "%LOG_FILE%"=="" >> "%LOG_FILE%" echo ERROR: Virtual environment not found: %VENV_ACTIVATE%
	exit /b 1
)

call "%VENV_ACTIVATE%"

if errorlevel 1 (
	echo ERROR: Failed to activate virtual environment.
	exit /b 1
)

REM Compatibility for newer PyTorch defaults (2.6+)
set "TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1"
if not defined NNUNET_DEVICE set "NNUNET_DEVICE=auto"
set "nnUNet_raw=%BASE_DIR%\Data"
set "nnUNet_preprocessed=%BASE_DIR%\nnUNet_trained_preprocessed"

set "nnUNet_results=%BASE_DIR%\nnUNet_trained_models"

if not exist "%nnUNet_results%" (
	echo ERROR: nnUNet models directory not found: %nnUNet_results%
	exit /b 1
)

REM Set paths for vessel wall analysis
set IMAGES_DIR=%RUN_ROOT%\images
set MASKS_DIR=%RUN_ROOT%\masks
set RESULTS_DIR=%RUN_ROOT%\results_analysis_Py

if not exist "%IMAGES_DIR%" (
	echo ERROR: Images directory not found: %IMAGES_DIR%
	exit /b 1
)

if not exist "%MASKS_DIR%" (
	echo INFO: Masks directory does not exist, creating: %MASKS_DIR%
	mkdir "%MASKS_DIR%"
	if errorlevel 1 (
		echo ERROR: Failed to create masks directory: %MASKS_DIR%
		exit /b 1
	)
)

if not exist "%RESULTS_DIR%" (
	mkdir "%RESULTS_DIR%"
	if errorlevel 1 (
		echo ERROR: Failed to create results directory: %RESULTS_DIR%
		exit /b 1
	)
)

REM Optional: Low-memory settings for nnUNet segmentation
set NNUNETV2_EXTRA_ARGS=--disable_tta -npp 1 -nps 1

echo.
echo ================================================
echo Vessel Analysis Pipeline
echo ================================================
echo Started: %DATE% %TIME%
echo.

REM Step 1: Segmentation (skip if masks already match images)
call :show_step 1 "Segmentation"
echo Step 1: Checking segmentation...
echo Input: %IMAGES_DIR%
echo Output: %MASKS_DIR%
echo nnUNet device: %NNUNET_DEVICE%

python "%BASE_DIR%\compare_masks.py" -i "%IMAGES_DIR%" -m "%MASKS_DIR%"
if not errorlevel 1 (
	echo [SKIP] Masks already match images. Skipping segmentation.
) else (
	echo Running nnUNet segmentation...
	if exist "%MASKS_DIR%" (
		echo Masks do not match images, deleting old masks...
		rd /s /q "%MASKS_DIR%"
		mkdir "%MASKS_DIR%"
	)
	python "%BASE_DIR%\AO_segm.py" -i "%IMAGES_DIR%" -o "%MASKS_DIR%" -m V3.2
	if errorlevel 1 (
		echo [ERROR] Segmentation step failed.
		exit /b 1
	)
	echo [OK] Segmentation done.
)

dir /b "%MASKS_DIR%\*.png" >nul 2>&1
if errorlevel 1 (
	echo [ERROR] Segmentation finished but no PNG masks were found in: %MASKS_DIR%
	exit /b 1
)

echo.
echo Step 1 complete.
echo.

REM Step 2: Wall measurement and analysis
call :show_step 2 "Wall analysis"
echo Step 2: Analyzing vessel walls...
echo Results: %RESULTS_DIR%
python "%BASE_DIR%\comp_wall_Pred.py" -i "%IMAGES_DIR%" -m "%MASKS_DIR%" -o "%RESULTS_DIR%"
if errorlevel 1 (
	echo [ERROR] Vessel wall analysis step failed.
	exit /b 1
)

echo [OK] Wall analysis done.

echo.
echo ================================================
echo Pipeline complete! Results saved to:
echo %RESULTS_DIR%
echo ================================================
echo Finished: %DATE% %TIME%
echo.

@REM pause

endlocal
