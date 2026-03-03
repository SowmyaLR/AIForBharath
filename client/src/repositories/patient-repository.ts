import { apiClient } from '../api/api-client';
import { Patient } from '../types';

export const patientRepository = {
    getPatient: async (hospitalId: string): Promise<Patient> => {
        const response = await apiClient.get<Patient>(`/patients/${hospitalId}`);
        return response.data;
    },

    createPatient: async (data: Partial<Patient>): Promise<Patient> => {
        const response = await apiClient.post<Patient>('/patients/', data);
        return response.data;
    }
};
