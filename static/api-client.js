// api-client.js - All API communication logic

// API Configuration - Smart environment detection
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5000/api'  // Local development
    : window.location.origin + '/api'; // Production

// ENHANCED: New function to collect questionnaire data for enhanced medical conditions
function collectEnhancedQuestionnaireData() {
    // Get basic fields
    const donationLanguage = document.getElementById('donationLanguage').value;
    const ageGroup = document.getElementById('ageGroup').value;

    // Get selected health conditions (NEW ENHANCED SYSTEM)
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

    console.log('Condition severities:', conditionSeverities);

    // Collect specification data for "other" conditions
    const conditionSpecifications = {};

    // Check for each "other" condition specification
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

    console.log('Condition specifications:', conditionSpecifications);

    // Structure the data according to new schema
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

async function submitDonation() {
    try {
        console.log('=== STARTING SUBMISSION ===');

        // Prepare form data
        const formData = new FormData();

        // Add audio file - ensure we have audio data
        if (!audioChunks || audioChunks.length === 0) {
            alert('No audio recorded. Please record your voice first.');
            return;
        }

        console.log('Audio chunks:', audioChunks.length, 'Total size:', audioChunks.reduce((total, chunk) => total + chunk.size, 0));

        // Create blob with proper MIME type
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
        console.log('Audio blob size:', audioBlob.size);

        if (audioBlob.size === 0) {
            alert('Audio recording is empty. Please try recording again.');
            return;
        }

        formData.append('audio', audioBlob, 'voice_donation.webm');

        // ENHANCED: Add questionnaire data using new collection method
        const questionnaireData = collectEnhancedQuestionnaireData();
        console.log('Enhanced questionnaire data:', questionnaireData);
        formData.append('questionnaire', JSON.stringify(questionnaireData));

        // Show processing screen
        document.getElementById(`step${currentStep}`).classList.remove('active');
        document.getElementById('processingStep').classList.add('active');

        // Submit to API (try real async endpoint)
        const submitUrl = `${API_BASE_URL}/voice-donation`;
        console.log('Submitting to:', submitUrl);

        const response = await fetch(submitUrl, {
            method: 'POST',
            body: formData
        });

        console.log('Response status:', response.status);

        const responseText = await response.text();
        console.log('Raw response:', responseText);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${responseText}`);
        }

        let result;
        try {
            result = JSON.parse(responseText);
        } catch (e) {
            throw new Error(`Invalid JSON response: ${responseText}`);
        }

        console.log('Parsed result:', result);

        if (result.success && result.status === 'processing') {
            // Store recording ID and start polling
            const recordingId = result.recording_id;

            // Update processing display with waiting message
            updateProcessingDisplay(recordingId, 'processing');

            // Start polling for completion
            pollDonationStatus(recordingId);
        } else if (result.success) {
            // Old-style synchronous response - show success immediately
            document.getElementById('donationId').textContent = `Donation ID: ${result.recording_id}`;
            document.getElementById('processingStep').classList.remove('active');
            document.getElementById('step5').classList.add('active');
        } else {
            throw new Error(result.message || result.error || 'Unknown error occurred');
        }

    } catch (error) {
        console.error('=== SUBMISSION ERROR ===');
        console.error('Error details:', error);
        console.error('Error stack:', error.stack);

        alert(`There was an error submitting your donation: ${error.message}`);

        // Go back to recording step
        document.getElementById('processingStep').classList.remove('active');
        document.getElementById(`step${currentStep}`).classList.add('active');
    }
}

function updateProcessingDisplay(recordingId, status) {
    const currentLang = document.documentElement.lang || 'en';

    // Update processing status text
    const statusElement = document.querySelector('.processing-title');
    const waitElement = document.querySelector('.processing-subtitle');

    if (statusElement && waitElement) {
        if (status === 'processing') {
            statusElement.textContent = translations[currentLang]['processingStatus'];
            waitElement.textContent = translations[currentLang]['processingWait'];
        } else if (status === 'completed') {
            statusElement.textContent = translations[currentLang]['processingSubtitle'];
            waitElement.textContent = translations[currentLang]['processingDescription'];
        }
    }
}

async function pollDonationStatus(recordingId) {
    const maxAttempts = 60; // Poll for up to 5 minutes (60 * 5 seconds)
    let attempts = 0;

    const poll = async () => {
        try {
            attempts++;
            console.log(`Polling attempt ${attempts} for ${recordingId}`);

            const response = await fetch(`${API_BASE_URL}/donation-status/${recordingId}`);

            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }

            const statusData = await response.json();
            console.log('Status check result:', statusData);

            if (statusData.status === 'completed') {
                // Processing complete - show success
                document.getElementById('donationId').textContent = `Donation ID: ${recordingId}`;
                document.getElementById('processingStep').classList.remove('active');
                document.getElementById('step5').classList.add('active');
                return;
            } else if (statusData.status === 'failed') {
                // Processing failed
                throw new Error(`Processing failed: ${statusData.error_message || 'Unknown processing error'}`);
            } else if (statusData.status === 'processing') {
                // Still processing - continue polling
                if (attempts < maxAttempts) {
                    setTimeout(poll, 5000); // Poll every 5 seconds
                } else {
                    throw new Error('Processing is taking longer than expected. Please check back later or contact support.');
                }
            }

        } catch (error) {
            console.error('Status polling error:', error);
            alert(`Error checking processing status: ${error.message}`);
            // Go back to recording step
            document.getElementById('processingStep').classList.remove('active');
            document.getElementById(`step${currentStep}`).classList.add('active');
        }
    };

    // Start polling after 2 seconds
    setTimeout(poll, 2000);
}