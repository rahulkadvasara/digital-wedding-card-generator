// Dashboard functionality for Digital Audio Wedding Cards
class DashboardService {
    constructor() {
        this.baseUrl = 'http://localhost:8000';
        this.currentUser = null;
        this.userCards = [];
    }

    async init() {
        // Verify authentication
        const authResult = await authService.verifyToken();
        if (!authResult.valid) {
            window.location.href = 'index.html';
            return;
        }

        this.currentUser = authService.getCurrentUser();
        await this.loadUserCards();
        this.setupEventListeners();
        this.updateUserInfo();
        this.updateDashboardSummary();
        this.setActiveNavigation();
    }

    async loadUserCards() {
        try {
            const response = await Utils.makeRequest(`${this.baseUrl}/cards/my-cards`);
            this.userCards = response;
            this.renderCards();
        } catch (error) {
            console.error('Failed to load user cards:', error);
            this.showError('Failed to load your cards. Please try again.');
        }
    }

    renderCards() {
        const cardsList = document.getElementById('cardsList');
        
        if (!this.userCards || this.userCards.length === 0) {
            cardsList.innerHTML = `
                <div class="no-cards">
                    <h3>No Cards Created Yet</h3>
                    <p>You haven't created any wedding cards yet. Start by creating your first card!</p>
                    <a href="create-card.html" class="btn btn-primary">Create Your First Card</a>
                </div>
            `;
            return;
        }

        cardsList.innerHTML = this.userCards.map(card => `
            <div class="card-item" data-card-id="${card.id}">
                <div class="card-header">
                    <h3>Wedding Card</h3>
                    <small>Created: ${this.formatDate(card.created_at)}</small>
                </div>
                <div class="card-content">
                    <p class="card-message">${this.truncateMessage(card.message)}</p>
                    <div class="card-stats">
                        <span class="stat-item">
                            <span class="stat-label">Views:</span>
                            <span class="stat-value">${card.views || 0}</span>
                        </span>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-secondary" onclick="dashboardService.viewCard('${card.id}')">
                        View Card
                    </button>
                    <button class="btn btn-info" onclick="dashboardService.showQRCode('${card.id}')">
                        Show QR Code
                    </button>
                    <button class="btn btn-primary" onclick="dashboardService.viewAnalytics('${card.id}')">
                        Analytics
                    </button>
                    <button class="btn btn-warning" onclick="dashboardService.editCard('${card.id}')">
                        Edit
                    </button>
                    <button class="btn btn-danger" onclick="dashboardService.deleteCard('${card.id}')">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    setupEventListeners() {
        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }

        // Navigation links
        const navLinks = document.querySelectorAll('nav a:not(#logoutBtn)');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                // Add active state management if needed
                this.setActiveNavLink(link);
            });
        });

        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadUserCards();
            });
        }
    }

    updateUserInfo() {
        // Update user info in header if element exists
        const userInfo = document.getElementById('userInfo');
        if (userInfo && this.currentUser) {
            userInfo.textContent = `Welcome, ${this.currentUser.username}!`;
        }

        // Update page title
        document.title = `Dashboard - ${this.currentUser.username} - Digital Audio Wedding Cards`;
    }

    setActiveNavLink(activeLink) {
        // Remove active class from all nav links
        document.querySelectorAll('nav a').forEach(link => {
            link.classList.remove('active');
        });
        
        // Add active class to clicked link
        activeLink.classList.add('active');
    }

    async viewCard(cardId) {
        // Open card in new tab for viewing
        window.open(`view-card.html?id=${cardId}`, '_blank');
    }

    async showQRCode(cardId) {
        try {
            const card = this.userCards.find(c => c.id === cardId);
            if (!card) {
                this.showError('Card not found');
                return;
            }

            // Create modal to show QR code
            const modal = this.createModal('QR Code', `
                <div class="qr-code-container">
                    <p>Share this QR code with your friends to let them view your wedding card:</p>
                    <div class="qr-code-display">
                        <img src="${this.baseUrl}/cards/${cardId}/qr-code" alt="QR Code for Card ${cardId}" />
                    </div>
                    <p class="qr-instructions">
                        Friends can scan this code with their phone camera to view your personalized wedding invitation.
                    </p>
                    <div class="qr-actions">
                        <button class="btn btn-primary" onclick="dashboardService.downloadQRCode('${cardId}')">
                            Download QR Code
                        </button>
                        <button class="btn btn-secondary" onclick="dashboardService.copyCardLink('${cardId}')">
                            Copy Link
                        </button>
                    </div>
                </div>
            `);

            document.body.appendChild(modal);
        } catch (error) {
            console.error('Failed to show QR code:', error);
            this.showError('Failed to load QR code');
        }
    }

    async downloadQRCode(cardId) {
        try {
            const link = document.createElement('a');
            link.href = `${this.baseUrl}/cards/${cardId}/qr-code`;
            link.download = `wedding-card-${cardId}-qr.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            this.showSuccess('QR code downloaded successfully!');
        } catch (error) {
            console.error('Failed to download QR code:', error);
            this.showError('Failed to download QR code');
        }
    }

