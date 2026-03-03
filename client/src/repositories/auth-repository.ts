import { apiClient } from '../api/api-client';
import { AuthResponse } from '../types';

export const authRepository = {
    login: async (hospital_id: string, password: string): Promise<AuthResponse> => {
        const response = await apiClient.post<AuthResponse>('/auth/login', {
            hospital_id,
            password,
        });
        return response.data;
    },

    verifyToken: async (token: string) => {
        const response = await apiClient.get('/auth/me', {
            params: { token }
        });
        return response.data;
    }
};
