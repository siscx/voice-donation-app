// form-validation.js - All questionnaire validation and handling logic

// Form validation
function validateQuestionnaire() {
    const language = document.getElementById('donationLanguage');
    const ageGroup = document.getElementById('ageGroup');

    // Get health conditions (new enhanced system)
    const healthConditions = Array.from(document.querySelectorAll('input[name="healthConditions"]:checked')).map(cb => cb.value);

    if (!language || !ageGroup) {
        console.log('Missing form elements');
        return false;
    }

    if (!language.value || !ageGroup.value || healthConditions.length === 0) {
        console.log('Missing form values');
        return false;
    }

    // Special "other" conditions that need text specification instead of severity
    const otherConditions = ['respiratory_other', 'mood_other', 'voice_other'];

    // Check that selected conditions have severity specified (except "none", "other_general", and category "other" conditions)
    for (const condition of healthConditions) {
        if (condition !== 'none' && condition !== 'other_general' && !otherConditions.includes(condition)) {
            const severitySelect = document.getElementById(`severity_${condition}`);
            if (severitySelect && !severitySelect.value) {
                console.log(`Missing severity for ${condition}`);
                return false;
            }
        }
    }

    // Check if "other" conditions in categories have text specification
    for (const condition of healthConditions) {
        if (otherConditions.includes(condition)) {
            const specifyInput = document.getElementById(`specify_${condition}`);
            if (!specifyInput || !specifyInput.value.trim()) {
                console.log(`Missing specification for ${condition}`);
                return false;
            }
        }
    }

    // Check if other_general is selected and text is provided
    if (healthConditions.includes('other_general')) {
        const otherGeneralInput = document.getElementById('otherGeneralCondition');
        if (!otherGeneralInput || !otherGeneralInput.value.trim()) {
            console.log('Missing text for other_general condition');
            return false;
        }
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

// Enhanced Medical Conditions Functions
function toggleCategory(categoryId) {
    const content = document.getElementById(`category-${categoryId}`);
    const header = content.previousElementSibling;

    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        header.classList.add('expanded');
    } else {
        content.classList.add('collapsed');
        header.classList.remove('expanded');
    }
}

function handleConditionCheckboxChange(event) {
    const checkbox = event.target;
    const conditionValue = checkbox.value;
    const severitySelect = document.getElementById(`severity_${conditionValue}`);

    // Special handling for "other" conditions that need text specification
    const otherConditions = ['respiratory_other', 'mood_other', 'voice_other'];
    const isOtherCondition = otherConditions.includes(conditionValue);
    const specifyInput = isOtherCondition ? document.getElementById(`specify_${conditionValue}`) : null;

    if (checkbox.checked) {
        // Show severity dropdown OR text input for "other" conditions
        if (isOtherCondition && specifyInput) {
            specifyInput.classList.remove('hidden');
            // Map condition values to translation keys explicitly
            const placeholderKeys = {
                'respiratory_other': 'specifyRespiratoryOtherPlaceholder',
                'mood_other': 'specifyMoodOtherPlaceholder',
                'voice_other': 'specifyVoiceOtherPlaceholder'
            };
            updatePlaceholderText(specifyInput, placeholderKeys[conditionValue]);
        } else if (severitySelect) {
            severitySelect.classList.remove('hidden');
            severitySelect.classList.add('visible');
        }

        // Handle "other_general" condition to show text field
        if (conditionValue === 'other_general') {
            const otherGeneralGroup = document.getElementById('otherGeneralConditionGroup');
            if (otherGeneralGroup) {
                otherGeneralGroup.classList.remove('hidden');
                const otherGeneralInput = document.getElementById('otherGeneralCondition');
                if (otherGeneralInput) {
                    updatePlaceholderText(otherGeneralInput, 'otherGeneralConditionPlaceholder');
                }
            }
        }

        // If "none" is selected, uncheck all other conditions
        if (conditionValue === 'none') {
            const allConditions = document.querySelectorAll('input[name="healthConditions"]:not([value="none"])');
            allConditions.forEach(cb => {
                cb.checked = false;
                const severityDropdown = document.getElementById(`severity_${cb.value}`);
                const specifyField = document.getElementById(`specify_${cb.value}`);

                if (severityDropdown) {
                    severityDropdown.classList.add('hidden');
                    severityDropdown.value = '';
                }
                if (specifyField) {
                    specifyField.classList.add('hidden');
                    specifyField.value = '';
                }
            });
            // Also hide the other general condition text field
            const otherGeneralGroup = document.getElementById('otherGeneralConditionGroup');
            if (otherGeneralGroup) {
                otherGeneralGroup.classList.add('hidden');
                const otherInput = document.getElementById('otherGeneralCondition');
                if (otherInput) otherInput.value = '';
            }
        } else {
            // If any other condition is selected, uncheck "none"
            const noneCheckbox = document.getElementById('condition_none');
            if (noneCheckbox) {
                noneCheckbox.checked = false;
            }
        }
    } else {
        // Hide severity dropdown/text input and clear value
        if (isOtherCondition && specifyInput) {
            specifyInput.classList.add('hidden');
            specifyInput.value = '';
        } else if (severitySelect) {
            severitySelect.classList.add('hidden');
            severitySelect.classList.remove('visible');
            severitySelect.value = '';
        }

        // Handle unchecking "other_general" condition
        if (conditionValue === 'other_general') {
            const otherGeneralGroup = document.getElementById('otherGeneralConditionGroup');
            if (otherGeneralGroup) {
                otherGeneralGroup.classList.add('hidden');
                const otherInput = document.getElementById('otherGeneralCondition');
                if (otherInput) otherInput.value = '';
            }
        }
    }

    // Update checkbox styling
    updateCheckboxStyling();
    updateContinueButton();
}

function updateCheckboxStyling() {
    document.querySelectorAll('.condition-checkbox').forEach(checkbox => {
        const card = checkbox.closest('.checkbox-card');
        if (checkbox.checked) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
}

function updatePlaceholderText(element, translationKey) {
    const currentLang = document.documentElement.lang || 'en';
    const translation = translations[currentLang][translationKey];

    console.log('updatePlaceholderText:', {
        element: element.id,
        translationKey: translationKey,
        currentLang: currentLang,
        translation: translation
    });

    if (translation) {
        element.placeholder = translation;
    }
}

// Initialize form validation - SINGLE DEFINITION
function initializeFormValidation() {
    // Enhanced medical conditions listeners
    const healthConditionCheckboxes = document.querySelectorAll('input[name="healthConditions"]');
    healthConditionCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleConditionCheckboxChange);
    });

    // Enhanced validation for severity selects
    const severitySelects = document.querySelectorAll('.severity-select');
    severitySelects.forEach(select => {
        select.addEventListener('change', updateContinueButton);
    });

    // Form inputs including the new condition text fields
    const formInputs = ['donationLanguage', 'ageGroup', 'otherGeneralCondition', 'specify_respiratory_other', 'specify_mood_other', 'specify_voice_other'];
    formInputs.forEach(inputId => {
        const element = document.getElementById(inputId);
        if (element) {
            element.addEventListener('change', updateContinueButton);
            element.addEventListener('input', updateContinueButton);
        }
    });

    // Populate native language dropdown
    populateNativeLanguageDropdown();

    // Add donation language change listener
    const donationLanguageSelect = document.getElementById('donationLanguage');
    if (donationLanguageSelect) {
        donationLanguageSelect.addEventListener('change', handleDonationLanguageChange);
    }

    // Add new fields to validation
    const newFormInputs = ['nativeLanguage', 'arabicDialect'];
    newFormInputs.forEach(inputId => {
        const element = document.getElementById(inputId);
        if (element) {
            element.addEventListener('change', updateContinueButton);
        }
    });

    updateContinueButton();
}

