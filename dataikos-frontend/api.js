// api.js - Client API autonome pour le frontend
const API_BASE_URL = 'https://website-pxkd.onrender.com';

class DataikosAPI {
    constructor() {
        this.token = localStorage.getItem('dataikos_token');
        this.refreshToken = localStorage.getItem('dataikos_refresh_token');
        this.user = JSON.parse(localStorage.getItem('dataikos_user') || 'null');
    }

    setAuth(token, refreshToken = null, user = null) {
        this.token = token;
        if (refreshToken) this.refreshToken = refreshToken;
        if (user) this.user = user;
        
        localStorage.setItem('dataikos_token', token);
        if (refreshToken) localStorage.setItem('dataikos_refresh_token', refreshToken);
        if (user) localStorage.setItem('dataikos_user', JSON.stringify(user));
    }

    clearAuth() {
        this.token = null;
        this.refreshToken = null;
        this.user = null;
        
        localStorage.removeItem('dataikos_token');
        localStorage.removeItem('dataikos_refresh_token');
        localStorage.removeItem('dataikos_user');
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);
            
            // Si le token a expiré, essayer de le rafraîchir
            if (response.status === 401 && this.refreshToken && endpoint !== '/api/auth/refresh') {
                const refreshed = await this.refreshAuth();
                if (refreshed) {
                    // Réessayer la requête avec le nouveau token
                    headers['Authorization'] = `Bearer ${this.token}`;
                    const retryResponse = await fetch(url, { ...config, headers });
                    return this.handleResponse(retryResponse);
                }
            }
            
            return this.handleResponse(response);
        } catch (error) {
            console.error('API request failed:', error);
            throw new Error(`Network error: ${error.message}`);
        }
    }

    async handleResponse(response) {
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
            } catch {
                // Si la réponse n'est pas du JSON
            }
            throw new Error(errorMessage);
        }

        // Si la réponse est 204 No Content
        if (response.status === 204) {
            return null;
        }

        try {
            return await response.json();
        } catch {
            return {};
        }
    }

    async refreshAuth() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                this.setAuth(data.access_token, this.refreshToken, this.user);
                return true;
            }
        } catch (error) {
            console.error('Failed to refresh token:', error);
        }
        
        // Si le rafraîchissement échoue, déconnecter l'utilisateur
        this.clearAuth();
        return false;
    }

    // Auth
    async login(username, password) {
        const data = await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        if (data.access_token) {
            this.setAuth(
                data.access_token,
                data.refresh_token,
                { username, is_admin: true }
            );
        }
        
        return data;
    }

    async logout() {
        try {
            await this.request('/api/auth/logout', { method: 'POST' });
        } catch (error) {
            // Ignorer les erreurs de déconnexion
        }
        this.clearAuth();
    }

    async validateToken() {
        try {
            await this.request('/api/auth/validate-token');
            return true;
        } catch {
            return false;
        }
    }

    // Orders
    async createOrder(orderData) {
        return this.request('/api/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    async getOrders(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/api/orders?${params}`);
    }

    async updateOrderStatus(orderId, status, notes = null) {
        return this.request(`/api/orders/${orderId}`, {
            method: 'PUT',
            body: JSON.stringify({ status, notes })
        });
    }

    async deleteOrder(orderId) {
        return this.request(`/api/orders/${orderId}`, {
            method: 'DELETE'
        });
    }

    // Messages
    async sendMessage(messageData) {
        return this.request('/api/messages', {
            method: 'POST',
            body: JSON.stringify(messageData)
        });
    }

    async getMessages(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/api/messages?${params}`);
    }

    async markMessageAsRead(messageId) {
        return this.request(`/api/messages/${messageId}/read`, {
            method: 'PUT'
        });
    }

    async deleteMessage(messageId) {
        return this.request(`/api/messages/${messageId}`, {
            method: 'DELETE'
        });
    }

    // Gallery
    async getGallery(category = null, limit = 100, skip = 0) {
        const params = new URLSearchParams();
        if (category && category !== 'all') params.append('category', category);
        params.append('limit', limit);
        params.append('skip', skip);
        
        return this.request(`/api/gallery?${params}`);
    }

    async uploadImage(formData) {
        const response = await fetch(`${API_BASE_URL}/api/gallery/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
        
        return this.handleResponse(response);
    }

    async deleteGalleryItem(itemId) {
        return this.request(`/api/gallery/${itemId}`, {
            method: 'DELETE'
        });
    }

    async getGalleryCategories() {
        return this.request('/api/gallery/categories');
    }

    // Admin
    async getDashboardStats() {
        return this.request('/api/admin/dashboard/stats');
    }

    async getRecentActivity() {
        return this.request('/api/admin/recent-activity');
    }

    async getRevenueChartData(period = '7d') {
        return this.request(`/api/admin/revenue/chart?period=${period}`);
    }

    async getOrdersChartData(period = '7d') {
        return this.request(`/api/admin/orders/chart?period=${period}`);
    }

    async getPopularServices() {
        return this.request('/api/admin/services/popular');
    }

    // File upload
    async uploadFiles(files, category) {
        const formData = new FormData();
        
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        formData.append('category', category);
        
        const response = await fetch(`${API_BASE_URL}/api/gallery/bulk-upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
        
        return this.handleResponse(response);
    }
}

// Export singleton instance
const api = new DataikosAPI();
window.DataikosAPI = api;
