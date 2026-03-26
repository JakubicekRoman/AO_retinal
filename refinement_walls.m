function [mask,skel] = refinement_walls(lumen, walls)

% walls = mask==2;

% % mask2 = imerode(walls,strel('diamond',1));
mask2 = imgaussfilt(single(walls),3);
mask2 = mask2 > 0.5;
% mask2 = walls;

% mask4 = imdilate(mask3,strel('diamond',1));

skel = bwskel(mask2);

% skel = imdilate(skel,strel('diamond',1));

bw_objcts = regionprops(skel,"Area","PixelList","PixelIdxList");

labels = bwlabel(mask2);

sel_obj = [bw_objcts(:).Area];
level = graythresh(sel_obj/max(sel_obj))*mean(sel_obj);
% level = graythresh(sel_obj/max(sel_obj))*max(sel_obj);

ind = find(sel_obj<level);

mask3 = mask2;


%% jen pro data, pro GT se musi vypnout
for i = 1:length(ind)
    label = labels(bw_objcts(ind(i)).PixelIdxList(1));
    mask3(labels==label) = false;
end

skel = skel .* mask3;

mask = double(lumen);
mask(mask3==1)=2;

% mask = medfilt2(mask,[3,3]);

% [] = sort

% figure(1)
% subplot 141
% imshow(walls,[])
% subplot 142
% imshow(mask2,[])
% subplot 143
% imshow(mask3,[])
% % subplot 144
% % imshow(mask4,[])
% linkaxes


%%
% sel_obj = [4,9,12,5,4,8,20,50,5,38];
% level = graythresh(sel_obj/max(sel_obj))*mean(sel_obj);


