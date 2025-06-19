// audio-recorder.js - All audio recording functionality

// Global recording variables
let mediaRecorder;
let audioChunks = [];
let recordingStartTime;
let recordingInterval;
let minRecordingTime = 30000;
let maxRecordingTime = 40000;

// Picture URLs
const pictureUrls = [
    'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=350&fit=crop&crop=center',
    'https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500&h=350&fit=crop&crop=center',
    'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=500&h=350&fit=crop&crop=center',
    'https://images.unsplash.com/photo-1544027993-37dbfe43562a?w=500&h=350&fit=crop&crop=center',
    'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=500&h=350&fit=crop&crop=center',
    'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=500&h=350&fit=crop&crop=center',
    'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=350&fit=crop&crop=center',
    'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=500&h=350&fit=crop&crop=center'
];

function loadRandomPicture() {
    const randomIndex = Math.floor(Math.random() * pictureUrls.length);
    const imgElement = document.getElementById('randomPicture');
    if (imgElement) {
        imgElement.src = pictureUrls[randomIndex];
    }
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
        console.log('Requesting microphone access...');
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: 44100,
                echoCancellation: false,
                noiseSuppression: false,
                autoGainControl: false
            }
        });
        console.log('Microphone access granted');

        // Prefer uncompressed formats for medical analysis
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
                console.log('Selected MIME type:', mimeType);
                break;
            }
        }

        if (!mimeType) {
            console.log('Using default MIME type (browser-specific)');
        }

        mediaRecorder = new MediaRecorder(stream, {
            mimeType: mimeType,
            audioBitsPerSecond: 256000
        });
        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            console.log('Data chunk received:', event.data.size, 'bytes', 'type:', event.data.type);
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            console.log('Recording stopped. Total chunks:', audioChunks.length);
            const totalSize = audioChunks.reduce((sum, chunk) => sum + chunk.size, 0);
            console.log('Total audio size:', totalSize, 'bytes');

            if (audioChunks.length === 0) {
                alert('No audio data recorded. Please try again.');
                return;
            }

            const audioBlob = new Blob(audioChunks, { type: mimeType });
            console.log('Final blob size:', audioBlob.size, 'type:', audioBlob.type);

            const audioUrl = URL.createObjectURL(audioBlob);

            const audioPlayer = document.getElementById('audioPlayer');
            if (audioPlayer) {
                audioPlayer.src = audioUrl;
                document.getElementById('audioPlayback').classList.remove('hidden');
            }
        };

        // Start recording with smaller timeslice for better data flow
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

    // Enable stop button after 30 seconds
    if (elapsed >= 30) {
        updateRecordingStatusText('recordingStatusRecording');
    }

    // Auto-stop after 40 seconds
    if (elapsed >= 40) {
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