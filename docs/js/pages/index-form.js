(function initCitizenGrievanceForm(globalScope) {
    const state = {
        currentUser: null,
        uploadedImages: [],
        imagesRequired: true,
        predictedDepartment: null,
        predictionConfidence: null,
        predictTimer: null,
        onSubmitted: null,
        showAlert: null,
    };

    function notify(message, type = 'info') {
        if (typeof state.showAlert === 'function') {
            state.showAlert(message, type);
            return;
        }
        if (typeof showAlert === 'function') {
            showAlert(message, type);
        }
    }

    function getImageDropZone() {
        return document.getElementById('imageDropZone');
    }

    function updateImageRequirementUI(required, department, predictionConfidence = null, requiresManualReview = false) {
        state.imagesRequired = !!required;
        state.predictedDepartment = department || null;
        state.predictionConfidence = typeof predictionConfidence === 'number' ? predictionConfidence : null;

        const requirementLabel = document.getElementById('imageRequirementLabel');
        const requirementHint = document.getElementById('imageRequirementHint');
        const departmentHint = document.getElementById('predictedDepartmentHint');
        const dropZone = getImageDropZone();

        if (requirementLabel) {
            requirementLabel.setAttribute('data-translate', required ? 'mandatory' : 'optional');
            requirementLabel.textContent = required ? '* MANDATORY' : '* OPTIONAL';
            requirementLabel.style.color = required ? '#ef4444' : '#16a34a';
        }

        if (requirementHint) {
            const key = required ? 'mandatory_image_hint' : 'optional_image_hint';
            requirementHint.setAttribute('data-translate', key);
            requirementHint.textContent = required 
                ? `At least 1 image is mandatory for ${department || 'this'} complaints.`
                : `Images are optional for ${department || 'this'} complaints, but helpful for faster verification.`;
            requirementHint.style.color = required ? '#ef4444' : '#047857';
        }

        if (departmentHint) {
            if (department) {
                const confidenceText = (
                    state.predictionConfidence !== null
                        ? ` (${(state.predictionConfidence * 100).toFixed(1)}% confidence)`
                        : ''
                );
                const routingText = requiresManualReview ? ' - manual review likely' : '';
                departmentHint.innerHTML = `<span data-translate="predicted_dept">Predicted department</span>: <span data-translate="${department.toLowerCase().replace(/ & /g, '_').replace(/ \/ /g, '_').replace(/ /g, '_')}">${department}</span>${confidenceText}${routingText}`;
                departmentHint.style.display = 'block';
            } else {
                departmentHint.style.display = 'none';
            }
        }
        
        // Trigger translation
        if (typeof applyTranslations === 'function') {
            applyTranslations();
        }

        if (dropZone) {
            const shouldHighlightRequired = required && state.uploadedImages.length === 0;
            dropZone.classList.toggle('required-upload', shouldHighlightRequired);
            dropZone.classList.toggle('optional-upload', !required);
        }
    }

    async function predictDepartmentFromComplaint() {
        const complaintField = document.getElementById('complaint');
        if (!complaintField) return;

        const complaintText = complaintField.value.trim();
        if (complaintText.length < 20) {
            updateImageRequirementUI(true, null);
            return;
        }

        try {
            const result = await apiCall('/grievances/predict-department', {
                method: 'POST',
                body: JSON.stringify({ complaint_text: complaintText }),
            });
            updateImageRequirementUI(
                result.images_required,
                result.department,
                result.prediction_confidence,
                result.requires_manual_review
            );
        } catch (_) {
            // Keep default required mode on prediction errors.
            updateImageRequirementUI(true, null);
        }
    }

    function debouncedPredictDepartment() {
        if (state.predictTimer) {
            clearTimeout(state.predictTimer);
        }
        state.predictTimer = setTimeout(() => {
            predictDepartmentFromComplaint();
        }, 450);
    }

    function displayImagePreviews() {
        const container = document.getElementById('imagePreviewContainer');
        const dropZone = getImageDropZone();
        if (!container || !dropZone) return;

        if (!state.uploadedImages.length) {
            container.style.display = 'none';
            dropZone.classList.toggle('required-upload', state.imagesRequired);
            return;
        }

        container.style.display = 'grid';
        dropZone.classList.remove('required-upload');
        container.innerHTML = state.uploadedImages.map((img, index) => `
            <div class="preview-item">
                <img src="${img}" class="preview-image" alt="Uploaded evidence preview ${index + 1}">
                <button type="button" class="remove-image" data-index="${index}" aria-label="Remove image ${index + 1}">×</button>
            </div>
        `).join('');

        container.querySelectorAll('.remove-image').forEach((button) => {
            button.addEventListener('click', () => {
                const idx = Number(button.getAttribute('data-index'));
                removeImage(idx);
            });
        });
    }

    function removeImage(index) {
        if (index < 0 || index >= state.uploadedImages.length) return;
        state.uploadedImages.splice(index, 1);
        displayImagePreviews();
    }

    function handleImageFileSelection(event) {
        const files = Array.from(event.target.files || []);
        if (!files.length) return;

        if (state.uploadedImages.length + files.length > 5) {
            notify('Maximum 5 images allowed', 'error');
            return;
        }

        files.forEach((file) => {
            if (file.size > 5 * 1024 * 1024) {
                notify('Image size must be less than 5MB', 'error');
                return;
            }
            const reader = new FileReader();
            reader.onload = (loadEvent) => {
                state.uploadedImages.push(loadEvent.target.result);
                displayImagePreviews();
            };
            reader.readAsDataURL(file);
        });
    }

    async function submitGrievance(event) {
        event.preventDefault();

        const complaintText = document.getElementById('complaint')?.value.trim() || '';
        const location = document.getElementById('location')?.value.trim() || '';

        if (!state.currentUser) {
            notify('Session expired. Please login again.', 'error');
            return;
        }

        if (
            !state.currentUser.residential_address
            || !state.currentUser.residential_city
            || !state.currentUser.residential_state
            || !state.currentUser.residential_pincode
        ) {
            notify('Please complete your residential address in your profile before submitting complaints', 'error');
            return;
        }

        if (complaintText.length < 20) {
            notify('Complaint must be at least 20 characters long', 'error');
            return;
        }

        // Refresh requirement from backend prediction before final validation.
        await predictDepartmentFromComplaint();

        notify('Submitting your grievance...', 'info');

        try {
            const response = await apiCall('/grievances/submit', {
                method: 'POST',
                body: JSON.stringify({
                    complaint_text: complaintText,
                    location,
                    images: state.uploadedImages,
                }),
            });

            let submitMessage = `Grievance submitted successfully! ID: #${response.grievance_id}`;
            if (response.routing_decision === 'manual_review') {
                submitMessage += ' This case has been routed for manual triage review.';
            }
            notify(submitMessage, 'success');
            const form = document.getElementById('grievanceForm');
            if (form) {
                form.reset();
            }
            state.uploadedImages = [];
            displayImagePreviews();
            updateImageRequirementUI(true, null);

            if (typeof state.onSubmitted === 'function') {
                state.onSubmitted(response);
            }
        } catch (error) {
            notify(error.message || 'Failed to submit grievance', 'error');
        }
    }

    function setupVoiceInput() {
        const voiceButton = document.getElementById('voiceBtn');
        if (!voiceButton) return;

        voiceButton.addEventListener('click', () => {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                notify('Voice input not supported in this browser', 'error');
                return;
            }
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-IN';
            recognition.onresult = (voiceEvent) => {
                const text = voiceEvent.results[0][0].transcript;
                const complaintField = document.getElementById('complaint');
                if (!complaintField) return;
                complaintField.value += complaintField.value ? ` ${text}` : text;
                debouncedPredictDepartment();
            };
            recognition.onerror = () => notify('Could not hear. Please try again.', 'error');
            recognition.start();
            notify('Listening... Speak your complaint.', 'info');
        });
    }

    function setupGeolocation() {
        const geoButton = document.getElementById('geoBtn');
        const locationField = document.getElementById('location');
        if (!geoButton || !locationField) return;

        geoButton.addEventListener('click', () => {
            if (!navigator.geolocation) {
                notify('Geolocation not supported', 'error');
                return;
            }
            geoButton.textContent = 'Getting location...';
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude.toFixed(6);
                    const lon = position.coords.longitude.toFixed(6);
                    locationField.value = `Lat: ${lat}, Long: ${lon} (GPS coordinates)`;
                    geoButton.textContent = '📍 Use GPS';
                },
                () => {
                    notify('Could not get location. Enter manually.', 'error');
                    geoButton.textContent = '📍 Use GPS';
                }
            );
        });
    }

    function setupFileDropZone() {
        const dropZone = getImageDropZone();
        const fileInput = document.getElementById('complaintImages');
        if (!dropZone || !fileInput) return;

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                fileInput.click();
            }
        });
        dropZone.addEventListener('dragover', (event) => {
            event.preventDefault();
            dropZone.classList.add('drag-active');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-active'));
        dropZone.addEventListener('drop', (event) => {
            event.preventDefault();
            dropZone.classList.remove('drag-active');
            const files = event.dataTransfer?.files ? Array.from(event.dataTransfer.files) : [];
            if (!files.length) return;
            const syntheticEvent = { target: { files } };
            handleImageFileSelection(syntheticEvent);
        });
    }

    function initialize(options = {}) {
        state.currentUser = options.currentUser || null;
        state.onSubmitted = options.onSubmitted || null;
        state.showAlert = options.showAlert || null;
        state.uploadedImages = [];
        updateImageRequirementUI(true, null);

        const complaintField = document.getElementById('complaint');
        const fileInput = document.getElementById('complaintImages');
        const form = document.getElementById('grievanceForm');

        if (complaintField) {
            complaintField.addEventListener('input', debouncedPredictDepartment);
        }
        if (fileInput) {
            fileInput.addEventListener('change', handleImageFileSelection);
        }
        if (form) {
            form.addEventListener('submit', submitGrievance);
        }

        setupVoiceInput();
        setupGeolocation();
        setupFileDropZone();
    }

    globalScope.CitizenGrievanceForm = {
        initialize,
        removeImage,
        refreshPrediction: predictDepartmentFromComplaint,
    };
})(window);
