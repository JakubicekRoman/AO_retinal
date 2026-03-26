clear all
close all
clc
%% cesty k trenovacim datum pro validaci
% 
% % path_dir = 'C:\Data\Jakubicek\AO_retinal\Data\Dataset007_AO25\';
% 
% % path_Data = [path_dir 'imagesTr'];
% path_Data = [path_dir 'images'];
% 
% % path_Mask = [path_dir 'lablesTr'];
% % path_Mask = [path_dir 'prediction'];
% path_Mask = [path_dir 'prediction2'];
% % path_Mask = [path_dir 'masks'];
% 
% % path_save = [path_dir 'results_GT'];
% % path_save = [path_dir 'results_Pred'];
% % path_save = [path_dir 'results2_Pred'];
% % path_save = [path_dir 'results3_Pred'];
% 
% mkdir([path_save ])
% 
% % D =  dir([path_Mask '\*.png']);
% D =  dir([path_Data '\*.png']);
% D = struct2table(D);

%% cesty pro nova data

% path_dir = ['C:\Data\Jakubicek\AO_retinal\Data\Vessels_ALL_to_May_posbirano11082025'];
% path_dir = ['C:\Data\Jakubicek\AO_retinal\Data\Tested_data_12_2025'];
path_dir = ['C:\Data\Jakubicek\AO_retinal\Data\Stack_12_2025'];


path_Data = [path_dir filesep 'images'];

path_Mask = [path_dir filesep 'masks'];

results_folder = 'results_WLR';
path_save = [path_dir filesep results_folder];

mkdir([path_save])

% D =  dir([path_Mask '\*.png']);
D =  dir([path_Data '\**\*.png']);
D = struct2table(D);


