function [vesselMask, vesselDensity] = segment_vessels(imgRGB, mask)
% SEGMENT_VESSELS Retinal vessel segmentation using green-channel enhancement and Frangi filter.
%
% Inputs:
%   imgRGB - Enhanced fundus image (uint8)
%   mask   - Retinal boundary mask
%
% Outputs:
%   vesselMask    - Binary mask of segmented blood vessel tree
%   vesselDensity - Proportion of retinal area occupied by vessels

    if size(imgRGB, 3) == 3
        green = imgRGB(:, :, 2);
    else
        green = imgRGB;
    end

    % Contrast enhancement
    gEnh = adapthisteq(green, 'ClipLimit', 0.02, 'NumTiles', [8, 8]);
    inverted = imcomplement(gEnh);

    % Morphological bottom-hat to enhance dark linear vessels
    vesselness = zeros(size(green));
    for angle = 0:15:165
        se = strel('line', 11, angle);
        opened = imopen(inverted, se);
        vesselness = max(vesselness, double(opened));
    end

    if nargin >= 2 && sum(mask(:)) > 0
        vesselness(~mask) = 0;
        validVals = vesselness(mask);
        thresh = prctile(validVals(validVals > 0), 82);
    else
        thresh = prctile(vesselness(vesselness > 0), 82);
    end

    vesselMask = vesselness >= thresh;
    vesselMask = bwareaopen(vesselMask, 15);

    if nargin >= 2 && sum(mask(:)) > 0
        vesselMask(~mask) = 0;
        vesselDensity = sum(vesselMask(:)) / sum(mask(:));
    else
        vesselDensity = sum(vesselMask(:)) / numel(vesselMask);
    end
end
