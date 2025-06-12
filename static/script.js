// Global variables
let currentStep = 1;
let mediaRecorder;
let audioChunks = [];
let recordingStartTime;
let recordingInterval;
let minRecordingTime = 30000;
let maxRecordingTime = 40000;

// API Configuration - Smart environment detection
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5000/api'  // Local development
    : window.location.origin + '/api'; // Production

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

// Translation object
const translations = {
    en: {
        heroTitle: "Donate Your Voice For Health",
        heroSubtitle: "Help us unlock the potential of voice for early health detection. Your donation helps train AI to identify signs of chronic conditions in just 30 seconds of speech—building proactive healthcare for everyone.",
        trustBadge1: "HIPAA Secure",
        trustBadge2: "Anonymous",
        trustBadge3: "AI-Powered",
        step1Icon: "🚀",
        step1Title: "Your Voice, Our Future",
        step1Text: "Every voice carries hidden health insights. Your unique vocal patterns hold clues that could transform how we detect and prevent illness. Help us build the foundation for accessible healthcare worldwide.",
        stat1Number: "60+",
        stat1Label: "Voice features analyzed",
        stat2Number: "30s",
        stat2Label: "Time to contribute",
        step1Button: "Begin Your Contribution",
        step2Icon: "💬",
        step2Title: "Health Questionnaire",
        step2Subtitle: "Anonymous data helps train our AI models",
        donationLanguageLabel: "Recording Language",
        donationLanguageSelect: "Select the language for your voice recording",
        donationLanguageEnglish: "English",
        donationLanguageArabic: "Arabic",
        ageLabel: "Age Range",
        ageSelect: "Select your age range",
        age1825: "18-25 years",
        age2635: "26-35 years",
        age3645: "36-45 years",
        age4655: "46-55 years",
        age5665: "56-65 years",
        age6675: "66-75 years",
        age76plus: "76+ years",
        conditionsLabel: "Health Conditions (Select all that apply)",
        conditionNone: "None",
        conditionRespiratory: "Respiratory (Asthma, COPD)",
        conditionNeurological: "Neurological (Parkinson's, MS)",
        conditionCardiovascular: "Cardiovascular (Heart disease)",
        conditionOther: "Other chronic condition",
        otherConditionLabel: "Please specify your chronic condition",
        otherConditionPlaceholder: "Describe your condition",
        respiratorySeverityLabel: "Please select the severity of your respiratory condition",
        severitySelect: "Select severity",
        severityMild: "Mild",
        severityMedium: "Medium",
        severitySevere: "Severe",
        voiceProblemsLabel: "Voice Problems",
        voiceProblemsSelect: "Select voice problems (if any)",
        voiceProblemNone: "None",
        voiceProblemNodules: "Vocal nodules",
        voiceProblemPolyps: "Vocal polyps",
        voiceProblemParalysis: "Vocal cord paralysis",
        voiceProblemLaryngitis: "Chronic laryngitis",
        voiceProblemOther: "Other voice problem",
        otherVoiceProblemLabel: "Please specify your voice problem",
        otherVoiceProblemPlaceholder: "Describe your voice problem",
        continueButton: "Continue to Voice Recording",
        step3Title: "Voice Recording",
        step3Subtitle: "Please describe what you see in the image below. Speak naturally for at least 30 seconds.",
        recordingInstruction: "Describe what you see in this image - the people, activities, setting, and any details you notice.",
        recordingStatusStart: "Click to start recording",
        recordingStatusRecording: "Recording... Click to stop",
        recordingStatusComplete: "Recording complete!",
        submitButton: "Submit Your Donation",
        consentText: "By submitting, you grant consent for anonymous use of your voice recording in health research, with data stored securely indefinitely for ongoing scientific analysis.",
        processingTitle: "Analyzing Your Voice",
        processingSubtitle: "Processing Audio Features",
        processingDescription: "Our AI is extracting over 60 vocal biomarkers from your recording. This analysis helps researchers identify subtle voice patterns that could indicate early signs of health conditions.",
        processingStatus: "Processing your voice donation...",
        processingWait: "This usually takes 1-2 minutes. Please keep this page open.",
        feature1: "✓ Pitch patterns",
        feature2: "✓ Voice quality",
        feature3: "✓ Speech rhythm",
        feature4: "✓ Spectral features",
        feature5: "✓ Intensity measures",
        feature6: "✓ Formant frequencies",
        successIcon: "🎉",
        successTitle: "Thank You!",
        successSubtitle: "Your voice sample has been successfully submitted and will contribute to life-changing voice analytics research.",
        successDescription: "Your anonymous donation contributes to developing AI that can detect health conditions years before symptoms appear, bringing proactive healthcare within reach for everyone.",
        privacyNote: "Your data is stored securely and used anonymously for health research. To request removal of your donation, please email privacy@munsait.com and include your Donation ID above for faster processing."
    },
    ar: {
        heroTitle: "تبرع بصوتك من أجل الصحة",
        heroSubtitle: "ساعدنا في إطلاق إمكانات الصوت للكشف المبكر عن الصحة. يساعد تبرعك في تدريب الذكاء الاصطناعي على تحديد علامات الحالات المزمنة في 30 ثانية فقط من الكلام—لبناء رعاية صحية استباقية للجميع.",
        trustBadge1: "آمن وفق HIPAA",
        trustBadge2: "مجهول الهوية",
        trustBadge3: "مدعوم بالذكاء الاصطناعي",
        step1Icon: "🚀",
        step1Title: "صوتك، مستقبلنا",
        step1Text: "كل صوت يحمل رؤى صحية مخفية. تحمل أنماطك الصوتية الفريدة أدلة يمكن أن تحول كيفية اكتشافنا ومنعنا للمرض. ساعدنا في بناء الأساس للرعاية الصحية المتاحة عالمياً.",
        stat1Number: "60+",
        stat1Label: "ميزات صوتية تم تحليلها",
        stat2Number: "30 ثانية",
        stat2Label: "الوقت المطلوب للمساهمة",
        step1Button: "ابدأ بالمساهمة",
        step2Icon: "💬",
        step2Title: "الاستبيان الصحي",
        step2Subtitle: "البيانات المجهولة تساعد في تدريب نماذج الذكاء الاصطناعي",
        donationLanguageLabel: "لغة التسجيل",
        donationLanguageSelect: "اختر لغة تسجيلك الصوتي",
        donationLanguageEnglish: "الإنجليزية",
        donationLanguageArabic: "العربية",
        ageLabel: "الفئة العمرية",
        ageSelect: "اختر فئتك العمرية",
        age1825: "18-25 سنة",
        age2635: "26-35 سنة",
        age3645: "36-45 سنة",
        age4655: "46-55 سنة",
        age5665: "56-65 سنة",
        age6675: "66-75 سنة",
        age76plus: "76+ سنة",
        conditionsLabel: "الحالات الصحية (اختر كل ما ينطبق)",
        conditionNone: "لا يوجد",
        conditionRespiratory: "تنفسية (الربو، انسداد رئوي)",
        conditionNeurological: "عصبية (باركنسون، تصلب متعدد)",
        conditionCardiovascular: "قلبية وعائية (أمراض القلب)",
        conditionOther: "حالة مزمنة أخرى",
        otherConditionLabel: "يرجى تحديد حالتك المزمنة",
        otherConditionPlaceholder: "اوصف حالتك",
        respiratorySeverityLabel: "يرجى اختيار شدة حالتك التنفسية",
        severitySelect: "اختر الشدة",
        severityMild: "خفيف",
        severityMedium: "متوسط",
        severitySevere: "شديد",
        voiceProblemsLabel: "مشاكل الصوت",
        voiceProblemsSelect: "اختر مشاكل الصوت (إن وجدت)",
        voiceProblemNone: "لا يوجد",
        voiceProblemNodules: "عقد صوتية",
        voiceProblemPolyps: "لحميات صوتية",
        voiceProblemParalysis: "شلل الحبال الصوتية",
        voiceProblemLaryngitis: "التهاب الحنجرة المزمن",
        voiceProblemOther: "مشكلة صوتية أخرى",
        otherVoiceProblemLabel: "يرجى تحديد مشكلتك الصوتية",
        otherVoiceProblemPlaceholder: "اوصف مشكلتك الصوتية",
        continueButton: "المتابعة إلى تسجيل الصوت",
        step3Title: "تسجيل الصوت",
        step3Subtitle: "يرجى وصف ما تراه في الصورة أدناه. تحدث بشكل طبيعي لمدة 30 ثانية على الأقل.",
        recordingInstruction: "صف ما تراه في هذه الصورة - الأشخاص والأنشطة والبيئة وأي تفاصيل تلاحظها.",
        recordingStatusStart: "اضغط لبدء التسجيل",
        recordingStatusRecording: "جاري التسجيل... اضغط للتوقف",
        recordingStatusComplete: "اكتمل التسجيل!",
        submitButton: "أرسل تبرعك",
        consentText: "من خلال الإرسال، فإنك توافق على الاستخدام المجهول لتسجيل صوتك في الأبحاث الصحية، مع تخزين البيانات بشكل آمن إلى أجل غير مسمى للتحليل العلمي المستمر.",
        processingTitle: "تحليل صوتك",
        processingSubtitle: "معالجة الميزات الصوتية",
        processingDescription: "يقوم الذكاء الاصطناعي بتحليل أكثر من 60 مؤشر صوتي من تسجيلك. يساعد هذا التحليل الباحثين في تحديد الأنماط الصوتية الدقيقة التي قد تشير إلى علامات مبكرة للحالات الصحية.",
        processingStatus: "جاري معالجة تبرعك الصوتي...",
        processingWait: "يستغرق هذا عادة 1-2 دقيقة. يرجى إبقاء هذه الصفحة مفتوحة.",
        feature1: "✓ أنماط الطبقة الصوتية",
        feature2: "✓ جودة الصوت",
        feature3: "✓ إيقاع الكلام",
        feature4: "✓ الميزات الطيفية",
        feature5: "✓ قياسات الشدة",
        feature6: "✓ ترددات التكوين",
        successIcon: "🎉",
        successTitle: "شكراً لك!",
        successSubtitle: "تم إرسال عينة صوتك بنجاح وستساهم في أبحاث التحليل الصوتي المغيرة للحياة.",
        successDescription: "يساهم تبرعك المجهول في تطوير ذكاء اصطناعي يمكنه اكتشاف الحالات الصحية قبل سنوات من ظهور الأعراض، مما يجعل الرعاية الصحية الاستباقية في متناول الجميع.",
        privacyNote: "يتم تخزين بياناتك بأمان واستخدامها بشكل مجهول للبحوث الصحية. لطلب إزالة تبرعك، يرجى مراسلة privacy@munsait.com وتضمين معرف التبرع أعلاه لمعالجة أسرع."
    }
};

