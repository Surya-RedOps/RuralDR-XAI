function consistency = consistency_eng(predGrade, conf, lesionInventory, lesionMasks, camMask, odCenter, odRadius)
% CONSISTENCY_ENG Evaluates evidence consistency between prediction, lesions, and XAI in MATLAB.

    combinedLesions = lesionMasks.combinedLesions;
    lesionPixels = sum(combinedLesions(:));
    camPixels = sum(camMask(:));

    % 1. Spatial Concordance Index & Pointing Game
    if lesionPixels > 0 && camPixels > 0
        intersection = sum(combinedLesions(:) & camMask(:));
        concordanceIndex = intersection / (lesionPixels + 1e-6);
        pointingHit = intersection > 0;
    elseif lesionPixels == 0 && predGrade == 0
        concordanceIndex = 1.0;
        pointingHit = true;
    else
        concordanceIndex = 0.0;
        pointingHit = false;
    end

    % 2. Clinical Rule Verifications
    discordanceReasons = {};
    ruleSatisfied = true;

    if predGrade == 0 && (lesionInventory.maCount > 5 || lesionInventory.hardExAreaPct > 0.05)
        ruleSatisfied = false;
        discordanceReasons{end+1} = sprintf('Model predicted No DR, but %d MAs and %.2f%% exudates detected.', lesionInventory.maCount, lesionInventory.hardExAreaPct);
    end

    if predGrade >= 2 && lesionInventory.hardExAreaPct < 0.01 && lesionInventory.maCount == 0 && lesionInventory.heCount == 0
        ruleSatisfied = false;
        discordanceReasons{end+1} = 'Model predicted Referable DR, but no significant morphological lesions found.';
    end

    % Synthesize Status
    if ~ruleSatisfied || length(discordanceReasons) >= 2 || (predGrade >= 2 && concordanceIndex < 0.05 && conf < 0.80)
        status = 'REVIEW_REQUIRED';
        priority = 'URGENT';
    elseif length(discordanceReasons) == 1 || (concordanceIndex < 0.25 && predGrade >= 1)
        status = 'PARTIALLY_SUPPORTED';
        priority = 'HIGH';
    else
        status = 'SUPPORTED';
        priority = 'ROUTINE';
    end

    consistency.status = status;
    consistency.concordanceIndex = concordanceIndex;
    consistency.pointingHit = pointingHit;
    consistency.ruleSatisfied = ruleSatisfied;
    consistency.discordanceReasons = discordanceReasons;
    consistency.priority = priority;
end
