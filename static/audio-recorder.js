// audio-recorder.js - Multi-task audio recording functionality

// Global recording variables
let mediaRecorder;
let audioChunks = [];
let recordingStartTime;
let recordingInterval;

// NEW: Multi-task variables
let currentTask = 1;
let totalTasks = 3;
let taskRecordings = {}; // Store recordings for each task
let minRecordingTime = 30000; // 30 seconds
let maxRecordingTime = 40000; // 40 seconds for task 1

// Task-specific settings
const taskSettings = {
    1: {
        minTime: 3000,   // 3 seconds minimum for MPT
        maxTime: 45000,  // 45 seconds max for MPT
        title: "Maximum Phonation Time"
    },
    2: {
        minTime: 30000,  // 30 seconds
        maxTime: 40000,  // 40 seconds
        title: "Picture Description"
    },
    3: {
        minTime: 30000,  // 30 seconds
        maxTime: 60000,  // 60 seconds
        title: "Weekend Question"
    }
};

// Standardized picture URL
const STANDARDIZED_PICTURE_URL = '/static/images/img.jpeg';
//'https://images.unsplash.com/photo-1680727293560-cabbce326e3b?w=500&h=350&fit=crop&crop=center&q=80&auto=format';

function loadStandardizedPicture() {
    const imgElement = document.getElementById('randomPicture');
    if (imgElement) {
        imgElement.src = STANDARDIZED_PICTURE_URL;
        imgElement.alt = "Afternoon tea scene - please describe what you see";
    }
}

// NEW: Update task progress and UI
function updateTaskUI() {
    // Update progress indicator
    const progressElement = document.getElementById('taskProgress');
    if (progressElement) {
        const currentLang = document.documentElement.lang || 'en';
//        const progressText = translations[currentLang]['taskProgress'].replace('1', currentTask).replace('2', totalTasks);
        const progressText = `Task ${currentTask} of ${totalTasks}`;
        progressElement.textContent = progressText;
    }

    // Show/hide task content
    for (let i = 1; i <= totalTasks; i++) {
        const taskElement = document.getElementById(`task${i}`);
        if (taskElement) {
            if (i === currentTask) {
                taskElement.classList.remove('hidden');
                taskElement.classList.add('active');
            } else {
                taskElement.classList.add('hidden');
                taskElement.classList.remove('active');
            }
        }
    }

    // Update recording limits for current task
    const settings = taskSettings[currentTask];
    minRecordingTime = settings.minTime;
    maxRecordingTime = settings.maxTime;

    // Update button visibility
    updateTaskButtons();
}

// NEW: Update task-specific buttons
function updateTaskButtons() {
    const task1Button = document.querySelector('.task1-button');
    const task2Button = document.querySelector('.task2-button');

    if (currentTask === 1 || currentTask === 2) {
        // Tasks 1 & 2 - show "Continue to Next Task" button
        task1Button?.classList.remove('hidden');
        task2Button?.classList.add('hidden');
    } else if (currentTask === 3) {
        // Task 3 - show "Submit All Tasks" button
        task1Button?.classList.add('hidden');
        task2Button?.classList.remove('hidden');
    }
}

function nextTask() {
    if (!audioChunks || audioChunks.length === 0) {
        alert('Please complete the current recording first.');
        return;
    }

    // Store current task recording
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
    taskRecordings[currentTask] = {
        blob: audioBlob,
        taskType: currentTask === 1 ? 'maximum_phonation_time' :
        currentTask === 2 ? 'picture_description' : 'weekend_question',
        duration: audioBlob.size // We can calculate actual duration later if needed
    };

    console.log(`Task ${currentTask} recording stored:`, taskRecordings[currentTask]);

    // Move to next task
    currentTask++;

    if (currentTask <= totalTasks) {
        // Reset recording state for next task
        resetRecordingState();
        updateTaskUI();

        console.log(`Moved to task ${currentTask}`);
    } else {
        // All tasks completed - this shouldn't happen with current UI
        console.log('All tasks completed');
    }
}

// NEW: Submit all task recordings
function submitAllTasks() {
    if (!audioChunks || audioChunks.length === 0) {
        alert('Please complete the current recording first.');
        return;
    }

    // Store final task recording
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
    taskRecordings[currentTask] = {
        blob: audioBlob,
        taskType: currentTask === 1 ? 'maximum_phonation_time' :
          currentTask === 2 ? 'picture_description' : 'weekend_question',
        duration: audioBlob.size
    };

    console.log('All task recordings ready for submission:', taskRecordings);

    // Call the submission function (will be updated in api-client.js)
    submitMultiTaskDonation();
}

