// Utility functions
class Utils {
    static formatDate(dateString) {
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return 'Invalid Date';
            }
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        } catch (error) {
            console.error('Date formatting error:', error);
            return 'Invalid Date';
        }
    }

    static generateId() {
        return Math.random().toString(36).substr(2, 9);
    }

    static showError(message, duration = 5000) {
        this.removeExistingNotifications();
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'notification error-notification';
        errorDiv.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">❌</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        this.addNotificationStyles();
        document.body.appendChild(errorDiv);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, duration);
    }

    static showSuccess(message, duration = 3000) {
        this.removeExistingNotifications();
        
        const successDiv = document.createElement('div');
        successDiv.className = 'notification success-notification';
        successDiv.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">✅</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        this.addNotificationStyles();
        document.body.appendChild(successDiv);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.remove();
            }
        }, duration);
    }

    static showWarning(message, duration = 4000) {
        this.removeExistingNotifications();
        
        const warningDiv = document.createElement('div');
        warningDiv.className = 'notification warning-notification';
        warningDiv.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">⚠️</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        this.addNotificationStyles();
        document.body.appendChild(warningDiv);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (warningDiv.parentNode) {
                warningDiv.remove();
            }
        }, duration);
    }

    static removeExistingNotifications() {
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
    }

    static addNotificationStyles() {
        if (document.getElementById('notification-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                animation: slideIn 0.3s ease-out;
            }
            
            .error-notification {
                background: #fee;
                border: 1px solid #fcc;
                color: #c33;
            }
            
            .success-notification {
                background: #efe;
                border: 1px solid #cfc;
                color: #3c3;
            }
            
            .warning-notification {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
            }
            
            .notification-content {
                display: flex;
                align-items: center;
                padding: 12px 16px;
                gap: 8px;
            }
            
            .notification-icon {
                font-size: 16px;
                flex-shrink: 0;
            }
            
            .notification-message {
                flex: 1;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .notification-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0.7;
                flex-shrink: 0;
            }
            
            .notification-close:hover {
                opacity: 1;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }

    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    static validatePassword(password) {
        const errors = [];
        
        if (!password) {
            errors.push('Password is required');
        } else {
            if (password.length < 6) {
                errors.push('Password must be at least 6 characters long');
            }
            if (password.length > 128) {
                errors.push('Password must be less than 128 characters');
            }
            if (!/[a-zA-Z]/.test(password)) {
                errors.push('Password must contain at least one letter');
            }
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    static validateUsername(username) {
        const errors = [];
        
        if (!username) {
            errors.push('Username is required');
        } else {
            if (username.length < 3) {
                errors.push('Username must be at least 3 characters long');
            }
            if (username.length > 50) {
                errors.push('Username must be less than 50 characters');
            }
            if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
                errors.push('Username can only contain letters, numbers, underscores, and hyphens');
            }
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    static validateMessage(message) {
        const errors = [];
        
        if (!message || !message.trim()) {
            errors.push('Message is required');
        } else {
            const trimmedMessage = message.trim();
            if (trimmedMessage.length < 10) {
                errors.push('Message must be at least 10 characters long');
            }
            if (trimmedMessage.length > 1000) {
                errors.push('Message must be less than 1000 characters');
            }
            // Check for potentially harmful content
            const suspiciousPatterns = [/<script/i, /javascript:/i, /on\w+=/i];
            if (suspiciousPatterns.some(pattern => pattern.test(trimmedMessage))) {
                errors.push('Message contains invalid content');
            }
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    static validateRecipientName(name) {
        const errors = [];
        
        if (!name || !name.trim()) {
            errors.push('Name is required');
        } else {
            const trimmedName = name.trim();
            if (trimmedName.length < 1) {
                errors.push('Name cannot be empty');
            }
            if (trimmedName.length > 100) {
                errors.push('Name must be less than 100 characters');
            }
            // Basic sanitization check
            if (/<[^>]*>/.test(trimmedName)) {
                errors.push('Name contains invalid characters');
            }
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    static async makeRequest(url, options = {}) {
        const token = localStorage.getItem('authToken');
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;
                
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                } catch (parseError) {
                    // If we can't parse the error response, use the status text
                    errorMessage = response.statusText || errorMessage;
                }
                
                // Handle specific HTTP status codes
                switch (response.status) {
                    case 401:
                        // Unauthorized - clear auth data and redirect
                        localStorage.removeItem('authToken');
                        localStorage.removeItem('userId');
                        localStorage.removeItem('username');
                        if (window.location.pathname !== '/index.html' && !window.location.pathname.endsWith('index.html')) {
                            window.location.href = 'index.html';
                        }
                        throw new Error('Session expired. Please log in again.');
                    case 403:
                        throw new Error('Access denied. You do not have permission to perform this action.');
                    case 404:
                        throw new Error('The requested resource was not found.');
                    case 429:
                        throw new Error('Too many requests. Please wait a moment and try again.');
                    case 500:
                        throw new Error('Server error. Please try again later.');
                    case 503:
                        throw new Error('Service temporarily unavailable. Please try again later.');
                    default:
                        throw new Error(errorMessage);
                }
            }
            
            return await response.json();
        } catch (error) {
            console.error('Request failed:', error);
            
            // Handle network errors
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error. Please check your internet connection and try again.');
            }
            
            throw error;
        }
    }

    static async makeFileUploadRequest(url, formData, onProgress = null) {
        const token = localStorage.getItem('authToken');
        
        try {
            const xhr = new XMLHttpRequest();
            
            return new Promise((resolve, reject) => {
                xhr.upload.addEventListener('progress', (event) => {
                    if (event.lengthComputable && onProgress) {
                        const percentComplete = (event.loaded / event.total) * 100;
                        onProgress(percentComplete);
                    }
                });
                
                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            resolve(response);
                        } catch (parseError) {
                            reject(new Error('Invalid response format'));
                        }
                    } else {
                        let errorMessage = `HTTP error! status: ${xhr.status}`;
                        try {
                            const errorData = JSON.parse(xhr.responseText);
                            errorMessage = errorData.detail || errorData.message || errorMessage;
                        } catch (parseError) {
                            errorMessage = xhr.statusText || errorMessage;
                        }
                        reject(new Error(errorMessage));
                    }
                });
                
                xhr.addEventListener('error', () => {
                    reject(new Error('Network error. Please check your connection and try again.'));
                });
                
                xhr.addEventListener('timeout', () => {
                    reject(new Error('Request timeout. Please try again.'));
                });
                
                xhr.open('POST', url);
                xhr.timeout = 60000; // 60 second timeout
                
                if (token) {
                    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                }
                
                xhr.send(formData);
            });
        } catch (error) {
            console.error('File upload failed:', error);
            throw error;
        }
    }

    static sanitizeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static isOnline() {
        return navigator.onLine;
    }

    static addOfflineHandler() {
        window.addEventListener('offline', () => {
            this.showWarning('You are currently offline. Some features may not work properly.');
        });
        
        window.addEventListener('online', () => {
            this.showSuccess('Connection restored.');
        });
    }
}

// Make Utils available globally
window.Utils = Utils;