%%
k=1;
% for i = 116:size(D,1)
for i = 1:size(D,1)
i

    path_file = fullfile( D{i,'folder'}{1} , D{i,'name'}{1} );

    img = imread( path_file);
    mask = imread( replace(path_file,'\images\','\masks\') );

    maskO = mask;

    % [mask,skelW] = refinement_walls(mask==1, mask==2);
    % [skel] = skel_vessels_2(mask==1);

    [mask,skelW] = refinement_walls(mask==126, mask==252);
    [skel] = skel_vessels_2(mask==1);

    pom = double(mask>0);
    pom(pom==0) = -inf;
    pom(pom==1) = inf;
    DM=[];
    DM(:,:,1) = pom;
    for ves = 1:max(skel,[],'all')
        DM(:,:,ves+1) = bwdist((skel==ves));
    end

    [lbl_ves, ind] = min(DM,[],3);
    ind = ind-1;

    mkdir( replace(D{i,'folder'}{1},'\images\', ['\', results_folder, '\']) )

    imwrite(uint8(mat2gray(ind)*255),  [ replace(replace(path_file,'\images\', ['\', results_folder, '\']),'.png','_labels_vessels.png')] )
    imwrite(uint8(mat2gray(img)*255), [ replace(replace(path_file,'\images\', ['\', results_folder, '\']),'.png','_orig.png')] )
    imwrite(uint8((mask)*120), [ replace(replace(path_file,'\images\', ['\', results_folder, '\']),'.png','_pred.png')] )

    % imwrite(uint8(mat2gray(ind)*255),  [path_save, filesep, D{i,'name'}{1}(1:end-4) ,'_labels_vessels.png']  )
    % imwrite(uint8(mat2gray(img)*255), [path_save, filesep, D{i,'name'}{1}(1:end-4) ,'_orig.png']   )
    % imwrite(uint8((mask)*120), [path_save, filesep, D{i,'name'}{1}(1:end-4) ,'_pred.png']   )


    %%
    ind_Wall = [];
    kk = 1;

    mask7 = mask;
    mask7( imdilate(logical(skelW), strel('diamond',1)) ) = 7;

    figure(3)
    ax = imshow(maskO,[]);
    hold off
    figure(4)
    axP = imshow(maskO,[]);
    hold off
    for ves = 1:max(skel,[],'all')
        skelI = logical(skel).*logical(ind==ves);
    
%         X = bwboundaries(logical(skelI),8);
        [Px,Py] = find(bwmorph(skelI,'endpoints')==1);
        if ~(isempty(Px) || isempty(Py))

        X = bwtraceboundary(logical(skelI),[Px(1),Py(1)],'SE',8);
%         X = X{1};
        if length(X) > 10 
            X = X(1:size(X,1)/2,[2,1]);
            nX = comp_normal(X,[50,1.0]);
        
        %     figure(2)
        %     imshow(skelI,[])
    
    %         figure(3)
    %         ax = imshow(mask,[]);
        
            lenLin = 200;
            profiles = [];
            profilesM = [];
            % visual contour and normals
            for k = 30 : 2 : size(nX,1)-30
                n1 = [X(k,1)-nX(k,1)*lenLin,X(k,1)+nX(k,1)*lenLin];
                n2 = [X(k,2)-nX(k,2)*lenLin,X(k,2)+nX(k,2)*lenLin];
        
    %             [~,~,profiles(end+1,:)] = improfile(img,n1,n2,400);
    %             [x, y, profilesM] = improfile(mask.*uint16(ind==ves),n1,n2,400);
                [x, y, profilesM] = improfile(mask7,n1,n2,400);
                wall = profilesM;
                wall(wall==7) = 2;
    
    %             figure(7)
    %             hold off
    %             plot(wall)
    %             hold on
    
                W1 = wall(1:length(wall)/2);
                W2 =  wall((length(wall)/2)+1:end);
    
    %             figure(12)
    %             plot(wall)
    %             hold off
    
        
                if ( (length(find(W1==0))>5) & (length(find(W2==0))>5) )
    
                   if mod(k,5)==0
                        figure(3)
                        hold on
                        plot(ax.Parent,n1,n2,'green')
                        hold off
                    end
    
                    p01 = find(W1==0,1,'last');
                    p02 = find(W2==0,1,'first');

                    W1(1:p01)=0;
                    W2(p02:end)=0;
    
                    p1 = find(W1==2,1,'first');
                    p2 = find(W1==1,1,'first');
                    p3 = find(W2==1,1,'last')+(length(wall)/2);
                    p4 = find(W2==2,1,'last')+(length(wall)/2);

                    if isempty(find(profilesM(1:length(profilesM)/2)==7,1))
                        p1 = []; 
                    end
                    if isempty(find(profilesM((length(wall)/2)+1:end)==7,1))
                        p4 = []; 
                    end
        
                    if isempty(p1)
                        ind_Wall(kk,2:3) = nan;
                    else
                        ind_Wall(kk,2:3) = [x(p1),y(p1)];
                        figure(4)
                        hold on
                        plot(axP.Parent,[x(p01),x(length(x)/2)],[y(p01),y(length(y)/2)],'g')
                        hold off
                    end
        
                    if isempty(p2)
                        ind_Wall(kk,4:5) = nan;
                    else
                        ind_Wall(kk,4:5) = [x(p2),y(p2)];            
                    end
        
                    if isempty(p3)
                        ind_Wall(kk,8:9) = nan;
                    else
                        ind_Wall(kk,8:9) = [x(p3),y(p3)];
                    end
        
                    if isempty(p4)
                        ind_Wall(kk,10:11) = nan;
                    else
                        ind_Wall(kk,10:11) = [x(p4),y(p4)];
                        figure(4)
                        hold on
                        plot(axP.Parent,[x(p02+(length(wall)/2)+1),x(length(x)/2)],[y(p02+(length(wall)/2)+1),y(length(y)/2)],'g')
                        hold off
                    end
        
                    ind_Wall(kk,6:7) = [X(k,1),X(k,2)];
                    ind_Wall(kk,1) = ves;
        
                    kk = kk + 1;

                else
                    if mod(k,5)==0
                        figure(3)
                        hold on
                        plot(ax.Parent,n1,n2,'red')
                        hold off
                    end
                end
            end
        end
        end

        % saveas(ax,  [path_save, filesep, D{i,'name'}{1}(1:end-4), '_profiles.png'])
        % saveas(axP,  [path_save, filesep, D{i,'name'}{1}(1:end-4), '_measuring.png'])

        saveas(ax, [ replace(replace(path_file,'\images\', ['\', results_folder, '\']),'.png','_profiles.png')] )
        saveas(axP, [ replace(replace(path_file,'\images\', ['\', results_folder, '\']),'.png','_measuring.png')] )
    end

    if ~isempty(ind_Wall)
        ind_Wall(:,12) = sqrt( (ind_Wall(:,2)-ind_Wall(:,4)).^2 + (ind_Wall(:,3)-ind_Wall(:,5)).^2 );
        ind_Wall(:,13) = sqrt( (ind_Wall(:,8)-ind_Wall(:,10)).^2 + (ind_Wall(:,9)-ind_Wall(:,11)).^2 );
    
        ind_Wall(:,14) = sqrt( (ind_Wall(:,2)-ind_Wall(:,10)).^2 + (ind_Wall(:,3)-ind_Wall(:,11)).^2 );
        ind = isnan(ind_Wall(:,14));
        ind_Wall(ind,14) = sqrt( (ind_Wall(ind,2)-ind_Wall(ind,6)).^2 + (ind_Wall(ind,3)-ind_Wall(ind,7)).^2 ) *2;
        ind = isnan(ind_Wall(:,14));
        ind_Wall(ind,14) = sqrt( (ind_Wall(ind,10)-ind_Wall(ind,6)).^2 + (ind_Wall(ind,11)-ind_Wall(ind,7)).^2 ) *2;
    
        ind_Wall(:,15) = ( ind_Wall(:,12) ./ ind_Wall(:,14) ) ;
        ind_Wall(:,16) = ( ind_Wall(:,13) ./ ind_Wall(:,14) ) ;
    
        ind_Wall(isnan(ind_Wall))=-1;
    else
        ind_Wall(1,1:16) = -1;
    end

    results = table();
    results.('Vessel') = ind_Wall(:,1);
    results.('Outer_X_left') = ind_Wall(:,2);
    results.('Outer_Y_left') = ind_Wall(:,3);
    results.('Inner_X_left') = ind_Wall(:,4);
    results.('Inner_Y_left') = ind_Wall(:,5);
    results.('Central_X') = ind_Wall(:,6);
    results.('Central_Y') = ind_Wall(:,7);
    results.('Inner_X_right') = ind_Wall(:,8);
    results.('Inner_Y_right') = ind_Wall(:,9);
    results.('Outer_X_right') = ind_Wall(:,10);
    results.('Outer_Y_right') = ind_Wall(:,11);
    results.('Wall_Left') = ind_Wall(:,12);
    results.('Wall_Right') = ind_Wall(:,13);
    results.('Lumen') = ind_Wall(:,14);
    results.('WLR_Left') = ind_Wall(:,15);
    results.('WLR_Right') = ind_Wall(:,16);

    results(results.("Lumen")==-1,:)=[];

    writetable(results, [ replace(replace(path_file,'\images\', ['\', results_folder, '\']),'.png','.xlsx')] )

%     Group = results.('Vessel');
    
%     figure
%     boxchart((Group*2)-1, results.('WLR_Left'))
%     hold on
%     boxchart((Group*2), results.('WLR_Right'))
%     legend
%     xlabel('number fo epochs')
%     ylabel('Dice coefficient')
%     ylim([0.7,0.95])


%     ind_Wall(ind_Wall==-1)=nan;
%     plot(ax.Parent,ind_Wall(:,2),ind_Wall(:,3),'red')
%     plot(ax.Parent,ind_Wall(:,4),ind_Wall(:,5),'blue')
%     plot(ax.Parent,ind_Wall(:,8),ind_Wall(:,9),'blue')
%     plot(ax.Parent,ind_Wall(:,10),ind_Wall(:,11),'red')
%     hold off
% 
%     figure(4)
%     imshow(profiles,[])
% 
%     figure(5)
%     imshow(profilesM,[])

%     figure
%     imshow(lumen,[])
%     figure
%     imshow(ind,[])

%     figure
%     subplot 121
%     imshow(lumen,[])
%     subplot 122
%     imshow(skel,[])
%     colormap jet

end


% %%
% imgC = repmat(maskO,[1,1,3]);
% skel2 = imdilate(skel, strel("diamond",3));
% 
% pom = imgC(:,:,1);
% pom(logical(skel2)) = 0;
% imgC(:,:,1) = pom;
% 
% pom = imgC(:,:,3);
% pom(logical(skel2)) = 255;
% imgC(:,:,2) = pom;
% 
% pom = imgC(:,:,3);
% pom(logical(skel2)) = 0;
% imgC(:,:,3) = pom;
% 
% figure
% imshow(imgC,[])


