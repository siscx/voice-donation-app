// form-validation.js - All questionnaire validation and handling logic

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

// Initialize form validation
function initializeFormValidation() {
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
}