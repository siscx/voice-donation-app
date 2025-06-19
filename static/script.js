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

    // Stop testimonials when leaving step 1
    if (currentStep === 2) {
        stopTestimonialRotation();
    }

    document.getElementById(`step${currentStep}`).classList.add('active');
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

// Tab switching functionality
function switchTab(tabName) {
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

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM loaded, initializing...');
    createParticles();

    // Load HTML components
    await loadComponents();

    // Start testimonials rotation on step 1
    startTestimonialRotation();

    console.log('Initialization complete');
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