import axios from 'axios';

const API = axios.create({
    baseURL: 'http://localhost:8000/api/',
});

API.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export const getNetworks = (hostId) =>
    API.get(`hosts/${hostId}/networks/`);

export const createNetwork = (hostId, data) =>
    API.post(`hosts/${hostId}/networks/`, data);

export const inspectNetwork = (hostId, id) =>
    API.get(`hosts/${hostId}/networks/${id}/`);

export const deleteNetwork = (hostId, id) =>
    API.delete(`hosts/${hostId}/networks/${id}/`);


// ==========================================
// CONTAINER ATTACHMENT ENDPOINTS
// ==========================================

export const connectContainer = (hostId, id, data) =>
    API.post(`hosts/${hostId}/networks/${id}/connect/`, data);

export const disconnectContainer = (hostId, id, data) =>
    API.post(`hosts/${hostId}/networks/${id}/disconnect/`, data);