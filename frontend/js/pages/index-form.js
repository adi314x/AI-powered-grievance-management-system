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
        leafletMap: null,
        leafletMarker: null,
        mapVisible: false,
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
            updateImageRequirementUI(false, null);
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
            updateImageRequirementUI(false, null);
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
            updateImageRequirementUI(false, null);

            if (typeof state.onSubmitted === 'function') {
                state.onSubmitted(response);
            }
        } catch (error) {
            notify(error.message || 'Failed to submit grievance', 'error');
        }
    }

    // ----------------------------------------------------------------
    // Map helpers
    // ----------------------------------------------------------------

    /**
     * Reverse-geocode lat/lng using OpenStreetMap Nominatim (no API key needed).
     * Returns a human-readable address string, or falls back to "Lat: X, Long: Y".
     */
    async function reverseGeocode(lat, lon) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`,
                { headers: { 'Accept-Language': 'en' } }
            );
            if (!response.ok) throw new Error('Nominatim error');
            const data = await response.json();
            return data.display_name || `Lat: ${lat}, Long: ${lon}`;
        } catch (_) {
            return `Lat: ${lat}, Long: ${lon}`;
        }
    }

    /**
     * Place or move the draggable Leaflet marker to (lat, lon) and fill the
     * location text field with a reverse-geocoded address.
     */
    async function placeMarker(lat, lon) {
        const locationField = document.getElementById('location');

        // Ensure map dimensions are correct before panning
        if (state.leafletMap) state.leafletMap.invalidateSize();

        if (state.leafletMarker) {
            state.leafletMarker.setLatLng([lat, lon]);
        } else {
            state.leafletMarker = window.L.marker([lat, lon], { draggable: true })
                .addTo(state.leafletMap);

            state.leafletMarker.on('dragend', async () => {
                const pos = state.leafletMarker.getLatLng();
                const address = await reverseGeocode(pos.lat.toFixed(6), pos.lng.toFixed(6));
                if (locationField) locationField.value = address;
            });
        }

        state.leafletMap.setView([lat, lon], 16);

        if (locationField) {
            locationField.value = 'Fetching address…';
        }
        const address = await reverseGeocode(lat.toFixed(6), lon.toFixed(6));
        if (locationField) locationField.value = address;
    }

    /**
     * Initialise the Leaflet map inside #locationMap (called once, lazily).
     */
    function initLeafletMap() {
        if (state.leafletMap) return; // already initialised

        // Default centre: Pune, Maharashtra
        const defaultLat = 18.5204;
        const defaultLon = 73.8567;
        const defaultZoom = 13;

        state.leafletMap = window.L.map('locationMap', {
            center: [defaultLat, defaultLon],
            zoom: defaultZoom,
            attributionControl: true,
        });

        window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(state.leafletMap);

        // Click on map → drop/move pin + reverse-geocode
        state.leafletMap.on('click', async (e) => {
            await placeMarker(e.latlng.lat, e.latlng.lng);
        });

        // Leaflet needs a size refresh after the container becomes visible.
        // We call it twice: once immediately and once after the CSS slide-down
        // animation (200ms) finishes, so tile sizing is always correct.
        setTimeout(() => state.leafletMap.invalidateSize(), 50);
        setTimeout(() => state.leafletMap.invalidateSize(), 250);
    }

    function setupGeolocation() {
        const mapToggleBtn = document.getElementById('mapToggleBtn');
        if (!mapToggleBtn) return;

        mapToggleBtn.addEventListener('click', () => {
            toggleMap(!state.mapVisible);
        });
    }

    /**
     * Show or hide the map panel and initialise Leaflet on first open.
     */
    function toggleMap(show) {
        const wrapper = document.getElementById('locationMapWrapper');
        const mapToggleBtn = document.getElementById('mapToggleBtn');
        if (!wrapper) return;

        if (show && typeof window.L === 'undefined') {
            // Leaflet not yet loaded — load it dynamically then open the map
            if (mapToggleBtn) {
                mapToggleBtn.textContent = '⏳ Loading Map…';
                mapToggleBtn.disabled = true;
            }
            _loadLeafletDynamic(() => {
                if (mapToggleBtn) {
                    mapToggleBtn.disabled = false;
                }
                toggleMap(true); // retry now that L is available
            });
            return;
        }

        state.mapVisible = show;
        wrapper.style.display = show ? 'block' : 'none';

        if (mapToggleBtn) {
            mapToggleBtn.textContent = show ? '📍 Hide Map' : '📍 Pick on Map';
        }

        if (show) {
            initLeafletMap();
            setTimeout(() => {
                if (state.leafletMap) state.leafletMap.invalidateSize();
                autoLocate(mapToggleBtn);
            }, 350);
        }
    }

    /**
     * Dynamically load Leaflet CSS + JS from CDN, then call callback.
     * Safe to call multiple times — skips if already in progress.
     */
    let _leafletLoading = false;
    let _leafletCallbacks = [];
    function _loadLeafletDynamic(callback) {
        _leafletCallbacks.push(callback);
        if (_leafletLoading) return; // already in flight
        _leafletLoading = true;

        // Inject CSS if not present
        if (!document.querySelector('link[href*="leaflet"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.css';
            document.head.appendChild(link);
        }

        // Inject JS
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.js';
        script.crossOrigin = '';
        script.onload = () => {
            _leafletLoading = false;
            _leafletCallbacks.forEach(cb => cb());
            _leafletCallbacks = [];
        };
        script.onerror = () => {
            _leafletLoading = false;
            _leafletCallbacks = [];
            notify('Failed to load map. Please check your internet connection.', 'error');
            const btn = document.getElementById('mapToggleBtn');
            if (btn) { btn.textContent = '📍 Pick on Map'; btn.disabled = false; }
        };
        document.body.appendChild(script);
    }


    /**
     * Request GPS, show a spinner on the button while waiting, then drop a pin.
     * Falls back silently to India centre if permission is denied or unavailable.
     */
    function autoLocate(btn) {
        if (!navigator.geolocation) {
            notify('Geolocation is not supported by your browser. Click on the map to pin a location.', 'info');
            return;
        }

        const originalText = btn ? btn.textContent : '📍 Hide Map';
        if (btn) {
            btn.textContent = '⏳ Getting your location…';
            btn.disabled = true;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                if (btn) {
                    btn.textContent = '📍 Hide Map';
                    btn.disabled = false;
                }
                await placeMarker(position.coords.latitude, position.coords.longitude);
            },
            (err) => {
                if (btn) {
                    btn.textContent = originalText;
                    btn.disabled = false;
                }
                // Tell the user why it failed so they can act
                if (err.code === err.PERMISSION_DENIED) {
                    notify('Location access denied. Please allow location in your browser, or click on the map to pin manually.', 'error');
                } else {
                    notify('Could not detect location. Click on the map to pin your location manually.', 'info');
                }
            },
            { timeout: 10000, maximumAge: 0, enableHighAccuracy: true }
        );
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
        updateImageRequirementUI(false, null);

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

        setupGeolocation();
        setupFileDropZone();
    }

    globalScope.CitizenGrievanceForm = {
        initialize,
        removeImage,
        refreshPrediction: predictDepartmentFromComplaint,
        toggleMap,
    };
})(window);
