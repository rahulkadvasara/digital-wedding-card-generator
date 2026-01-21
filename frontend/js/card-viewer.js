// Card viewing functionality
class CardViewer {
    constructor() {
        this.baseUrl = 'http://localhost:8000';
        this.cardId = this.getCardIdFromUrl();
        this.cardData = null;
    }

    getCardIdFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id');
    }

    async loadCard(cardId, recipientName = null) {
        try {
            if (!cardId) {
                throw new Error('No card ID provided');
            }

            // Validate card ID format (basic check)
            if (!/^[a-zA-Z0-9_-]+$/.test(cardId)) {
                throw new Error('Invalid card ID format');
            }

            // Validate recipient name if provided
            if (recipientName) {
                const nameValidation = Utils.validateRecipientName(recipientName);
                if (!nameValidation.isValid) {
                    throw new Error(nameValidation.errors[0]);
                }
            }

            // Check if online
            if (!Utils.isOnline()) {
                throw new Error('You are offline. Please check your internet connection and try again.');
            }

            // Build URL with recipient name if provided for personalized content
            let url = `${this.baseUrl}/cards/${cardId}`;
            if (recipientName) {
                url += `?recipient_name=${encodeURIComponent(recipientName)}`;
            }

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                let errorMessage;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message;
                } catch (parseError) {
                    errorMessage = response.statusText;
                }

                switch (response.status) {
                    case 404:
                        throw new Error('Wedding card not found. Please check the QR code and try again.');
                    case 400:
                        throw new Error(errorMessage || 'Invalid request. Please try scanning the QR code again.');
                    case 500:
                        throw new Error('Server error. Please try again in a few moments.');
                    default:
                        throw new Error(errorMessage || `Failed to load card: ${response.status}`);
                }
            }

            const cardData = await response.json();
            this.cardData = cardData;
            return cardData;
            
        } catch (error) {
            console.error('Error loading card:', error);
            throw error;
        }
    }

    personalizeMessage(message, name) {
        // Replace placeholder with actual name
        return message.replace(/\{name\}/g, name);
    }



    async playAudio(audioPath, recipientName = null) {
        try {
            const audioElement = document.getElementById('audioMessage');
            
            if (!audioElement) {
                console.warn('Audio element not found');
                return;
            }

            if (!audioPath) {
                console.warn('No audio path provided');
                return;
            }
            
            let audioUrl;
            
            // If we have a recipient name, use the personalized audio endpoint
            if (recipientName && this.cardId) {
                audioUrl = `${this.baseUrl}/cards/${this.cardId}/audio?recipient_name=${encodeURIComponent(recipientName)}`;
            } else {
                // Use direct file path for static audio
                audioUrl = `${this.baseUrl}/${audioPath}`;
            }
            
            // Add error handling for audio loading
            audioElement.addEventListener('error', (e) => {
                console.error('Audio loading error:', e);
                const audioSection = document.querySelector('.audio-section');
                const audioLabel = document.querySelector('.audio-label');
                
                if (audioLabel) {
                    audioLabel.innerHTML = '🎵 Voice Message: <em>Audio temporarily unavailable</em>';
                }
                
                // Add error note
                const errorNote = document.createElement('p');
                errorNote.className = 'audio-error-note';
                errorNote.innerHTML = '<em>There was an issue loading the voice message. Please try refreshing the page.</em>';
                errorNote.style.color = '#e74c3c';
                errorNote.style.fontStyle = 'italic';
                errorNote.style.marginTop = '10px';
                
                // Remove existing error note if any
                const existingErrorNote = audioSection.querySelector('.audio-error-note');
                if (existingErrorNote) {
                    existingErrorNote.remove();
                }
                
                audioSection.appendChild(errorNote);
            }, { once: true });

            // Add loading state
            audioElement.addEventListener('loadstart', () => {
                const audioLabel = document.querySelector('.audio-label');
                if (audioLabel) {
                    audioLabel.innerHTML = '🎵 Personal Voice Message: <em>Loading...</em>';
                }
            }, { once: true });

            // Add loaded state
            audioElement.addEventListener('canplay', () => {
                const audioLabel = document.querySelector('.audio-label');
                if (audioLabel) {
                    audioLabel.textContent = '🎵 Personal Voice Message:';
                }
            }, { once: true });
            
            audioElement.src = audioUrl;
            
            // Try to play audio automatically (may be blocked by browser)
            try {
                await audioElement.play();
            } catch (playError) {
                console.log('Auto-play blocked by browser. User needs to click play.');
                
                // Show a message encouraging user to click play
                const audioSection = document.querySelector('.audio-section');
                const playNote = document.createElement('p');
                playNote.className = 'play-note';
                playNote.innerHTML = '<em>Click the play button above to hear your personalized message!</em>';
                playNote.style.color = '#3498db';
                playNote.style.fontStyle = 'italic';
                playNote.style.marginTop = '5px';
                
                // Remove existing play note if any
                const existingPlayNote = audioSection.querySelector('.play-note');
                if (existingPlayNote) {
                    existingPlayNote.remove();
                }
                
                audioSection.appendChild(playNote);
            }
            
        } catch (error) {
            console.error('Error setting up audio:', error);
            Utils.showWarning('There was an issue setting up the audio playback. Please try refreshing the page.');
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <h2>Error</h2>
            <p>${message}</p>
            <p>Please check the QR code and try again.</p>
        `;
        
        const container = document.querySelector('.container main');
        container.innerHTML = '';
        container.appendChild(errorDiv);
    }
}

// Initialize card viewer
const cardViewer = new CardViewer();

// DOM event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Add offline handler
    Utils.addOfflineHandler();

    // Check if card ID is present in URL
    if (!cardViewer.cardId) {
        cardViewer.showError('Invalid card link. Please scan the QR code again.');
        return;
    }

    const nameForm = document.getElementById('nameForm');

    if (nameForm) {
        nameForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const recipientName = document.getElementById('recipientName').value.trim();
            
            // Enhanced validation using Utils
            const nameValidation = Utils.validateRecipientName(recipientName);
            if (!nameValidation.isValid) {
                Utils.showError(nameValidation.errors[0]);
                return;
            }
            
            try {
                // Show loading state
                const submitButton = nameForm.querySelector('button[type="submit"]');
                const originalText = submitButton.textContent;
                submitButton.textContent = 'Loading...';
                submitButton.disabled = true;
                
                // Load personalized card data
                const card = await cardViewer.loadCard(cardViewer.cardId, recipientName);
                const personalizedMessage = cardViewer.personalizeMessage(card.message, recipientName);
                
                // Update UI
                document.getElementById('personalizedMessage').innerHTML = personalizedMessage;
                document.getElementById('nameInput').style.display = 'none';
                document.getElementById('cardDisplay').style.display = 'block';
                
                // Set up and play audio if available
                const audioSection = document.querySelector('.audio-section');
                const audioElement = document.getElementById('audioMessage');
                const audioLabel = document.querySelector('.audio-label');
                
                if (card.ai_voice_path) {
                    // Audio is available
                    audioLabel.textContent = '🎵 Personal Voice Message:';
                    audioElement.style.display = 'block';
                    await cardViewer.playAudio(card.ai_voice_path, recipientName);
                } else {
                    // No audio available - show message instead of hiding
                    audioLabel.innerHTML = '🎵 Voice Message: <em>Audio message will be available soon!</em>';
                    audioElement.style.display = 'none';
                    
                    // Add a note about the audio
                    const audioNote = document.createElement('p');
                    audioNote.className = 'audio-note';
                    audioNote.innerHTML = '<em>The couple is preparing a personalized voice message for you. Please check back later!</em>';
                    audioNote.style.color = '#666';
                    audioNote.style.fontStyle = 'italic';
                    audioNote.style.marginTop = '10px';
                    
                    // Remove existing note if any
                    const existingNote = audioSection.querySelector('.audio-note');
                    if (existingNote) {
                        existingNote.remove();
                    }
                    
                    audioSection.appendChild(audioNote);
                }
                

                
            } catch (error) {
                console.error('Error loading card:', error);
                cardViewer.showError(error.message || 'Failed to load wedding card');
                
                // Reset button state
                const submitButton = nameForm.querySelector('button[type="submit"]');
                submitButton.textContent = originalText;
                submitButton.disabled = false;
            }
        });
    }
});