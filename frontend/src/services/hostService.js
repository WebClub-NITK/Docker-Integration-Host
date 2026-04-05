import { API_BASE_URL } from './apiConfig';

export const hostService = {
  async listHosts() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('Missing access token. Please login again.');
    }

    const response = await fetch(`${API_BASE_URL}/api/hosts/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      let errorPayload = null;
      try {
        errorPayload = await response.json();
      } catch {
        errorPayload = await response.text();
      }
      throw new Error(typeof errorPayload === 'string' ? errorPayload : errorPayload?.detail || 'Failed to fetch hosts');
    }

    return response.json();
  },
};
