function [camHeatmap, camMask] = xai_gradcam(net, imgRGB, targetClass, featureLayer)
% XAI_GRADCAM Generates native MATLAB gradCAM activation heatmaps.
%
% Inputs:
%   net          - MATLAB DAGNetwork / dlnetwork
%   imgRGB       - Preprocessed RGB fundus image
%   targetClass  - Integer index (1 to 5) or class categorical
%   featureLayer - (Optional) Name of final convolutional layer
%
% Outputs:
%   camHeatmap   - H x W normalized [0, 1] class activation heatmap
%   camMask      - Binary high-activation mask (>0.35)

    [H, W, ~] = size(imgRGB);

    if isempty(net)
        camHeatmap = zeros(H, W);
        camMask = false(H, W);
        return;
    end

    resized = imresize(imgRGB, [224, 224]);

    if nargin < 4
        % Auto-detect last convolutional layer in DAGNetwork
        layerNames = {net.Layers.Name};
        convIdx = find(contains(lower(layerNames), 'conv') | contains(lower(layerNames), 'stage'));
        if ~isempty(convIdx)
            featureLayer = layerNames{convIdx(end)};
        else
            featureLayer = layerNames{end-2};
        end
    end

    % Call MATLAB Deep Learning Toolbox gradCAM
    cam = gradCAM(net, resized, targetClass, 'FeatureLayer', featureLayer);
    camHeatmap = imresize(cam, [H, W], 'bilinear');
    camMin = min(camHeatmap(:));
    camMax = max(camHeatmap(:));
    if camMax > camMin
        camHeatmap = (camHeatmap - camMin) / (camMax - camMin);
    end

    camMask = camHeatmap >= 0.35;
end
