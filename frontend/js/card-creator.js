// Card creation functionality
class CardCreator {
    constructor() {
        this.baseUrl = 'http://localhost:8000';
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recordedBlob = null;
        this.isRecording = false;
        this.recordingStartTime = null;
        this.recordingTimer = null;
    }

    async initializeAudio() {
        try {
            // Check if getUserMedia is supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Audio recording is not supported in this browser');
            }

            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                } 
            });
            
            // Check if MediaRecorder is supported
            if (!window.MediaRecorder) {
                throw new Error('Audio recording is not supported in this browser');
            }

            // Check supported MIME types
            let mimeType = 'audio/webm;codecs=opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/mp4';
                    if (!MediaRecorder.isTypeSupported(mimeType)) {
                        mimeType = ''; // Let browser choose
                    }
                }
            }
            
            this.mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.recordedBlob = new Blob(this.audioChunks, { type: mimeType || 'audio/webm' });
                this.displayAudioPreview();
                this.validateForm();
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('MediaRecorder error:', event.error);
                this.showError('voiceError', 'Recording error occurred. Please try again.');
            };
            
            return true;
        } catch (error) {
            console.error('Error accessing microphone:', error);
            
            let errorMessage = 'Unable to access microphone. ';
            if (error.name === 'NotAllowedError') {
                errorMessage += 'Please allow microphone access and try again.';
            } else if (error.name === 'NotFoundError') {
                errorMessage += 'No microphone found. Please connect a microphone and try again.';
            } else if (error.name === 'NotSupportedError') {
                errorMessage += 'Audio recording is not supported in this browser.';
            } else if (error.name === 'NotReadableError') {
                errorMessage += 'Microphone is being used by another application.';
            } else {
                errorMessage += error.message || 'Please check your permissions and try again.';
            }
            
            this.showError('voiceError', errorMessage);
            return false;
        }
    }

    async startRecording() {
        if (!this.mediaRecorder) {
            const initialized = await this.initializeAudio();
            if (!initialized) return;
        }

        try {
            this.audioChunks = [];
            this.recordedBlob = null;
            this.isRecording = true;
            this.recordingStartTime = Date.now();
            
            this.mediaRecorder.start();
            this.updateRecordingUI(true);
            this.startRecordingTimer();
            
            // Auto-stop after 30 seconds
            setTimeout(() => {
                if (this.isRecording) {
                    this.stopRecording();
                }
            }, 30000);
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.showError('voiceError', 'Failed to start recording. Please try again.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateRecordingUI(false);
            this.stopRecordingTimer();
            
            // Stop all audio tracks
            if (this.mediaRecorder.stream) {
                this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        }
    }

    startRecordingTimer() {
        const statusElement = document.getElementById('recordingStatus');
        this.recordingTimer = setInterval(() => {
            if (this.recordingStartTime) {
                const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
                statusElement.textContent = `Recording... ${elapsed}s`;
                statusElement.className = 'recording-status active';
            }
        }, 1000);
    }

    stopRecordingTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
        
        const statusElement = document.getElementById('recordingStatus');
        statusElement.textContent = 'Recording complete';
        statusElement.className = 'recording-status';
    }

    updateRecordingUI(isRecording) {
        const recordBtn = document.getElementById('recordBtn');
        const recordText = recordBtn.querySelector('.record-text');
        const recordIcon = recordBtn.querySelector('.record-icon');
        
        if (isRecording) {
            recordBtn.classList.add('recording');
            recordText.textContent = 'Stop Recording';
            recordIcon.textContent = '⏹️';
        } else {
            recordBtn.classList.remove('recording');
            recordText.textContent = 'Start Recording';
            recordIcon.textContent = '🎤';
        }
    }

    displayAudioPreview() {
        const audioPreview = document.getElementById('audioPreview');
        if (this.recordedBlob) {
            const audioUrl = URL.createObjectURL(this.recordedBlob);
            audioPreview.src = audioUrl;
            audioPreview.style.display = 'block';
            
            // Clear any previous voice errors
            this.hideError('voiceError');
        }
    }

    validateForm() {
        const message = document.getElementById('message').value.trim();
        const submitBtn = document.getElementById('submitBtn');
        
        const isMessageValid = this.validateMessage(message);
        const isVoiceValid = this.recordedBlob !== null;
        
        submitBtn.disabled = !(isMessageValid && isVoiceValid);
        
        return isMessageValid && isVoiceValid;
    }

    validateMessage(message) {
        const validation = Utils.validateMessage(message);
        
        if (!validation.isValid) {
            this.showError('messageError', validation.errors[0]);
            return false;
        }
        
        this.hideError('messageError');
        return true;
    }

    showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }

    hideError(elementId) {
        const errorElement = document.getElementById(elementId);
        errorElement.classList.remove('show');
    }

    showPersistentError(message) {
        // Remove any existing persistent error
        const existingError = document.getElementById('persistentError');
        if (existingError) {
            existingError.remove();
        }

        // Create a persistent error message that stays until manually dismissed
        const errorDiv = document.createElement('div');
        errorDiv.id = 'persistentError';
        errorDiv.className = 'persistent-error';
        errorDiv.innerHTML = `
            <div class="persistent-error-content">
                <span class="error-icon">❌</span>
                <span class="error-message">${message}</span>
                <button class="error-close" onclick="document.getElementById('persistentError').remove()">×</button>
            </div>
        `;

        // Add styles for the persistent error
        const style = document.createElement('style');
        style.textContent = `
            .persistent-error {
                position: fixed;
                top: 80px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 10001;
                max-width: 600px;
                width: 90%;
                background: #fee;
                border: 2px solid #f00;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(255, 0, 0, 0.3);
                animation: slideDown 0.3s ease-out;
            }
            
            .persistent-error-content {
                display: flex;
                align-items: center;
                padding: 16px 20px;
                gap: 12px;
            }
            
            .persistent-error .error-icon {
                font-size: 20px;
                flex-shrink: 0;
            }
            
            .persistent-error .error-message {
                flex: 1;
                font-size: 16px;
                font-weight: 500;
                color: #c33;
                line-height: 1.4;
            }
            
            .persistent-error .error-close {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #c33;
                border-radius: 50%;
                flex-shrink: 0;
            }
            
            .persistent-error .error-close:hover {
                background: rgba(204, 51, 51, 0.1);
            }
            
            @keyframes slideDown {
                from {
                    transform: translateX(-50%) translateY(-100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(-50%) translateY(0);
                    opacity: 1;
                }
            }
        `;
        
        // Add styles to head if not already added
        if (!document.getElementById('persistent-error-styles')) {
            style.id = 'persistent-error-styles';
            document.head.appendChild(style);
        }

        // Add error to page
        document.body.appendChild(errorDiv);
    }

    showLoadingOverlay() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    hideLoadingOverlay() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    async createCard(message, voiceBlob) {
        try {
            this.showLoadingOverlay();
            
            // Validate inputs before sending
            const messageValidation = Utils.validateMessage(message);
            if (!messageValidation.isValid) {
                throw new Error(messageValidation.errors[0]);
            }

            if (!voiceBlob) {
                throw new Error('Voice recording is required');
            }

            // Check file size (limit to 10MB)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (voiceBlob.size > maxSize) {
                throw new Error('Voice recording is too large. Please record a shorter message.');
            }

            // Check if online
            if (!Utils.isOnline()) {
                throw new Error('You are offline. Please check your internet connection and try again.');
            }
            
            // Create FormData for voice generation endpoint
            const formData = new FormData();
            formData.append('message', message);
            formData.append('recipient_name', 'Guest'); // Default recipient name
            formData.append('voice_sample', voiceBlob, 'voice_sample.webm');
            
            const token = localStorage.getItem('authToken');
            if (!token) {
                throw new Error('Authentication required. Please log in again.');
            }
            
            // Use voice generation endpoint instead of card creation
            const result = await Utils.makeFileUploadRequest(
                `${this.baseUrl}/voice/generate`,
                formData,
                (progress) => {
                    // Update progress indicator if available
                    const progressElement = document.getElementById('uploadProgress');
                    if (progressElement) {
                        progressElement.style.width = `${progress}%`;
                    }
                }
            );
            
            // After voice generation, create the card
            const cardData = {
                message: message
            };
            
            const cardResult = await Utils.makeRequest(`${this.baseUrl}/cards/create`, {
                method: 'POST',
                body: JSON.stringify(cardData)
            });
            
            this.hideLoadingOverlay();
            
            return {
                success: true,
                card: cardResult,
                voice: result
            };
            
        } catch (error) {
            this.hideLoadingOverlay();
            console.error('Card creation error:', error);
            
            // Only redirect for actual authentication errors, not voice generation errors
            if ((error.message.includes('Authentication') || error.message.includes('Session expired')) && 
                !error.message.includes('voice') && !error.message.includes('recording')) {
                // Redirect to login if authentication failed
                localStorage.removeItem('authToken');
                localStorage.removeItem('userId');
                localStorage.removeItem('username');
                window.location.href = 'index.html';
                return;
            }
            
            throw error;
        }
    }

    async displaySuccessModal(card) {
        const modal = document.getElementById('successModal');
        const previewMessage = document.getElementById('previewMessage');
        
        // Display the message
        previewMessage.textContent = card.message;
        
        modal.style.display = 'flex';
    }
}

