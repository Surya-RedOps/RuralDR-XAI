function [metrics, isGradeable, advice] = quality_gate(imgRGB, thresholds)
% QUALITY_GATE Automated Fundus Image Quality Assessment (FIQA) in MATLAB
% Evaluates focus (Tenengrad), illumination entropy, exposure, and FOV coverage.
%
% Inputs:
%   imgRGB     - uint8 RGB fundus image (H x W x 3)
%   thresholds - (Optional) struct with metric cutoff parameters
%
% Outputs:
%   metrics     - struct containing focusScore, entropy, fovCoverage, qualityScore
%   isGradeable - boolean flag (true = Gradeable/Borderline, false = Reject)
%   advice      - cell array of strings with actionable recapture guidance

    if nargin < 2
        thresholds.minFocus = 15.0;
        thresholds.minEntropy = 4.2;
        thresholds.minFOV = 0.45;
        thresholds.maxGlare = 0.12;
        thresholds.passScore = 0.60;
        thresholds.borderlineScore = 0.40;
    end

    if size(imgRGB, 3) == 3
        green = double(imgRGB(:, :, 2));
        gray = double(rgb2gray(imgRGB));
    else
        green = double(imgRGB);
        gray = double(imgRGB);
    end

    % 1. Retinal FOV Mask
    mask = gray > 15;
    mask = imclose(mask, strel('disk', 11));
    mask = imfill(mask, 'holes');
    fovCoverage = sum(mask(:)) / numel(mask);

    % 2. Focus: Tenengrad Sobel Gradient Magnitude on Green Channel
    [Gx, Gy] = imgradientxy(green, 'Sobel');
    gradMagSq = Gx.^2 + Gy.^2;
    if sum(mask(:)) > 0
        focusScore = mean(gradMagSq(mask));
    else
        focusScore = mean(gradMagSq(:));
    end

    % 3. Illumination: Shannon Entropy
    if sum(mask(:)) > 0
        validPixels = uint8(green(mask));
    else
        validPixels = uint8(green(:));
    end
    entropyVal = entropy(validPixels);

    % 4. Glare and Overexposure Check
    overexposedRatio = sum(validPixels > 245) / length(validPixels);
    glarePenalty = min(1.0, overexposedRatio * 5.0);

    % 5. Normalized Composite Quality Score Q in [0, 1]
    normFocus = min(1.0, focusScore / 100.0);
    normEntropy = min(1.0, max(0.0, (entropyVal - 2.5) / 4.0));
    normFOV = min(1.0, fovCoverage / 0.70);

    rawScore = 0.35 * normFocus + 0.35 * normEntropy + 0.30 * normFOV - 0.25 * glarePenalty;
    qualityScore = max(0.0, min(1.0, rawScore));

    % 6. Actionable Recapture Guidance
    advice = {};
    if focusScore < thresholds.minFocus
        advice{end+1} = 'Focus inadequate: Adjust objective lens on retinal vessels.';
    end
    if entropyVal < thresholds.minEntropy
        advice{end+1} = 'Illumination insufficient: Increase camera flash intensity.';
    end
    if glarePenalty > thresholds.maxGlare
        advice{end+1} = 'Corneal glare/reflection: Re-align optical axis to pupil center.';
    end
    if fovCoverage < thresholds.minFOV
        advice{end+1} = 'Incomplete retinal coverage: Center fundus field of view.';
    end

    % Gradability Decision
    if length(advice) >= 2 || qualityScore < thresholds.borderlineScore
        status = 'UNGRADABLE';
        isGradeable = false;
    elseif length(advice) == 1 || qualityScore < thresholds.passScore
        status = 'BORDERLINE';
        isGradeable = true;
    else
        status = 'GRADEABLE';
        isGradeable = true;
    end

    metrics.status = status;
    metrics.qualityScore = qualityScore;
    metrics.focusScore = focusScore;
    metrics.entropy = entropyVal;
    metrics.fovCoverage = fovCoverage;
    metrics.glarePenalty = glarePenalty;
end