// Add this new function
function handleDonationLanguageChange() {
    const donationLanguage = document.getElementById('donationLanguage').value;
    const nativeLanguageGroup = document.getElementById('nativeLanguageGroup');
    const arabicDialectGroup = document.getElementById('arabicDialectGroup');

    // Hide both groups initially
    if (nativeLanguageGroup) nativeLanguageGroup.classList.add('hidden');
    if (arabicDialectGroup) arabicDialectGroup.classList.add('hidden');

    // Clear their values
    const nativeLanguageSelect = document.getElementById('nativeLanguage');
    const arabicDialectSelect = document.getElementById('arabicDialect');
    if (nativeLanguageSelect) nativeLanguageSelect.value = '';
    if (arabicDialectSelect) arabicDialectSelect.value = '';

    // Show appropriate group
    if (donationLanguage === 'english' && nativeLanguageGroup) {
        nativeLanguageGroup.classList.remove('hidden');
    } else if (donationLanguage === 'arabic' && arabicDialectGroup) {
        arabicDialectGroup.classList.remove('hidden');
    }

    updateContinueButton();
}

function populateNativeLanguageDropdown() {
    const select = document.getElementById('nativeLanguage');
    if (!select) return;

    console.log('ISO639 available:', typeof ISO6391);

    if (typeof ISO6391 !== 'undefined') {
        try {
            // Get all languages with their codes and names
            const languages = ISO6391.getAllCodes().map(code => ({
                code: code,
                name: ISO6391.getName(code)
            }));

            console.log('Languages loaded:', languages.length);

            // Sort alphabetically by name
            languages.sort((a, b) => a.name.localeCompare(b.name));

            languages.forEach(({code, name}) => {
                const option = document.createElement('option');
                option.value = code;
                option.textContent = name;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Error with ISO6391:', error);
        }
    } else {
        console.log('ISO6391 not loaded');
    }
}