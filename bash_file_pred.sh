source ./env/AO_segm/bin/activate

export nnUNet_raw="/media/jakubicek/DATA/Jakubicek/AO_retinal/Data" 
export nnUNet_preprocessed="/media/jakubicek/DATA/Jakubicek/AO_retinal/nnUNet_trained_preprocessed" 
export nnUNet_results="/media/jakubicek/DATA/Jakubicek/AO_retinal/nnUNet_trained_models/" 

nnUNetv2_predict -i /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe/ -o /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe_pred/fold_0/ -d 006 -c 2d -f 0

nnUNetv2_predict -i /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe/ -o /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe_pred/fold_1/ -d 006 -c 2d -f 1

nnUNetv2_predict -i /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe/ -o /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe_pred/fold_2/ -d 006 -c 2d -f 2

nnUNetv2_predict -i /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe/ -o /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe_pred/fold_3/ -d 006 -c 2d -f 3

nnUNetv2_predict -i /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe/ -o /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe_pred/fold_4/ -d 006 -c 2d -f 4

nnUNetv2_predict -i /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe/ -o /media/jakubicek/DATA/Jakubicek/AO_retinal/Data/Dataset006_AO/imagesTe_pred/fold_all/ -d 006 -c 2d -f all