// Create particles
function createParticles() {
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;

    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.width = particle.style.height = (Math.random() * 4 + 2) + 'px';
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (Math.random() * 10 + 15) + 's';
        particlesContainer.appendChild(particle);
    }
}

// Step navigation
function nextStep() {
    console.log('nextStep called, currentStep:', currentStep);

    // Validate questionnaire on step 2
    if (currentStep === 2 && !validateQuestionnaire()) {
        return;
    }

    // Check for audio recording on step 3
    if (currentStep === 3 && !audioChunks.length) {
        alert('Please record your voice first.');
        return;
    }

    // Submit donation on step 3
    if (currentStep === 3) {
        submitDonation();
        return;
    }

    document.getElementById(`step${currentStep}`).classList.remove('active');
    currentStep++;

    // Load random picture when entering recording step
    if (currentStep === 3) {
        loadRandomPicture();
    }

    document.getElementById(`step${currentStep}`).classList.add('active');
}

function loadRandomPicture() {
    const randomIndex = Math.floor(Math.random() * pictureUrls.length);
    const imgElement = document.getElementById('randomPicture');
    if (imgElement) {
        imgElement.src = pictureUrls[randomIndex];
    }
}

// Language switching
function switchLanguage(lang) {
    console.log('switchLanguage called with:', lang);

    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";

    // Toggle active class
    document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
    const langBtn = document.getElementById(`lang-${lang}`);
    if (langBtn) {
        langBtn.classList.add('active');
    }

    // Translate all elements with data-translate
    document.querySelectorAll('[data-translate]').forEach(el => {
        const key = el.getAttribute('data-translate');
        const translation = translations[lang][key];
        if (translation) {
            el.textContent = translation;
        }
    });
}

