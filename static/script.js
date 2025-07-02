// Global variables
let currentStep = 1;

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

    // Preserve current language
    const currentLang = document.documentElement.lang || 'en';

    // Validate questionnaire on step 2
    if (currentStep === 2 && !validateQuestionnaire()) {
        return;
    }

    document.getElementById(`step${currentStep}`).classList.remove('active');
    currentStep++;

    // Hide hero after leaving landing page
    if (currentStep === 2) {
        const hero = document.querySelector('.hero');
        if (hero) {
            hero.style.display = 'none';
        }
    }

    // UPDATED: Initialize multi-task recording when entering recording step
    if (currentStep === 3) {
        initializeMultiTaskRecording(); // New function from audio-recorder.js
    }

    // Stop testimonials when leaving step 1
    if (currentStep === 2) {
        stopTestimonialRotation();
    }

    document.getElementById(`step${currentStep}`).classList.add('active');

    // CRITICAL: Restore language state after step transition
    if (currentLang === 'ar') {
        switchLanguage('ar');
    }

    // Scroll to top when moving to next step
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function clearMultiTaskRecording() {
    console.log('Clearing multi-task recording...');

    // Clear task recordings
    if (typeof taskRecordings !== 'undefined') {
        taskRecordings = {};
    }

    // Reset task state
    if (typeof currentTask !== 'undefined') {
        currentTask = 1;
    }

    // Clear current audio recording (existing function)
    clearAudioRecording();

    console.log('Multi-task recording cleared successfully');
}

// Language switching
function switchLanguage(lang) {
    // Close the language dropdown when language is selected
    document.getElementById('languageDropdown').classList.remove('show');

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
    }); // <- This closing bracket was missing

    // Update dynamic placeholders for any visible conditional fields
    const conditionalInputs = [
        { id: 'specify_respiratory_other', key: 'specifyRespiratoryOtherPlaceholder' },
        { id: 'specify_mood_other', key: 'specifyMoodOtherPlaceholder' },
        { id: 'specify_voice_other', key: 'specifyVoiceOtherPlaceholder' },
        { id: 'otherGeneralCondition', key: 'otherGeneralConditionPlaceholder' }
    ];

    conditionalInputs.forEach(input => {
        const element = document.getElementById(input.id);
        if (element && !element.classList.contains('hidden')) {
            const translation = translations[lang][input.key];
            if (translation) {
                element.placeholder = translation;
            }
        }
    });
}

// Tab switching functionality
// Complete switchTab function with form clearing functionality
// Replace your existing switchTab function with this:

function switchTab(tabName) {
    // Close the hamburger menu when tab is selected
    document.getElementById('menuDropdown').classList.remove('show');

    console.log('Switching to tab:', tabName);

    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab content
    const targetTab = document.getElementById(`tab-${tabName}`);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // Add active class to clicked button
    event.target.classList.add('active');

    // Reset to step 1 when going back to home tab
    if (tabName === 'home') {
        currentStep = 1;
        document.querySelectorAll('.step').forEach(step => step.classList.remove('active'));
        document.getElementById('step1').classList.add('active');

        // CLEAR ALL FORM DATA AND RESET STATE
        clearAllFormData();
    }
}

// Add this new function to clear all form data and reset state
function clearAllFormData() {
    console.log('Clearing all form data...');

    // Clear basic form fields
    const form = document.getElementById('questionnaireForm');
    if (form) {
        form.reset();
    }

    // Clear donation language and age group specifically
    const donationLanguage = document.getElementById('donationLanguage');
    const ageGroup = document.getElementById('ageGroup');
    if (donationLanguage) donationLanguage.value = '';
    if (ageGroup) ageGroup.value = '';

    // Clear all health condition checkboxes
    document.querySelectorAll('input[name="healthConditions"]').forEach(checkbox => {
        checkbox.checked = false;
    });

    // Clear and hide all severity selects
    document.querySelectorAll('.severity-select').forEach(select => {
        select.value = '';
        select.classList.add('hidden');
        select.classList.remove('visible');
    });

    // Clear and hide all specification text inputs
    const specificationFields = [
        'specify_respiratory_other',
        'specify_mood_other',
        'specify_voice_other',
        'otherGeneralCondition'
    ];

    specificationFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = '';
            field.classList.add('hidden');
        }
    });

    // Hide other general condition group
    const otherGeneralGroup = document.getElementById('otherGeneralConditionGroup');
    if (otherGeneralGroup) {
        otherGeneralGroup.classList.add('hidden');
    }

    // Reset checkbox card styling
    document.querySelectorAll('.checkbox-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Collapse all category sections
    document.querySelectorAll('.category-content').forEach(content => {
        content.classList.add('collapsed');
    });

    document.querySelectorAll('.category-header').forEach(header => {
        header.classList.remove('expanded');
    });

    // Clear audio recording state
    clearAudioRecording();

    // NEW: Clear multi-task recording state
    clearMultiTaskRecording();

    // Reset continue button state
    updateContinueButton();

    console.log('Form data cleared successfully');
}

