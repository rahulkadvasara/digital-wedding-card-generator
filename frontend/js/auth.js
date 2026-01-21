/**
 * Authentication functionality for Digital Audio Wedding Cards
 * 
 * This module handles all user authentication operations including:
 * - User login and registration
 * - Token management and validation
 * - Session persistence using localStorage
 * - Authentication state management
 * - Automatic redirection for protected pages
 * 
 * The AuthService class provides a clean API for authentication operations
 * and integrates with the backend FastAPI authentication endpoints.
 */

class AuthService {
    /**
     * Initialize the authentication service
     * 
     * Sets up the base URL for API calls and prepares the service
     * for handling authentication operations.
     */
    constructor() {
        // Base URL for all authentication API calls
        // In production, this should be configurable via environment variables
        this.baseUrl = 'http://localhost:8000';
    }

    async login(username, password) {
        try {
            const response = await fetch(`${this.baseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            // Store authentication data
            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('userId', data.user.id);
            localStorage.setItem('username', data.user.username);

            return { success: true, user: data.user, token: data.access_token };
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    async register(username, password) {
        try {
            const response = await fetch(`${this.baseUrl}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            // Store authentication data
            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('userId', data.user.id);
            localStorage.setItem('username', data.user.username);

            return { success: true, user: data.user, token: data.access_token };
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    }

    async logout() {
        try {
            const token = localStorage.getItem('authToken');
            if (token) {
                await fetch(`${this.baseUrl}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage regardless of API call success
            localStorage.removeItem('authToken');
            localStorage.removeItem('userId');
            localStorage.removeItem('username');
            window.location.href = 'index.html';
        }
    }

    async verifyToken() {
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                return { valid: false };
            }

            const response = await fetch(`${this.baseUrl}/auth/verify`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                // Token is invalid, clear storage
                this.clearAuthData();
                return { valid: false };
            }

            const data = await response.json();
            return { valid: true, user: data.user };
        } catch (error) {
            console.error('Token verification error:', error);
            this.clearAuthData();
            return { valid: false };
        }
    }

    clearAuthData() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userId');
        localStorage.removeItem('username');
    }

    isAuthenticated() {
        return localStorage.getItem('authToken') !== null;
    }

    getCurrentUser() {
        return {
            id: localStorage.getItem('userId'),
            username: localStorage.getItem('username'),
            token: localStorage.getItem('authToken')
        };
    }
}

// Initialize auth service
const authService = new AuthService();

// DOM event listeners
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const logoutBtn = document.getElementById('logoutBtn');
    const registerLink = document.getElementById('registerLink');
    const loginLink = document.getElementById('loginLink');

    // Show/hide error messages
    function showError(message) {
        let errorDiv = document.getElementById('errorMessage');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'errorMessage';
            errorDiv.style.cssText = 'color: #e74c3c; background: #fadbd8; padding: 10px; border-radius: 4px; margin: 10px 0; text-align: center;';
            const form = document.querySelector('.login-form') || document.querySelector('.register-form');
            form.insertBefore(errorDiv, form.firstChild);
        }
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    function hideError() {
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    function showSuccess(message) {
        let successDiv = document.getElementById('successMessage');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.id = 'successMessage';
            successDiv.style.cssText = 'color: #27ae60; background: #d5f4e6; padding: 10px; border-radius: 4px; margin: 10px 0; text-align: center;';
            const form = document.querySelector('.login-form') || document.querySelector('.register-form');
            form.insertBefore(successDiv, form.firstChild);
        }
        successDiv.textContent = message;
        successDiv.style.display = 'block';
    }

    // Login form handler
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            hideError();
            
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            
            // Enhanced validation using Utils
            const usernameValidation = Utils.validateUsername(username);
            const passwordValidation = Utils.validatePassword(password);
            
            if (!usernameValidation.isValid) {
                showError(usernameValidation.errors[0]);
                return;
            }
            
            if (!passwordValidation.isValid) {
                showError(passwordValidation.errors[0]);
                return;
            }
            
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Logging in...';
            submitBtn.disabled = true;
            
            try {
                const result = await authService.login(username, password);
                if (result.success) {
                    showSuccess('Login successful! Redirecting...');
                    setTimeout(() => {
                        window.location.href = 'dashboard.html';
                    }, 1000);
                }
            } catch (error) {
                showError(error.message || 'Login failed. Please try again.');
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // Registration form handler
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            hideError();
            
            const username = document.getElementById('regUsername').value.trim();
            const password = document.getElementById('regPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            // Enhanced validation using Utils
            const usernameValidation = Utils.validateUsername(username);
            const passwordValidation = Utils.validatePassword(password);
            
            if (!usernameValidation.isValid) {
                showError(usernameValidation.errors[0]);
                return;
            }
            
            if (!passwordValidation.isValid) {
                showError(passwordValidation.errors[0]);
                return;
            }
            
            if (!confirmPassword) {
                showError('Please confirm your password');
                return;
            }
            
            if (password !== confirmPassword) {
                showError('Passwords do not match');
                return;
            }
            
            const submitBtn = registerForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Creating account...';
            submitBtn.disabled = true;
            
            try {
                const result = await authService.register(username, password);
                if (result.success) {
                    showSuccess('Registration successful! Redirecting...');
                    setTimeout(() => {
                        window.location.href = 'dashboard.html';
                    }, 1000);
                }
            } catch (error) {
                showError(error.message || 'Registration failed. Please try again.');
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // Toggle between login and registration forms
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = 'register.html';
        });
    }

    if (loginLink) {
        loginLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = 'index.html';
        });
    }

    // Logout button handler
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            authService.logout();
        });
    }

    // Add offline handler
    Utils.addOfflineHandler();

    // Check authentication on protected pages
    const protectedPages = ['dashboard.html', 'create-card.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (protectedPages.includes(currentPage)) {
        authService.verifyToken().then(result => {
            if (!result.valid) {
                window.location.href = 'index.html';
            }
        });
    }
});