// Form validation
function validateQuestionnaire() {
    const language = document.getElementById('donationLanguage');
    const ageGroup = document.getElementById('ageGroup');
    const chronicConditions = Array.from(document.querySelectorAll('input[name="chronicConditions"]:checked')).map(cb => cb.value);
    const voiceProblems = document.getElementById('voiceProblems');

    if (!language || !ageGroup || !voiceProblems) {
        console.log('Missing form elements');
        return false;
    }

    if (!language.value || !ageGroup.value || chronicConditions.length === 0 || !voiceProblems.value) {
        console.log('Missing form values');
        return false;
    }

    // Check conditional fields
    const otherConditionRequired = chronicConditions.includes('other') && !document.getElementById('otherCondition').value.trim();
    const otherVoiceProblemRequired = voiceProblems.value === 'other' && !document.getElementById('otherVoiceProblem').value.trim();
    const respiratorySeverityRequired = chronicConditions.includes('respiratory') && !document.getElementById('respiratorySeverity').value;

    if (otherConditionRequired || otherVoiceProblemRequired || respiratorySeverityRequired) {
        return false;
    }

    return true;
}

function updateContinueButton() {
    const button = document.getElementById('continueButton');
    if (button && validateQuestionnaire()) {
        button.disabled = false;
        button.style.opacity = '1';
    } else if (button) {
        button.disabled = true;
        button.style.opacity = '0.5';
    }
}

