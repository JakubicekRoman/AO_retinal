%% evaluation of segmentation
clear all
close all
clc

%% cross-validation - validation data - s augmentovanyma

path_data = 'C:\Data\Jakubicek\AO_retinal\nnUNet_trained_models\Dataset007_AO25\nnUNetTrainer__nnUNetPlans__2d';
% path_data = 'C:\Data\Jakubicek\AO_retinal\nnUNet_trained_models\007zaloha\nnUNetTrainer__nnUNetPlans__2d';
path_GT = 'C:\Data\Jakubicek\AO_retinal\Data\Dataset007_AO25\labelsTr';

Dice = []; Fold = [];
Tbl = table();
Tbl.('Name') = 'XXXXXXX';
k = 1;

for fold = 1:5
    D = dir([path_data '\fold_' num2str(fold-1) '\validation\*.png']);
    for i = 1:size(D,1)
        img_pred = imread(fullfile(D(i).folder,D(i).name));
        img_gt = imread(fullfile( path_GT, D(i).name) );
        name = D(i).name;
        num = name(end-6:end-4);
        if mod(str2double(num)-1,11)==0; augm = 0; else; augm = 1; end
        Tbl{k,'Name'} = name(1:end-4);
        Tbl{k,'Fold'} = ['fold_' num2str(fold-1)];
        Tbl{k,'Set'} = 'Val';
        Tbl{k,'Augm'} = augm;
        Tbl{k,'Dice_V'} = {dice(img_gt==1, img_pred==1)};
        Tbl{k,'Dice_W'} = {dice(img_gt==2, img_pred==2)};
        Tbl{k,'Walls_GT'} = sum(img_gt==2,'all');
        Tbl{k,'Walls_pred'} = sum(img_pred==2,'all');
        k = k+1;
    end
end

D = dir([path_data '\fold_all\validation\*.png']);
for i = i:size(D,1)
        img_pred = imread(fullfile(D(i).folder,D(i).name));
        img_gt = imread(fullfile( path_GT, D(i).name) );
        name = D(i).name;
        num = name(end-6:end-4);
        if mod(str2double(num)-1,11)==0; augm = 0; else; augm = 1; end
        Tbl{k,'Name'} = name(1:end-4);
        Tbl{k,'Fold'} = ['fold_A'];
        Tbl{k,'Set'} = 'Val';
        Tbl{k,'Augm'} = augm;
        Tbl{k,'Dice_V'} = {dice(img_gt==1, img_pred==1)};
        Tbl{k,'Dice_W'} = {dice(img_gt==2, img_pred==2)};
        Tbl{k,'Walls_GT'} = sum(img_gt==2,'all');
        Tbl{k,'Walls_pred'} = sum(img_pred==2,'all');
        k = k+1;
end

Tbl = sortrows(Tbl, 'Name');

%% zobrazeni dice pro walls a vessels

ind1 = contains(string(Tbl.Set), 'Val');
ind = ind1;

figure
subplot(1,2,1)
boxplot(cell2mat(Tbl{ind,"Dice_V"}), Tbl{ind,"Fold"})
ylabel('Dice')
title('Vessels - Traning Cross Validation - ALL')
ylim([0.8, 1.0])

% figure
subplot(1,2,2)
boxplot(cell2mat(Tbl{ind,"Dice_W"}), Tbl{ind,"Fold"})
ylabel('Dice')
title('Walls - Cross Validation - ALL')
ylim([0.2, 1.0])


ind1 = contains(string(Tbl.Set), 'Val');
ind2 = Tbl.Augm==0;
ind = ind1 & ind2;

figure
subplot(1,2,1)
boxplot(cell2mat(Tbl{ind,"Dice_V"}), Tbl{ind,"Fold"})
ylabel('Dice')
title('Vessels - Traning Cross Validation - noAugm')
ylim([0.8, 1.0])

% figure
subplot(1,2,2)
boxplot(cell2mat(Tbl{ind,"Dice_W"}), Tbl{ind,"Fold"})
ylabel('Dice')
title('Walls - Cross Validation - noAugm')
ylim([0.2, 1.0])


disp([ 'Vessel dice (noAugm) - ' num2str(nanmean(cell2mat(Tbl{ind,"Dice_V"}))) ''])
disp([ 'Vessel dice (noAugm) - ' num2str(nanmean(cell2mat(Tbl{ind,"Dice_W"}))) ''])



%% rozptyl augmentace
ind = ~contains(string(Tbl.Fold), 'fold_A');
Tbl2 = Tbl(ind,:);

% ind = cell2mat(Tbl2{:,"Dice_V"})==0;
% Tbl2 = Tbl2(~ind,:);

Tbl3 = table();

k=1;
for i = 1:11:size(Tbl2,1)-1
    numbers = cell2mat(Tbl2{i:i+10,'Dice_V'});
    numbers(numbers==0)=[];
    varVData = std(numbers);

    numbers = cell2mat(Tbl2{i:i+10,'Dice_W'});
    numbers(numbers==0)=[];
    varWData = std(numbers);

    Tbl3{k,"Name"} = Tbl2{i,"Name"};
    Tbl3{k,"Fold"} = Tbl2{i,"Fold"};
    Tbl3{k,"VarDice_V"} = varVData;
    Tbl3{k,"VarDice_W"} = varWData;
    k=k+1;
end

figure
subplot(1,2,1)
boxplot(Tbl3{:,"VarDice_V"}, Tbl3{:,"Fold"})
ylabel('Dice')
title('Vessels - Augment variance')
ylim([0.0, 0.2])

% figure
subplot(1,2,2)
boxplot(Tbl3{:,"VarDice_W"}, Tbl3{:,"Fold"})
ylabel('Dice')
title('Walls - Augment variance')
ylim([0.0, 0.2])