// NEW: Reset recording state between tasks
function resetRecordingState() {
    audioChunks = [];

    // Reset UI elements
    const recordButton = document.getElementById('recordButton');
    const recordIcon = document.getElementById('recordIcon');
    const recordingTimer = document.getElementById('recordingTimer');
    const audioPlayback = document.getElementById('audioPlayback');
    const audioPlayer = document.getElementById('audioPlayer');

    if (recordButton) recordButton.classList.remove('recording');
    if (recordIcon) recordIcon.textContent = '🎤';
    if (recordingTimer) recordingTimer.textContent = '00:00';
    if (audioPlayback) audioPlayback.classList.add('hidden');
    if (audioPlayer) audioPlayer.src = '';

    // Clear any active recording interval
    if (recordingInterval) {
        clearInterval(recordingInterval);
        recordingInterval = null;
    }

    // Stop any active media recorder
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        try {
            mediaRecorder.stop();
            if (mediaRecorder.stream) {
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        } catch (error) {
            console.log('Error stopping media recorder:', error);
        }
    }

    // Reset recording status text
    updateRecordingStatusText('recordingStatusStart');
}

function toggleRecording() {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        startRecording();
    } else {
        const elapsed = Date.now() - recordingStartTime;
        if (elapsed >= minRecordingTime) {
            stopRecording();
        } else {
            const remaining = Math.ceil((minRecordingTime - elapsed) / 1000);
            alert(`Please continue recording for at least ${remaining} more seconds.`);
        }
    }
}

async function startRecording() {
    try {
        console.log(`Starting recording for task ${currentTask}...`);
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: 44100,
                echoCancellation: false,
                noiseSuppression: false,
                autoGainControl: false
            }
        });

        const mimeTypes = [
            'audio/wav',
            'audio/webm;codecs=pcm',
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            ''
        ];

        let mimeType = '';
        for (let type of mimeTypes) {
            if (MediaRecorder.isTypeSupported(type)) {
                mimeType = type;
                break;
            }
        }

        mediaRecorder = new MediaRecorder(stream, {
            mimeType: mimeType,
            audioBitsPerSecond: 256000
        });
        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            console.log(`Recording stopped for task ${currentTask}`);
            const totalSize = audioChunks.reduce((sum, chunk) => sum + chunk.size, 0);
            console.log('Total audio size:', totalSize, 'bytes');

            if (audioChunks.length === 0) {
                alert('No audio data recorded. Please try again.');
                return;
            }

            const audioBlob = new Blob(audioChunks, { type: mimeType });
            const audioUrl = URL.createObjectURL(audioBlob);

            const audioPlayer = document.getElementById('audioPlayer');
            if (audioPlayer) {
                audioPlayer.src = audioUrl;
                document.getElementById('audioPlayback').classList.remove('hidden');
            }
        };

        mediaRecorder.start(500);
        recordingStartTime = Date.now();

        // Update UI
        document.getElementById('recordButton').classList.add('recording');
        document.getElementById('recordIcon').textContent = '⏹️';
        updateRecordingStatusText('recordingStatusRecording');

        // Start timer
        recordingInterval = setInterval(updateTimer, 1000);

    } catch (error) {
        alert('Could not access microphone. Please check your permissions.');
        console.error('Recording error:', error);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());

        // Update UI
        document.getElementById('recordButton').classList.remove('recording');
        document.getElementById('recordIcon').textContent = '🎤';
        updateRecordingStatusText('recordingStatusComplete');

        clearInterval(recordingInterval);
    }
}

function updateTimer() {
    const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    const timerElement = document.getElementById('recordingTimer');
    if (timerElement) {
        timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    // Enable stop button after minimum time
    if (elapsed >= minRecordingTime / 1000) {
        updateRecordingStatusText('recordingStatusRecording');
    }

    // Auto-stop after maximum time
    if (elapsed >= maxRecordingTime / 1000) {
        stopRecording();
    }
}

// Helper function to update recording status with current language
function updateRecordingStatusText(translationKey) {
    const currentLang = document.documentElement.lang || 'en';
    const statusElement = document.getElementById('recordingStatus');
    const translation = translations[currentLang][translationKey];
    if (statusElement && translation) {
        statusElement.textContent = translation;
    }
}

// NEW: Initialize multi-task recording
function initializeMultiTaskRecording() {
    currentTask = 1;
    taskRecordings = {};
    updateTaskUI();
    loadStandardizedPicture();
    console.log('Multi-task recording initialized');
}