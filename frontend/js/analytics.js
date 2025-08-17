// Analytics functionality
class Analytics {
    constructor() {
        this.baseUrl = 'http://localhost:8000';
    }

    async loadUserAnalytics() {
        try {
            // Check if online
            if (!Utils.isOnline()) {
                throw new Error('You are offline. Please check your internet connection and try again.');
            }

            // Get current user from localStorage (more reliable than sessionStorage)
            const userId = localStorage.getItem('userId');
            
            if (!userId) {
                throw new Error('User not logged in');
            }

            const response = await Utils.makeRequest(`${this.baseUrl}/analytics/user/${userId}`);
            return response;
            
        } catch (error) {
            console.error('Error loading user analytics:', error);
            throw error;
        }
    }

    async loadCardAnalytics(cardId) {
        try {
            // Check if online
            if (!Utils.isOnline()) {
                throw new Error('You are offline. Please check your internet connection and try again.');
            }

            // Validate card ID
            if (!cardId || !/^[a-zA-Z0-9_-]+$/.test(cardId)) {
                throw new Error('Invalid card ID');
            }

            const response = await Utils.makeRequest(`${this.baseUrl}/analytics/${cardId}`);
            return response;
            
        } catch (error) {
            console.error('Error loading card analytics:', error);
            throw error;
        }
    }

    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } catch (error) {
            return dateString;
        }
    }

    renderAnalytics(analyticsData) {
        const container = document.getElementById('analyticsData');
        container.innerHTML = '';

        if (!analyticsData || analyticsData.length === 0) {
            container.innerHTML = `
                <div class="no-data">
                    <h3>No Cards Found</h3>
                    <p>You haven't created any wedding cards yet.</p>
                    <a href="create-card.html" class="btn btn-primary">Create Your First Card</a>
                </div>
            `;
            return;
        }

        // Add summary statistics
        const totalViews = analyticsData.reduce((sum, card) => sum + card.total_views, 0);
        const totalCards = analyticsData.length;
        const totalUniqueViewers = new Set(
            analyticsData.flatMap(card => card.viewer_names)
        ).size;

        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'analytics-summary';
        summaryDiv.innerHTML = `
            <h2>Analytics Overview</h2>
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-number">${totalCards}</div>
                    <div class="stat-label">Total Cards</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${totalViews}</div>
                    <div class="stat-label">Total Views</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${totalUniqueViewers}</div>
                    <div class="stat-label">Unique Viewers</div>
                </div>
            </div>
        `;
        container.appendChild(summaryDiv);

        // Add individual card analytics
        const cardsDiv = document.createElement('div');
        cardsDiv.className = 'cards-analytics';
        cardsDiv.innerHTML = '<h2>Individual Card Statistics</h2>';

        analyticsData.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'analytics-card';
            
            // Truncate message for display
            const displayMessage = card.message.length > 80 
                ? card.message.substring(0, 80) + '...' 
                : card.message;
            
            cardDiv.innerHTML = `
                <div class="card-header">
                    <h3>Card: ${displayMessage}</h3>
                    <small>Created: ${this.formatDate(card.created_at)}</small>
                </div>
                <div class="card-stats">
                    <div class="stat-item">
                        <span class="stat-label">Total Views:</span>
                        <span class="stat-value">${card.total_views}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Unique Viewers:</span>
                        <span class="stat-value">${card.unique_viewers}</span>
                    </div>
                </div>
                <div class="viewer-section">
                    <h4>Viewers (${card.viewer_names.length}):</h4>
                    <div class="viewer-list">
                        ${card.viewer_names.length > 0 
                            ? card.viewer_names.map(viewer => `
                                <div class="viewer-item">${viewer}</div>
                            `).join('')
                            : '<div class="no-viewers">No views yet</div>'
                        }
                    </div>
                </div>
                ${card.recent_views.length > 0 ? `
                    <div class="recent-views">
                        <h4>Recent Views:</h4>
                        <div class="recent-views-list">
                            ${card.recent_views.map(view => `
                                <div class="recent-view-item">
                                    <span class="viewer-name">${view.viewer_name}</span>
                                    <span class="view-time">${this.formatDate(view.viewed_at)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                <div class="card-actions">
                    <button class="btn btn-secondary" onclick="analytics.viewCardDetails('${card.card_id}')">
                        View Details
                    </button>
                </div>
            `;
            
            cardsDiv.appendChild(cardDiv);
        });

        container.appendChild(cardsDiv);
    }

    async viewCardDetails(cardId) {
        try {
            const cardAnalytics = await this.loadCardAnalytics(cardId);
            this.showCardDetailsModal(cardAnalytics);
        } catch (error) {
            alert('Failed to load card details: ' + error.message);
        }
    }

    showCardDetailsModal(cardAnalytics) {
        // Create modal overlay
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Detailed Analytics</h2>
                    <button class="close-btn" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="detail-stats">
                        <div class="stat-item">
                            <span>Card ID:</span>
                            <span>${cardAnalytics.card_id}</span>
                        </div>
                        <div class="stat-item">
                            <span>Total Views:</span>
                            <span>${cardAnalytics.total_views}</span>
                        </div>
                        <div class="stat-item">
                            <span>Unique Viewers:</span>
                            <span>${cardAnalytics.unique_viewers}</span>
                        </div>
                    </div>
                    <div class="all-views">
                        <h3>All Views (${cardAnalytics.recent_views.length}):</h3>
                        <div class="views-list">
                            ${cardAnalytics.recent_views.map(view => `
                                <div class="view-item">
                                    <span class="viewer-name">${view.viewer_name}</span>
                                    <span class="view-time">${this.formatDate(view.viewed_at)}</span>
                                    ${view.ip_address ? `<span class="ip-address">${view.ip_address}</span>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    showError(message) {
        const container = document.getElementById('analyticsData');
        container.innerHTML = `
            <div class="error-message">
                <h3>Error Loading Analytics</h3>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="location.reload()">Retry</button>
            </div>
        `;
    }

    showLoading() {
        const container = document.getElementById('analyticsData');
        container.innerHTML = `
            <div class="loading-message">
                <h3>Loading Analytics...</h3>
                <p>Please wait while we fetch your card statistics.</p>
            </div>
        `;
    }
}

// Initialize analytics
const analytics = new Analytics();

// DOM event listeners
document.addEventListener('DOMContentLoaded', async function() {
    // Check if user is logged in using localStorage for consistency
    const userId = localStorage.getItem('userId');
    
    if (!userId) {
        window.location.href = 'index.html';
        return;
    }

    // Add offline handler
    Utils.addOfflineHandler();

    // Show loading state
    analytics.showLoading();

    try {
        const analyticsData = await analytics.loadUserAnalytics();
        analytics.renderAnalytics(analyticsData);
    } catch (error) {
        console.error('Error loading analytics:', error);
        analytics.showError(error.message || 'Failed to load analytics data');
    }

    // Logout functionality
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('authToken');
            localStorage.removeItem('userId');
            localStorage.removeItem('username');
            window.location.href = 'index.html';
        });
    }
});