function [enhancedRGB, mask, meta] = preprocess(imgRGB, targetSize, clipLimit)
% PREPROCESS Adaptive fundus preprocessing with CLAHE and illumination correction.
%
% Inputs:
%   imgRGB     - Raw fundus image (uint8 RGB)
%   targetSize - [height, width], default [512, 512]
%   clipLimit  - CLAHE contrast limit, default 0.02 (normalized for MATLAB adapthisteq)
%
% Outputs:
%   enhancedRGB - Enhanced fundus image (512x512x3 uint8)
%   mask        - Binary retinal field mask
%   meta        - Struct with preprocessing parameters

    if nargin < 2, targetSize = [512, 512]; end
    if nargin < 3, clipLimit = 0.02; end

    origSize = size(imgRGB);

    % 1. Extract Retinal Mask & Crop Bounding Box
    gray = rgb2gray(imgRGB);
    mask = gray > 15;
    mask = imclose(mask, strel('disk', 11));
    mask = imfill(mask, 'holes');

    stats = regionprops(mask, 'BoundingBox');
    if ~isempty(stats)
        bb = round(stats(1).BoundingBox);
        % Bound bbox within image coordinates
        x1 = max(1, bb(1));
        y1 = max(1, bb(2));
        x2 = min(size(imgRGB, 2), bb(1) + bb(3));
        y2 = min(size(imgRGB, 1), bb(2) + bb(4));
        croppedImg = imgRGB(y1:y2, x1:x2, :);
        croppedMask = mask(y1:y2, x1:x2);
    else
        croppedImg = imgRGB;
        croppedMask = mask;
    end

    % 2. Resize to standard dimensions
    resizedImg = imresize(croppedImg, targetSize);
    resizedMask = imresize(croppedMask, targetSize, 'nearest');

    % 3. Illumination Homogenization (Gaussian Background Subtraction)
    hsv = rgb2hsv(resizedImg);
    vChan = hsv(:, :, 3);
    blurredV = imgaussfilt(vChan, targetSize(2) / 30);
    homogenizedV = vChan - blurredV + 0.5;
    homogenizedV = max(0.0, min(1.0, homogenizedV));

    % 4. Adaptive CLAHE on L* / V channel
    claheV = adapthisteq(homogenizedV, 'ClipLimit', clipLimit, 'NumTiles', [8, 8]);
    hsv(:, :, 3) = claheV;
    enhancedRGB = hsv2rgb(hsv);
    enhancedRGB = uint8(enhancedRGB * 255);

    % Apply mask
    for c = 1:3
        chan = enhancedRGB(:, :, c);
        chan(~resizedMask) = 0;
        enhancedRGB(:, :, c) = chan;
    end

    mask = resizedMask;
    meta.origSize = origSize;
    meta.targetSize = targetSize;
    meta.clipLimit = clipLimit;
end
