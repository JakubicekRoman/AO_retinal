source ./env/AO_segm/bin/activate

export nnUNet_raw="/media/jakubicek/DATA/Jakubicek/AO_retinal/Data" 
export nnUNet_preprocessed="/media/jakubicek/DATA/Jakubicek/AO_retinal/nnUNet_trained_preprocessed" 
export nnUNet_results="/media/jakubicek/DATA/Jakubicek/AO_retinal/nnUNet_trained_models/" 

nnUNetv2_train 006 2d 0
nnUNetv2_train 006 2d 1
nnUNetv2_train 006 2d 2
nnUNetv2_train 006 2d 3
nnUNetv2_train 006 2d 4
nnUNetv2_train 006 2d all
