function [nX] = comp_normal(X,param)

win = gausswin(param(1),param(2));
win = win./sum(win);

X = cat( 1, ones(param(1),2).*X(1,:), X , ones(param(1),2).*X(end,:));
X = conv2(X,win,'same');
X = X(param(1)+1:end-param(1),:);

dX = [X(2:end,:);X(end-1,:)]-[X(1:end,:)];
% dX = conv2(dX,win,'same');

vel=sqrt( dX(:,1).^2 + dX(:,2).^2 );
nX=[dX(:,2), -dX(:,1)]./[vel,vel];
% nX = conv2(nX,win,'same');