// Add this function to clear audio recording state
function clearAudioRecording() {
    console.log('Clearing audio recording...');

    // Clear audio chunks array
    if (typeof audioChunks !== 'undefined') {
        audioChunks = [];
    }

    // Reset recording UI elements
    const recordButton = document.getElementById('recordButton');
    const recordIcon = document.getElementById('recordIcon');
    const recordingTimer = document.getElementById('recordingTimer');
    const audioPlayback = document.getElementById('audioPlayback');
    const audioPlayer = document.getElementById('audioPlayer');

    if (recordButton) {
        recordButton.classList.remove('recording');
    }

    if (recordIcon) {
        recordIcon.textContent = '🎤';
    }

    if (recordingTimer) {
        recordingTimer.textContent = '00:00';
    }

    if (audioPlayback) {
        audioPlayback.classList.add('hidden');
    }

    if (audioPlayer) {
        audioPlayer.src = '';
    }

    // Clear any active recording interval
    if (typeof recordingInterval !== 'undefined' && recordingInterval) {
        clearInterval(recordingInterval);
        recordingInterval = null;
    }

    // Stop any active media recorder
    if (typeof mediaRecorder !== 'undefined' && mediaRecorder && mediaRecorder.state !== 'inactive') {
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

    console.log('Audio recording cleared successfully');
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

// Testimonials rotation
let currentTestimonial = 0;
const totalTestimonials = 4;
let testimonialInterval;

function rotateTestimonials() {
    const currentSlide = document.getElementById(`testimonial-${currentTestimonial}`);
    if (currentSlide) {
        currentSlide.classList.remove('active');
    }

    currentTestimonial = (currentTestimonial + 1) % totalTestimonials;

    const nextSlide = document.getElementById(`testimonial-${currentTestimonial}`);
    if (nextSlide) {
        nextSlide.classList.add('active');
    }
}

function startTestimonialRotation() {
    // Start rotation every 10 seconds
    testimonialInterval = setInterval(rotateTestimonials, 10000);
}

function stopTestimonialRotation() {
    if (testimonialInterval) {
        clearInterval(testimonialInterval);
    }
}

// Toggle hamburger menu
function toggleMenu() {
    const dropdown = document.getElementById('menuDropdown');
    dropdown.classList.toggle('show');
}

// Toggle language dropdown
function toggleLanguageMenu() {
    const dropdown = document.getElementById('languageDropdown');
    dropdown.classList.toggle('show');
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    const menuDropdown = document.getElementById('menuDropdown');
    const langDropdown = document.getElementById('languageDropdown');
    const hamburger = document.querySelector('.main-tabs');
    const langSwitcher = document.querySelector('.language-switcher');

    // Close menu dropdown if clicked outside
    if (!hamburger.contains(event.target) && !menuDropdown.contains(event.target)) {
        menuDropdown.classList.remove('show');
    }

    // Close language dropdown if clicked outside
    if (!langSwitcher.contains(event.target) && !langDropdown.contains(event.target)) {
        langDropdown.classList.remove('show');
    }
});

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM loaded, initializing...');

    // Auto-detect and LOCK language from URL
    const path = window.location.pathname;
    let detectedLang = 'en'; // default

    if (path === '/ar') {
        detectedLang = 'ar';
        // Store in sessionStorage to persist through step changes
        sessionStorage.setItem('appLanguage', 'ar');
    } else if (path === '/en') {
        detectedLang = 'en';
        sessionStorage.setItem('appLanguage', 'en');
    } else {
        // Check if we have a stored language preference
        const storedLang = sessionStorage.getItem('appLanguage');
        if (storedLang) {
            detectedLang = storedLang;
        }
    }

    switchLanguage(detectedLang);

    createParticles();

    // Load HTML components
    await loadComponents();

    // Start testimonials rotation on step 1
    startTestimonialRotation();

    console.log('Initialization complete with language:', detectedLang);
});

// Simple HTML include function
async function includeHTML(elementId, filePath) {
    try {
        const response = await fetch(filePath);
        const html = await response.text();
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = html;
        }
    } catch (error) {
        console.error(`Failed to load ${filePath}:`, error);
    }
}

// Load components on page load
async function loadComponents() {
    await includeHTML('questionnaire-placeholder', '/static/questionnaire-section.html');
    await includeHTML('recording-placeholder', '/static/recording-section.html');

    // Re-initialize form validation after loading questionnaire
    initializeFormValidation();
}