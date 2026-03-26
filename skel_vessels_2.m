function [skel] = skel_vessels_2(mask)

    mask1 = imresize(mask,0.5,'nearest');
%     mask2 = mask;

    % mask2 = ImgExtent(mask1,'mirroring');
    mask2 = ImgExtent(mask1,'copying');

    objcts = imfill(mask2,'holes') - mask2;
    objcts = bwareafilt(logical(objcts),[0,50]);

    mask2 = mask2 + objcts;

    mask2 = imerode(mask2,strel('diamond',2));
%     mask2 = imerode(mask2,strel('diamond',5));
%     mask2 = imerode(mask2,strel('diamond',5));
%     mask2 = imerode(mask2,strel('diamond',5));
% 
%     mask2 = imdilate(mask2,strel('diamond',5));
%     mask2 = imdilate(mask2,strel('diamond',5));
%     mask2 = imdilate(mask2,strel('diamond',5));
%     mask2 = imdilate(mask2,strel('diamond',5));

%     N = 75;
%     kernel = ones(N, N) / N^2;
%     kernel = 
    % mask2 = conv2(double(mask2), kernel, 'same');

    mask3 = imgaussfilt(single(mask2),5);
    mask3 = mask3 > 0.5;
    mask4 = imgaussfilt(single(mask3),5);
    mask4 = mask4 > 0.5;
    % mask4 = mask2;

    mask2 = imdilate(mask4,strel('diamond',2));

    mask2 = logical(mask2);

    % mask2 = imresize(mask2,size(mask),'nearest');

    skel = bwskel(mask2);

    win1 = centerCropWindow2d(size(skel),size(mask1));
    skel = imcrop(skel,win1);
    r = 3;
    skel(1:1+r,:) = 0;skel(end-r:end,:) = 0;skel(:,1:1+r) = 0;skel(:,end-r:end) = 0;

    skel = skel .* ~imdilate(bwmorph(skel,'branchpoints'),strel('disk',20));
    skel = bwlabel(skel);

    skel = imresize(skel,size(mask),'nearest');