// Initialize card creator
const cardCreator = new CardCreator();

// Global functions for modal actions

function goToDashboard() {
    window.location.href = 'dashboard.html';
}

// DOM event listeners
document.addEventListener('DOMContentLoaded', function() {
    const cardForm = document.getElementById('cardForm');
    const recordBtn = document.getElementById('recordBtn');
    const messageInput = document.getElementById('message');
    const logoutBtn = document.getElementById('logoutBtn');

    // Check authentication
    const token = localStorage.getItem('authToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    // Message input validation
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            cardCreator.validateForm();
        });

        messageInput.addEventListener('blur', function() {
            cardCreator.validateMessage(this.value.trim());
        });
    }

    // Recording button
    if (recordBtn) {
        recordBtn.addEventListener('click', function() {
            if (!cardCreator.isRecording) {
                cardCreator.startRecording();
            } else {
                cardCreator.stopRecording();
            }
        });
    }

    // Form submission
    if (cardForm) {
        cardForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Form submission started - preventDefault called');
            
            const message = document.getElementById('message').value.trim();
            
            // Final validation
            if (!cardCreator.validateForm()) {
                console.log('Form validation failed, returning early');
                return;
            }
            
            console.log('Form validation passed, proceeding with card creation');
            
            try {
                const submitBtn = document.getElementById('submitBtn');
                const submitText = submitBtn.querySelector('.submit-text');
                const loadingSpinner = submitBtn.querySelector('.loading-spinner');
                
                // Update button state
                submitBtn.disabled = true;
                submitText.style.display = 'none';
                loadingSpinner.style.display = 'inline-block';
                
                const result = await cardCreator.createCard(message, cardCreator.recordedBlob);
                
                if (result.success) {
                    await cardCreator.displaySuccessModal(result.card);
                }
                
            } catch (error) {
                console.error('Card creation error:', error);
                
                // Show user-friendly error message
                let errorMessage = 'Failed to create card. Please try again.';
                if (error.message.includes('Authentication')) {
                    errorMessage = 'Session expired. Please log in again.';
                } else if (error.message.includes('network') || error.message.includes('fetch')) {
                    errorMessage = 'Network error. Please check your connection and try again.';
                } else if (error.message) {
                    errorMessage = error.message;
                }
                
                // Show blocking error message that user must acknowledge
                alert('❌ Card Creation Failed\n\n' + errorMessage + '\n\nPlease click OK to continue.');
                
                // Also show persistent error banner after alert is dismissed
                cardCreator.showPersistentError(errorMessage);
                
                // Show notification as well
                Utils.showError(errorMessage, 10000);
                
                // Log error for debugging
                console.error('Card creation failed:', errorMessage);
                
                // Reset button state
                const submitBtn = document.getElementById('submitBtn');
                const submitText = submitBtn.querySelector('.submit-text');
                const loadingSpinner = submitBtn.querySelector('.loading-spinner');
                
                submitBtn.disabled = false;
                submitText.style.display = 'inline-block';
                loadingSpinner.style.display = 'none';
            }
        });
    }

    // Logout functionality
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('authToken');
            window.location.href = 'index.html';
        });
    }

    // Close modal when clicking outside
    document.addEventListener('click', function(e) {
        const modal = document.getElementById('successModal');
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Add offline handler
    Utils.addOfflineHandler();

    // Initial form validation
    cardCreator.validateForm();
});