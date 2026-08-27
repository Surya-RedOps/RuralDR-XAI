function [predGrade, gradeName, isReferable, probs, conf] = dr_classifier(net, imgRGB, temperature)
% DR_CLASSIFIER Evaluates deep CNN for 5-class ICDR Diabetic Retinopathy severity.
%
% Inputs:
%   net         - Pretrained MATLAB DAGNetwork / dlnetwork / SeriesNetwork
%   imgRGB      - Preprocessed 512x512x3 fundus image
%   temperature - (Optional) Temperature scaling parameter T (default 1.25)
%
% Outputs:
%   predGrade   - Predicted ICDR Grade (0 to 4)
%   gradeName   - Clinical string description
%   isReferable - Boolean triage flag (true for Grade >= 2)
%   probs       - 1x5 calibrated probability vector
%   conf        - Maximum calibrated posterior confidence

    if nargin < 3, temperature = 1.25; end

    gradeNames = {
        'Level 0 — No Diabetic Retinopathy', ...
        'Level 1 — Mild Non-Proliferative DR', ...
        'Level 2 — Moderate Non-Proliferative DR', ...
        'Level 3 — Severe Non-Proliferative DR', ...
        'Level 4 — Proliferative Diabetic Retinopathy'
    };

    if ~isempty(net)
        % Forward pass through MATLAB Deep Learning Toolbox network
        resized = imresize(imgRGB, [224, 224]);
        [predLabel, rawScores] = classify(net, resized);
        % Apply temperature scaling
        scaledLogits = log(max(rawScores, 1e-7)) / temperature;
        probs = exp(scaledLogits) / sum(exp(scaledLogits));
        [conf, maxIdx] = max(probs);
        predGrade = maxIdx - 1;
    else
        % Model weights not yet supplied: Return uninitialized contract
        predGrade = -1;
        gradeName = 'Model Uninitialized — Training Required';
        isReferable = false;
        probs = zeros(1, 5);
        conf = 0.0;
        return;
    end

    gradeName = gradeNames{predGrade + 1};
    isReferable = (predGrade >= 2);
end
