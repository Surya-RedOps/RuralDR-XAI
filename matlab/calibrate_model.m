function [optTemperature, ece] = calibrate_model(valLogits, valLabels, numBins)
% CALIBRATE_MODEL Optimizes temperature scaling parameter T on validation logits in MATLAB.
%
% Inputs:
%   valLogits - N x 5 matrix of raw uncalibrated network logits
%   valLabels - N x 1 vector of ground truth class indices (0 to 4)
%   numBins   - Number of bins for Expected Calibration Error (default 10)
%
% Outputs:
%   optTemperature - Optimal scalar temperature T
%   ece            - Measured Expected Calibration Error

    if nargin < 3, numBins = 10; end

    % Objective function: Negative Log Likelihood
    nllObjective = @(T) compute_nll(valLogits, valLabels, T);

    % Optimize T > 0 using fminsearch
    initialT = 1.25;
    optTemperature = fminsearch(nllObjective, initialT, optimset('Display', 'off'));

    % Compute ECE with optimal temperature
    scaledLogits = valLogits ./ optTemperature;
    probs = exp(scaledLogits) ./ sum(exp(scaledLogits), 2);
    [confs, preds] = max(probs, [], 2);
    preds = preds - 1; % 0-indexed

    binEdges = linspace(0.0, 1.0, numBins + 1);
    ece = 0.0;
    N = length(valLabels);

    for b = 1:numBins
        inBin = (confs > binEdges(b)) & (confs <= binEdges(b + 1));
        if sum(inBin) > 0
            accInBin = mean(preds(inBin) == valLabels(inBin));
            confInBin = mean(confs(inBin));
            ece = ece + (sum(inBin) / N) * abs(accInBin - confInBin);
        end
    end
end

function nll = compute_nll(logits, labels, T)
    scaled = logits ./ max(T, 1e-4);
    probs = exp(scaled) ./ sum(exp(scaled), 2);
    N = length(labels);
    nll = 0;
    for i = 1:N
        c = labels(i) + 1;
        nll = nll - log(max(probs(i, c), 1e-7));
    end
    nll = nll / N;
end
