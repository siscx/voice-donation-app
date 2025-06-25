// api-client.js - Multi-task API communication logic

// API Configuration - Smart environment detection
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5000/api'  // ← Fix this port
    : window.location.origin + '/api'; // Production

// ENHANCED: New function to collect questionnaire data for multi-task submissions
function collectEnhancedQuestionnaireData() {
    // Get basic fields
    const donationLanguage = document.getElementById('donationLanguage').value;
    const ageGroup = document.getElementById('ageGroup').value;

    // Get selected health conditions
    const healthConditions = Array.from(document.querySelectorAll('input[name="healthConditions"]:checked'))
        .map(cb => cb.value);

    console.log('Selected health conditions:', healthConditions);

    // Collect severity data for each selected condition
    const conditionSeverities = {};
    healthConditions.forEach(condition => {
        const severitySelect = document.getElementById(`severity_${condition}`);
        if (severitySelect && severitySelect.value) {
            conditionSeverities[condition] = severitySelect.value;
        }
    });

    // Collect specification data for "other" conditions
    const conditionSpecifications = {};
    const specificationFields = [
        'specify_respiratory_other',
        'specify_mood_other',
        'specify_voice_other',
        'otherGeneralCondition'
    ];

    specificationFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field && field.value.trim()) {
            conditionSpecifications[fieldId] = field.value.trim();
        }
    });

    // Structure the data according to schema
    const questionnaireData = {
        donation_language: donationLanguage,
        age_group: ageGroup,
        native_language: document.getElementById('nativeLanguage')?.value || null,
        arabic_dialect: document.getElementById('arabicDialect')?.value || null,
        health_conditions: healthConditions,
        condition_severities: conditionSeverities,
        condition_specifications: conditionSpecifications
    };

    console.log('Final enhanced questionnaire data:', questionnaireData);
    return questionnaireData;
}

// NEW: Submit multiple task recordings
async function submitMultiTaskDonation() {
    try {
        console.log('=== STARTING MULTI-TASK SUBMISSION ===');

        // Validate we have recordings for all tasks
        if (!taskRecordings || Object.keys(taskRecordings).length !== totalTasks) {
            alert('Please complete all recording tasks first.');
            return;
        }

        console.log('Task recordings ready:', taskRecordings);

        // Prepare questionnaire data (same for all tasks)
        const questionnaireData = collectEnhancedQuestionnaireData();

        // Generate single donation ID for all tasks in this donation
        const donationId = generateDonationId();
        console.log('Generated donation ID:', donationId);

        // Show processing screen
        document.getElementById(`step${currentStep}`).classList.remove('active');
        document.getElementById('processingStep').classList.add('active');

        // Submit each task recording
        const submissions = [];
        for (const [taskNum, recording] of Object.entries(taskRecordings)) {
            console.log(`Preparing submission for task ${taskNum}:`, recording.taskType);

            const formData = new FormData();

            // Add audio file with task-specific filename
            const filename = `voice_donation_task${taskNum}_${recording.taskType}.webm`;
            formData.append('audio', recording.blob, filename);

            // Add questionnaire data with task metadata
            const taskQuestionnaireData = {
                ...questionnaireData,
                task_metadata: {
                    task_number: parseInt(taskNum),
                    task_type: recording.taskType,
                    total_tasks: totalTasks,
                    donation_id: donationId // Use donation_id instead of session_id
                }
            };

            formData.append('questionnaire', JSON.stringify(taskQuestionnaireData));

            // Create submission promise
            const submissionPromise = submitSingleTask(formData, taskNum, recording.taskType);
            submissions.push(submissionPromise);
        }

        // Submit all tasks in parallel for faster processing
//        console.log('Submitting all tasks in parallel...');
//        const results = await Promise.all(submissions);
//
        // DIAGNOSTIC: Process tasks sequentially instead of parallel
        console.log('Testing sequential processing...');
        const results = [];
        for (const submission of submissions) {
            console.log('Processing submission sequentially...');
            const result = await submission;
            results.push(result);
            console.log('Submission completed:', result.success);
        }

        console.log('All submissions completed:', results);

        // Check if all submissions succeeded
        const allSuccessful = results.every(result => result.success);

        if (allSuccessful) {
            // BACKGROUND: Show success immediately - no polling needed
            console.log('All tasks submitted successfully! Processing in background...');

            // Show success page right away
            document.getElementById('donationId').textContent = `Donation ID: ${donationId}`;
            document.getElementById('processingStep').classList.remove('active');
            document.getElementById('step5').classList.add('active');
        } else {
            // Handle partial failures
            const failedTasks = results.filter(result => !result.success);
            throw new Error(`Some tasks failed to submit: ${failedTasks.map(r => r.error).join(', ')}`);
        }

    } catch (error) {
        console.error('=== MULTI-TASK SUBMISSION ERROR ===');
        console.error('Error details:', error);

        alert(`There was an error submitting your recordings: ${error.message}`);

        // Go back to recording step
        document.getElementById('processingStep').classList.remove('active');
        document.getElementById(`step${currentStep}`).classList.add('active');
    }
}