    async copyCardLink(cardId) {
        try {
            const cardUrl = `${window.location.origin}/view-card.html?id=${cardId}`;
            await navigator.clipboard.writeText(cardUrl);
            this.showSuccess('Card link copied to clipboard!');
        } catch (error) {
            console.error('Failed to copy link:', error);
            this.showError('Failed to copy link to clipboard');
        }
    }

    async viewAnalytics(cardId) {
        // Navigate to analytics page with card filter
        window.location.href = `analytics.html?card=${cardId}`;
    }

    async editCard(cardId) {
        const card = this.userCards.find(c => c.id === cardId);
        if (!card) {
            this.showError('Card not found');
            return;
        }

        // Create modal for editing card message
        const modal = this.createModal('Edit Wedding Card', `
            <form id="editCardForm" class="edit-card-form">
                <div class="form-group">
                    <label for="editMessage">Wedding Message:</label>
                    <textarea id="editMessage" rows="6" placeholder="Enter your personalized wedding message..." required>${card.message}</textarea>
                    <small class="help-text">Use {name} in your message to personalize it for each recipient</small>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Update Card</button>
                </div>
            </form>
        `);

        document.body.appendChild(modal);

        // Handle form submission
        const editForm = modal.querySelector('#editCardForm');
        editForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const newMessage = modal.querySelector('#editMessage').value.trim();
            
            if (!newMessage) {
                this.showError('Please enter a message');
                return;
            }

            try {
                // For now, we'll simulate the update
                // In a full implementation, this would call the backend API
                this.showInfo('Card editing feature is coming soon! The backend API needs to be implemented.');
                modal.remove();
                
                // Future implementation:
                // await Utils.makeRequest(`${this.baseUrl}/cards/${cardId}`, {
                //     method: 'PUT',
                //     body: JSON.stringify({ message: newMessage })
                // });
                // await this.loadUserCards();
                // this.showSuccess('Card updated successfully');
            } catch (error) {
                console.error('Failed to update card:', error);
                this.showError('Failed to update card');
            }
        });
    }

    async deleteCard(cardId) {
        const card = this.userCards.find(c => c.id === cardId);
        if (!card) {
            this.showError('Card not found');
            return;
        }

        // Create confirmation modal
        const modal = this.createModal('Delete Wedding Card', `
            <div class="delete-confirmation">
                <div class="warning-icon">⚠️</div>
                <h3>Are you sure you want to delete this card?</h3>
                <p>This action cannot be undone. The card and all its analytics data will be permanently removed.</p>
                <div class="card-preview">
                    <strong>Card Message:</strong>
                    <div class="message-preview">${this.truncateMessage(card.message, 150)}</div>
                    <small>Views: ${card.views || 0}</small>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                    <button type="button" class="btn btn-danger" onclick="dashboardService.confirmDeleteCard('${cardId}', this.closest('.modal-overlay'))">Delete Card</button>
                </div>
            </div>
        `);

        document.body.appendChild(modal);
    }

    async confirmDeleteCard(cardId, modal) {
        try {
            // For now, we'll simulate the deletion
            // In a full implementation, this would call the backend API
            this.showInfo('Card deletion feature is coming soon! The backend API needs to be implemented.');
            modal.remove();
            
            // Future implementation:
            // await Utils.makeRequest(`${this.baseUrl}/cards/${cardId}`, { method: 'DELETE' });
            // this.userCards = this.userCards.filter(card => card.id !== cardId);
            // this.renderCards();
            // this.updateDashboardSummary();
            // this.showSuccess('Card deleted successfully');
        } catch (error) {
            console.error('Failed to delete card:', error);
            this.showError('Failed to delete card');
        }
    }

    createModal(title, content) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${title}</h2>
                    <button class="close-btn" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
            </div>
        `;

        // Close modal when clicking overlay
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        return modal;
    }

    async logout() {
        const confirmed = confirm('Are you sure you want to logout?');
        if (confirmed) {
            await authService.logout();
        }
    }

    // Utility methods
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    truncateMessage(message, maxLength = 100) {
        if (message.length <= maxLength) {
            return message;
        }
        return message.substring(0, maxLength) + '...';
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    updateDashboardSummary() {
        // Calculate summary statistics
        const totalCards = this.userCards.length;
        const totalViews = this.userCards.reduce((sum, card) => sum + (card.views || 0), 0);
        
        // For unique viewers, we'd need analytics data, so for now we'll estimate
        const uniqueViewers = Math.floor(totalViews * 0.8); // Rough estimate
        
        // Update summary cards
        const totalCardsElement = document.getElementById('totalCards');
        const totalViewsElement = document.getElementById('totalViews');
        const uniqueViewersElement = document.getElementById('uniqueViewers');
        
        if (totalCardsElement) totalCardsElement.textContent = totalCards;
        if (totalViewsElement) totalViewsElement.textContent = totalViews;
        if (uniqueViewersElement) uniqueViewersElement.textContent = uniqueViewers;
    }

    setActiveNavigation() {
        // Set the dashboard link as active
        const dashboardLink = document.querySelector('a[href="dashboard.html"]');
        if (dashboardLink) {
            dashboardLink.classList.add('active');
        }
    }

    showNotification(message, type = 'info') {
        // Get or create notification container
        let container = document.getElementById('notificationContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">&times;</button>
        `;

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard service
const dashboardService = new DashboardService();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    dashboardService.init();
});