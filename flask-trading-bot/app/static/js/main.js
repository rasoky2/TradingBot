// JavaScript principal para Flask Trading Bot

// Configuración de la API
const API_BASE = '/api';

// Helper para hacer requests autenticados
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
}

// Formatear números
function formatNumber(num, decimals = 2) {
    return parseFloat(num).toFixed(decimals);
}

// Formatear fecha
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('es-ES');
}

// Notificaciones
function showNotification(message, type = 'info') {
    // TODO: Implementar sistema de notificaciones
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Exportar funciones globales
window.apiRequest = apiRequest;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.showNotification = showNotification;