// NEW: Submit a single task recording
async function submitSingleTask(formData, taskNum, taskType) {
    try {
        const submitUrl = `${API_BASE_URL}/voice-donation`;
        console.log(`Submitting task ${taskNum} (${taskType}) to:`, submitUrl);

        const response = await fetch(submitUrl, {
            method: 'POST',
            body: formData
        });

        const responseText = await response.text();

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${responseText}`);
        }

        let result;
        try {
            result = JSON.parse(responseText);
        } catch (e) {
            throw new Error(`Invalid JSON response: ${responseText}`);
        }

        console.log(`Task ${taskNum} submission result:`, result);

        return {
            success: result.success,
            task_number: taskNum,
            task_type: taskType,
            recording_id: result.recording_id,
            donation_id: result.donation_id || result.recording_id, // Fallback for compatibility
            status: result.status
        };

    } catch (error) {
        console.error(`Task ${taskNum} submission failed:`, error);
        return {
            success: false,
            task_number: taskNum,
            task_type: taskType,
            error: error.message
        };
    }
}

// NEW: Poll for completion of all tasks in a donation
async function pollMultiTaskCompletion(donationId, submissions) {
    const maxAttempts = 80; // Poll for up to ~7 minutes (80 * 5 seconds)
    let attempts = 0;

    // Update processing display
    updateMultiTaskProcessingDisplay(donationId, 'processing', submissions);

    const poll = async () => {
        try {
            attempts++;
            console.log(`Multi-task polling attempt ${attempts} for donation ${donationId}`);

            // Check status of the entire donation (not individual recordings)
            const response = await fetch(`${API_BASE_URL}/donation-status/${donationId}`);

            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }

            const donationData = await response.json();
            console.log('Donation status check result:', donationData);

            if (donationData.donation_status === 'completed') {
                // All tasks in donation completed - show success
                console.log('All tasks completed successfully!');
                document.getElementById('donationId').textContent = `Donation ID: ${donationId}`;
                document.getElementById('processingStep').classList.remove('active');
                document.getElementById('step5').classList.add('active');
                return;
            } else if (donationData.donation_status === 'failed') {
                // Some tasks failed
                const failedRecordings = donationData.recordings.filter(r => r.status === 'failed');
                throw new Error(`Task processing failed: ${failedRecordings.map(r => r.error_message || 'Unknown error').join(', ')}`);
            } else if (attempts < maxAttempts) {
                // Still processing - continue polling
                setTimeout(poll, 5000); // Poll every 5 seconds
            } else {
                // Timeout
                throw new Error('Processing is taking longer than expected. Please check back later or contact support.');
            }

        } catch (error) {
            console.error('Multi-task status polling error:', error);
            alert(`Error checking processing status: ${error.message}`);

            // Go back to recording step
            document.getElementById('processingStep').classList.remove('active');
            document.getElementById(`step${currentStep}`).classList.add('active');
        }
    };

    // Start polling after 3 seconds (longer delay for multiple tasks)
    setTimeout(poll, 3000);
}

// NEW: Update processing display for multi-task
function updateMultiTaskProcessingDisplay(donationId, status, submissions) {
    const currentLang = document.documentElement.lang || 'en';

    // Update processing status text
    const statusElement = document.querySelector('.processing-title');
    const waitElement = document.querySelector('.processing-subtitle');

    if (statusElement && waitElement) {
        if (status === 'processing') {
            statusElement.textContent = translations[currentLang]['processingStatus'];
            waitElement.textContent = `Processing voice recordings. This usually takes 2-4 minutes. Please keep this page open.`;
        } else if (status === 'completed') {
            statusElement.textContent = translations[currentLang]['processingSubtitle'];
            waitElement.textContent = `Successfully processed voice recordings with advanced AI analysis.`;
        }
    }

    // Keep original feature descriptions (don't mention specific tasks)
    const featureGrid = document.querySelector('.feature-grid');
    if (featureGrid) {
        // Don't modify the feature grid - keep original descriptions
        // The HTML already has the correct feature descriptions
    }
}

// NEW: Generate a user-friendly donation ID
function generateDonationId() {
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const random = Math.random().toString(36).substr(2, 6).toUpperCase();
    return `DON_${date}_${random}`;
}

// LEGACY: Keep the old submitDonation function for backward compatibility (if needed)
async function submitDonation() {
    // This is the old single-task submission - can be removed if not needed elsewhere
    console.warn('submitDonation() called - use submitMultiTaskDonation() instead');
    return submitMultiTaskDonation();
}