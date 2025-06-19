// api-client.js - All API communication logic

// API Configuration - Smart environment detection
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5000/api'  // Local development
    : window.location.origin + '/api'; // Production

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

        // Add questionnaire data
        const chronicConditions = Array.from(document.querySelectorAll('input[name="chronicConditions"]:checked')).map(cb => cb.value);
        const questionnaireData = {
            donation_language: document.getElementById('donationLanguage').value,
            age_group: document.getElementById('ageGroup').value,
            chronic_conditions: chronicConditions,
            respiratory_severity: document.getElementById('respiratorySeverity').value || null,
            voice_problems: document.getElementById('voiceProblems').value,
            other_condition: document.getElementById('otherCondition').value || null,
            other_voice_problem: document.getElementById('otherVoiceProblem').value || null
        };

        console.log('Questionnaire data:', questionnaireData);
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