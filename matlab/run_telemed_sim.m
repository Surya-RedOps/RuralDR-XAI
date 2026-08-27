function results = run_telemed_sim(varargin)
% RUN_TELEMED_SIM District-Scale Telemedicine Screening Simulation in MATLAB
% Evaluates queuing bottlenecks, cellular network bandwidth, and specialist review queues
% for rural screening programs serving 100,000+ patients/year.
%
% Name-Value Parameters:
%   'NumPHCs'           - Number of rural Primary Health Centers (default: 50)
%   'ArrivalRatePerPHC' - Patients per PHC per day (default: 8)
%   'DaysPerYear'       - Active screening days per year (default: 250)
%   'ImageSizeBytesMB'  - High-res uncompressed image payload in MB (default: 15.0)
%   'CompressedSizeMB'  - Edge compressed payload for referable cases (default: 1.2)
%   'BandwidthMbps'     - Cellular connection bandwidth per PHC (default: 1.5)
%   'UngradableRate'    - Quality gate rejection rate (default: 0.12)
%   'ReferableRate'     - Proportion of patients requiring tele-review (default: 0.18)
%   'NumDoctors'        - Number of tele-ophthalmologists on roster (default: 2)
%   'ReviewTimeSec'     - Clinician verification time per referable case (default: 30)

    p = inputParser;
    addParameter(p, 'NumPHCs', 50, @isnumeric);
    addParameter(p, 'ArrivalRatePerPHC', 8, @isnumeric);
    addParameter(p, 'DaysPerYear', 250, @isnumeric);
    addParameter(p, 'ImageSizeBytesMB', 15.0, @isnumeric);
    addParameter(p, 'CompressedSizeMB', 1.2, @isnumeric);
    addParameter(p, 'BandwidthMbps', 1.5, @isnumeric);
    addParameter(p, 'UngradableRate', 0.12, @isnumeric);
    addParameter(p, 'ReferableRate', 0.18, @isnumeric);
    addParameter(p, 'NumDoctors', 2, @isnumeric);
    addParameter(p, 'ReviewTimeSec', 30, @isnumeric);
    parse(p, varargin{:});

    args = p.Results;

    fprintf('============================================================\n');
    fprintf('  RuralDR-XAI: District Telemedicine Queuing Simulation\n');
    fprintf('============================================================\n');

    % 1. Annual Screening Volume Calculations
    annualArrivals = args.NumPHCs * args.ArrivalRatePerPHC * args.DaysPerYear;
    dailyArrivals = args.NumPHCs * args.ArrivalRatePerPHC;

    % Quality Gate Triage
    gradeablePatients = annualArrivals * (1 - args.UngradableRate);
    recapturedPatients = annualArrivals * args.UngradableRate;

    % Referable / High Review Priority Cases
    referableCases = gradeablePatients * args.ReferableRate;
    nonReferableLocal = gradeablePatients * (1 - args.ReferableRate);

    % 2. Bandwidth Comparison: Cloud-Only vs. RuralDR-XAI Edge Architecture
    % Cloud-only sends ALL raw images (2 eyes per patient * 15 MB)
    cloudBandwidthDailyGB = (dailyArrivals * 2 * args.ImageSizeBytesMB) / 1024;
    cloudBandwidthAnnualTB = (annualArrivals * 2 * args.ImageSizeBytesMB) / (1024 * 1024);

    % Edge architecture sends ONLY referable summary packages (compressed 1.2 MB)
    edgeBandwidthDailyGB = (dailyArrivals * args.ReferableRate * 2 * args.CompressedSizeMB) / 1024;
    edgeBandwidthAnnualTB = (annualArrivals * args.ReferableRate * 2 * args.CompressedSizeMB) / (1024 * 1024);
    bandwidthSavingsPct = (1 - edgeBandwidthAnnualTB / cloudBandwidthAnnualTB) * 100.0;

    % 3. Tele-Ophthalmologist Review Queue & Waiting Time (M/M/c Queueing Model)
    % Arrival rate to doctor queue (cases/hour assuming 6-hour clinical shift)
    lambdaDoc = (dailyArrivals * args.ReferableRate) / 6.0; % arrivals/hour
    muDoc = 3600.0 / args.ReviewTimeSec;                   % reviews/hour per doctor
    c = args.NumDoctors;
    rho = lambdaDoc / (c * muDoc);                         % System utilization

    if rho < 1.0
        % Stable M/M/c queue
        % Probability of empty system P0
        sumTerms = 0;
        for n = 0:(c-1)
            sumTerms = sumTerms + ((c * rho)^n) / factorial(n);
        end
        lastTerm = ((c * rho)^c) / (factorial(c) * (1 - rho));
        P0 = 1.0 / (sumTerms + lastTerm);

        % Average Queue Length (Lq) and Waiting Time (Wq)
        Lq = (P0 * ((c * rho)^c) * rho) / (factorial(c) * ((1 - rho)^2));
        Wq_minutes = (Lq / lambdaDoc) * 60.0;
        W_total_minutes = Wq_minutes + (args.ReviewTimeSec / 60.0);
        isStable = true;
    else
        % Queue overflows
        Lq = Inf;
        Wq_minutes = Inf;
        W_total_minutes = Inf;
        isStable = false;
    end

    % 4. Results Reporting
    fprintf('• Annual Patient Target:       %d patients/year\n', annualArrivals);
    fprintf('• Active PHCs:                 %d centres\n', args.NumPHCs);
    fprintf('• Local Non-Referable Volume:  %d patients (%.1f%% discharged locally)\n', round(nonReferableLocal), (1-args.ReferableRate)*100);
    fprintf('• Central Specialist Review:   %d referable cases/year\n', round(referableCases));
    fprintf('• Network Bandwidth Savings:   %.1f%% (%.2f TB/yr vs. %.2f TB/yr)\n', bandwidthSavingsPct, edgeBandwidthAnnualTB, cloudBandwidthAnnualTB);
    fprintf('• Doctor Queue Utilization:    %.1f%% (%d ophthalmologists)\n', rho * 100, c);
    fprintf('• Average Clinician Wait Time: %.2f minutes per referable case\n', W_total_minutes);
    fprintf('• Queue Stability Status:      %s\n', iif(isStable, 'STABLE', 'OVERFLOW / BOTTLENECK'));
    fprintf('============================================================\n');

    results.annualArrivals = annualArrivals;
    results.bandwidthSavingsPct = bandwidthSavingsPct;
    results.cloudBandwidthAnnualTB = cloudBandwidthAnnualTB;
    results.edgeBandwidthAnnualTB = edgeBandwidthAnnualTB;
    results.doctorUtilization = rho;
    results.waitingTimeMinutes = W_total_minutes;
    results.isStable = isStable;
end

function out = iif(cond, vTrue, vFalse)
    if cond, out = vTrue; else, out = vFalse; end
end