function handleChronicConditionChange() {
    const checkedConditions = Array.from(document.querySelectorAll('input[name="chronicConditions"]:checked')).map(cb => cb.value);

    // Handle "None" exclusivity
    if (checkedConditions.includes('none') && checkedConditions.length > 1) {
        document.querySelectorAll('input[name="chronicConditions"]').forEach(cb => {
            if (cb.value !== 'none') cb.checked = false;
        });
        // Recalculate after changes
        const newCheckedConditions = Array.from(document.querySelectorAll('input[name="chronicConditions"]:checked')).map(cb => cb.value);
        checkedConditions.length = 0;
        checkedConditions.push(...newCheckedConditions);
    } else if (checkedConditions.length > 0 && !checkedConditions.includes('none')) {
        const noneCheckbox = document.getElementById('condition_none');
        if (noneCheckbox) noneCheckbox.checked = false;
    }

    // Show/hide conditional fields
    const otherGroup = document.getElementById('otherConditionGroup');
    const respiratoryGroup = document.getElementById('respiratorySeverityGroup');

    if (checkedConditions.includes('other')) {
        if (otherGroup) otherGroup.classList.remove('hidden');
    } else {
        if (otherGroup) {
            otherGroup.classList.add('hidden');
            const otherInput = document.getElementById('otherCondition');
            if (otherInput) otherInput.value = '';
        }
    }

    if (checkedConditions.includes('respiratory')) {
        if (respiratoryGroup) respiratoryGroup.classList.remove('hidden');
    } else {
        if (respiratoryGroup) {
            respiratoryGroup.classList.add('hidden');
            const severitySelect = document.getElementById('respiratorySeverity');
            if (severitySelect) severitySelect.value = '';
        }
    }

    // Update checkbox styling
    document.querySelectorAll('.checkbox-card').forEach(item => {
        const checkbox = item.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });

    updateContinueButton();
}

function handleVoiceProblemsChange() {
    const voiceProblems = document.getElementById('voiceProblems').value;
    const otherVoiceGroup = document.getElementById('otherVoiceProblemGroup');

    if (voiceProblems === 'other') {
        if (otherVoiceGroup) otherVoiceGroup.classList.remove('hidden');
    } else {
        if (otherVoiceGroup) {
            otherVoiceGroup.classList.add('hidden');
            const otherInput = document.getElementById('otherVoiceProblem');
            if (otherInput) otherInput.value = '';
        }
    }

    updateContinueButton();
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

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    createParticles();

    // Form event listeners
    const chronicConditionCheckboxes = document.querySelectorAll('input[name="chronicConditions"]');
    chronicConditionCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleChronicConditionChange);
    });

    const formInputs = ['donationLanguage', 'ageGroup', 'voiceProblems', 'otherCondition', 'otherVoiceProblem', 'respiratorySeverity'];
    formInputs.forEach(inputId => {
        const element = document.getElementById(inputId);
        if (element) {
            element.addEventListener('change', updateContinueButton);
            element.addEventListener('input', updateContinueButton);
        }
    });

    const voiceProblemsSelect = document.getElementById('voiceProblems');
    if (voiceProblemsSelect) {
        voiceProblemsSelect.addEventListener('change', handleVoiceProblemsChange);
    }

    updateContinueButton();
    console.log('Initialization complete');
});