function [inventory, masks] = detect_lesions(imgRGB, odCenter, odRadius, foveaCenter, vesselMask, mask)
% DETECT_LESIONS Retinal lesion detection (MAs, Hard/Soft Exudates, Hemorrhages) in MATLAB.
%
% Outputs:
%   inventory - Struct with lesion counts, area percentages, and foveal threat status
%   masks     - Struct containing binary masks for all lesion categories

    [H, W, ~] = size(imgRGB);
    green = imgRGB(:, :, 2);
    gEnh = adapthisteq(green, 'ClipLimit', 0.02, 'NumTiles', [8, 8]);

    % 1. Create Optic Disc Mask
    odMask = false(H, W);
    if ~isempty(odCenter) && ~isempty(odRadius)
        [X, Y] = meshgrid(1:W, 1:H);
        odDist = sqrt((X - odCenter(1)).^2 + (Y - odCenter(2)).^2);
        odMask = odDist <= (odRadius * 1.2);
    end

    % 2. Microaneurysm Detection via Morphological Bottom-Hat
    maBothat = imbothat(gEnh, strel('disk', 6));
    if nargin >= 6 && sum(mask(:)) > 0
        maBothat(~mask) = 0;
        threshMA = prctile(maBothat(mask), 98.0);
    else
        threshMA = prctile(maBothat(:), 98.0);
    end
    maBinary = maBothat >= threshMA;
    if nargin >= 5 && ~isempty(vesselMask)
        maBinary(imdilate(vesselMask, strel('disk', 2))) = 0;
    end
    maBinary(odMask) = 0;
    maProps = regionprops(maBinary, 'Area', 'Centroid');
    validMAIdx = find([maProps.Area] >= 2 & [maProps.Area] <= 35);
    maMask = ismember(bwlabel(maBinary), validMAIdx);
    maCount = length(validMAIdx);

    % 3. Hard & Soft Exudate Detection
    lab = rgb2lab(imgRGB);
    L = lab(:, :, 1);
    b = lab(:, :, 3);
    exCombined = 0.6 * L + 0.4 * b;
    if nargin >= 6 && sum(mask(:)) > 0
        exCombined(~mask) = 0;
        threshHard = prctile(exCombined(mask), 97.5);
    else
        threshHard = prctile(exCombined(:), 97.5);
    end
    hardBinary = exCombined >= threshHard;
    hardBinary(imdilate(odMask, strel('disk', 10))) = 0;
    hardExMask = bwareaopen(hardBinary, 4);

    if nargin >= 6 && sum(mask(:)) > 0
        hardExAreaPct = (sum(hardExMask(:)) / sum(mask(:))) * 100.0;
    else
        hardExAreaPct = (sum(hardExMask(:)) / numel(hardExMask)) * 100.0;
    end

    % 4. Hemorrhage Detection (Dark non-vessel lesions in green channel)
    r = double(imgRGB(:, :, 1));
    g = double(gEnh);
    rgRatio = g ./ max(r, 1.0);
    heBinary = (g <= prctile(g(mask), 6.0)) & (rgRatio < 0.85);
    if nargin >= 5 && ~isempty(vesselMask)
        heBinary(imdilate(vesselMask, strel('disk', 2))) = 0;
    end
    heBinary(odMask) = 0;
    heMask = bwareaopen(heBinary, 10);
    heProps = regionprops(heMask, 'Area');
    heCount = length(heProps);

    % 5. Foveal Threat Check (Hard Exudates within 1.0 DD of Fovea)
    foveaHazard = false;
    if ~isempty(foveaCenter) && ~isempty(odRadius)
        [X, Y] = meshgrid(1:W, 1:H);
        foveaDist = sqrt((X - foveaCenter(1)).^2 + (Y - foveaCenter(2)).^2);
        foveaZone = foveaDist <= (odRadius * 2.0);
        if sum(hardExMask(foveaZone)) > 0
            foveaHazard = true;
        end
    end

    inventory.maCount = maCount;
    inventory.hardExAreaPct = hardExAreaPct;
    inventory.heCount = heCount;
    inventory.foveaHazard = foveaHazard;

    masks.maMask = maMask;
    masks.hardExMask = hardExMask;
    masks.heMask = heMask;
    masks.combinedLesions = maMask | hardExMask | heMask;
end
