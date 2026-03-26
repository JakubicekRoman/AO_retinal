function [cropped_image] = ImgExtent(original_image,type)


% Výpočet středu pro oříznutí
original_size = size(original_image, 1); % 1500
new_size = size(original_image) * 1.2;

if contains(type,'mirroring')
    % Zrcadlení obrázku na všechny 4 strany
    % 1. Vytvoření zrcadlených verzí
    flipped_ud = flipud(original_image);   % Zrcadlení nahoru/dolů
    flipped_lr = fliplr(original_image);   % Zrcadlení doleva/doprava
    flipped_diag = flipud(flipped_lr);     % Zrcadlení obou os
    
    % 2. Složení všech dílů do nového, většího obrázku
    top_row = [flipped_diag, flipped_ud, flipped_diag];
    middle_row = [flipped_lr, original_image, flipped_lr];
    bottom_row = [flipped_diag, flipped_ud, flipped_diag];
    
    modified_image = [top_row; middle_row; bottom_row];

    center_start = (original_size * 3 - new_size) / 2 + 1;
    center_end = center_start + new_size - 1;
    
    % Oříznutí nového obrázku
    cropped_image = modified_image(center_start:center_end, center_start:center_end);

elseif contains(type,'copying')
    padding_size = ceil((new_size - original_size)/2);

    % Vytvoření paddingu pro horní a spodní stranu
    top_padding = repmat(original_image(1, :), padding_size(1), 1);
    bottom_padding = repmat(original_image(end, :), padding_size(1), 1);
    
    % Vytvoření obrázku s horním a spodním paddingem
    padded_vertical = [top_padding; original_image; bottom_padding];
    
    % Vytvoření paddingu pro levou a pravou stranu
    left_padding = repmat(padded_vertical(:, 1), 1, padding_size(2));
    right_padding = repmat(padded_vertical(:, end), 1, padding_size(2));
    
    % Vytvoření finálního, kompletně padovaného obrázku
    modified_image = [left_padding, padded_vertical, right_padding];

    cropped_image = modified_image;
end


