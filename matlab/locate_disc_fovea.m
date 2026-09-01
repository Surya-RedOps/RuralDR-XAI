function [odCenter, odRadius, foveaCenter] = locate_disc_fovea(imgRGB, mask, vesselMask)
% LOCATE_DISC_FOVEA Detects Optic Disc and Foveal center coordinates in MATLAB.
%
% Inputs:
%   imgRGB     - Enhanced fundus image (uint8 RGB)
%   mask       - Retinal boundary mask
%   vesselMask - Segmented vessel tree mask
%
% Outputs:
%   odCenter    - [x, y] center coordinates of Optic Disc
%   odRadius    - Estimated radius of Optic Disc in pixels
%   foveaCenter - [x, y] coordinates of Foveal center

    [H, W, ~] = size(imgRGB);
    red = imgRGB(:, :, 1);
    green = imgRGB(:, :, 2);

    % 1. Optic Disc Localization via Top-Hat and Brightness Search
    tophat = imtophat(red, strel('disk', 25));
    combined = 0.7 * double(red) + 0.3 * double(tophat);
    if nargin >= 2 && sum(mask(:)) > 0
        combined(~mask) = 0;
    end
    blurred = imgaussfilt(combined, 10);

    % Find Circular Hough Transform candidates
    minR = round(W * 0.04);
    maxR = round(W * 0.12);
    [centers, radii] = imfindcircles(uint8(blurred), [minR maxR], 'Sensitivity', 0.88);

    if ~isempty(centers)
        odCenter = round(centers(1, :));
        odRadius = radii(1);
    else
        % Fallback to centroid of brightest cluster
        [~, maxIdx] = max(blurred(:));
        [cy, cx] = ind2sub(size(blurred), maxIdx);
        odCenter = [cx, cy];
        odRadius = (minR + maxR) / 2;
    end

    % 2. Foveal Localization based on Anatomical Horizontal Offset (~2.5 DD)
    odX = odCenter(1);
    odY = odCenter(2);

    if odX < W / 2
        % OD in left hemisphere -> Fovea is temporal to the right
        searchXMin = max(1, round(odX + 1.8 * odRadius * 2));
        searchXMax = min(W, round(odX + 3.2 * odRadius * 2));
    else
        % OD in right hemisphere -> Fovea is temporal to the left
        searchXMin = max(1, round(odX - 3.2 * odRadius * 2));
        searchXMax = min(W, round(odX - 1.8 * odRadius * 2));
    end
    searchYMin = max(1, round(odY - 1.0 * odRadius * 2));
    searchYMax = min(H, round(odY + 1.0 * odRadius * 2));

    if searchXMax > searchXMin && searchYMax > searchYMin
        roi = double(green(searchYMin:searchYMax, searchXMin:searchXMax));
        if nargin >= 3
            vesselRoi = vesselMask(searchYMin:searchYMax, searchXMin:searchXMax);
            roi(vesselRoi > 0) = 255;
        end
        blurredRoi = imgaussfilt(roi, 10);
        [~, minIdx] = min(blurredRoi(:));
        [ry, rx] = ind2sub(size(blurredRoi), minIdx);
        foveaCenter = [searchXMin + rx - 1, searchYMin + ry - 1];
    else
        foveaCenter = [round(W / 2), round(H / 2)];
    end
end
