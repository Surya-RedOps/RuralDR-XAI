function fig = generate_report(origImg, enhancedImg, lesionMasks, camHeatmap, metrics, consistency, predGrade, conf)
% GENERATE_REPORT Generates a MATLAB figure clinical screening summary.

    fig = figure('Name', 'RuralDR-XAI Screening Report', 'Position', [100, 100, 1000, 700], 'Color', 'w');

    % Subplot 1: Original
    subplot(2, 2, 1);
    imshow(origImg);
    title(sprintf('Original Fundus (Quality: %s, Score: %.2f)', metrics.status, metrics.qualityScore), 'FontWeight', 'bold');

    % Subplot 2: Enhanced + Lesions
    subplot(2, 2, 2);
    imshow(enhancedImg); hold on;
    if isfield(lesionMasks, 'combinedLesions')
        visboundaries(lesionMasks.combinedLesions, 'Color', 'r', 'LineWidth', 1.5);
    end
    title('Enhanced Fundus with Lesion Overlays', 'FontWeight', 'bold');

    % Subplot 3: Grad-CAM Saliency
    subplot(2, 2, 3);
    if ~isempty(camHeatmap)
        imshow(enhancedImg); hold on;
        h = imshow(camHeatmap);
        colormap(gca, 'jet');
        set(h, 'AlphaData', 0.45);
        title('Grad-CAM Attribution Saliency', 'FontWeight', 'bold');
    else
        imshow(enhancedImg);
        title('Grad-CAM (Awaiting Model)', 'FontWeight', 'bold');
    end

    % Subplot 4: Clinical Summary Text Pane
    subplot(2, 2, 4);
    axis off;
    gradeNames = {'Level 0 (No DR)', 'Level 1 (Mild NPDR)', 'Level 2 (Moderate NPDR)', 'Level 3 (Severe NPDR)', 'Level 4 (PDR)'};
    if predGrade >= 0
        gName = gradeNames{predGrade + 1};
    else
        gName = 'Model Uninitialized';
    end

    summaryText = {
        '\bf\fontsize{14}\color[rgb]{0.1,0.2,0.5}RuralDR-XAI Clinical Screening Summary', ...
        '', ...
        sprintf('\\rm\\bfPredicted DR Grade:\\rm %s', gName), ...
        sprintf('\\rm\\bfReferable Status:\\rm %s', iif(predGrade >= 2, '\color{red}REFERABLE (Level 2+)', '\color[rgb]{0,0.6,0}NON-REFERABLE')), ...
        sprintf('\\rm\\bfCalibrated Confidence:\\rm %.1f%%', conf * 100), ...
        sprintf('\\rm\\bfEvidence Consistency:\\rm %s (Concordance: %.2f)', consistency.status, consistency.concordanceIndex), ...
        sprintf('\\rm\\bfReview Priority:\\rm \\bf%s', consistency.priority), ...
        '', ...
        '\fontsize{8}\color[rgb]{0.5,0.5,0.5}Disclaimer: Investigational decision-support tool. Requires ophthalmologist validation.'
    };
    text(0.05, 0.5, summaryText, 'FontSize', 10);
end

function out = iif(cond, valTrue, valFalse)
    if cond, out = valTrue; else, out = valFalse; end
end
