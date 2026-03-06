import { apiClient } from '../api/api-client';
import { TriageRecord, SOAPNote, VitalSigns } from '../types';

export const triageRepository = {
    createTriage: async (formData: FormData, idempotencyKey?: string): Promise<TriageRecord> => {
        const response = await apiClient.post<TriageRecord>('/triage/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
                ...(idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {}),
            },
        });
        return response.data;
    },

    createVitalsTriage: async (formData: FormData, idempotencyKey?: string): Promise<TriageRecord> => {
        const response = await apiClient.post<TriageRecord>('/triage/vitals', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
                ...(idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {}),
            },
        });
        return response.data;
    },

    uploadAudio: async (id: string, formData: FormData): Promise<TriageRecord> => {
        const response = await apiClient.post<TriageRecord>(`/triage/audio/${id}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    getQueue: async (specialty?: string): Promise<TriageRecord[]> => {
        const response = await apiClient.get<TriageRecord[]>('/triage/queue', {
            params: { specialty },
        });
        return response.data;
    },

    getTriage: async (id: string): Promise<TriageRecord> => {
        const response = await apiClient.get<TriageRecord>(`/triage/${id}`);
        return response.data;
    },

    updateSoap: async (id: string, soap: SOAPNote): Promise<TriageRecord> => {
        const response = await apiClient.post<TriageRecord>(`/triage/${id}/soap`, soap);
        return response.data;
    },

    addVitals: async (id: string, vitals: VitalSigns): Promise<TriageRecord> => {
        const response = await apiClient.post<TriageRecord>(`/triage/${id}/vitals`, vitals);
        return response.data;
    },

    finalize: async (id: string): Promise<TriageRecord> => {
        const response = await apiClient.post<TriageRecord>(`/triage/${id}/finalize`);
        return response.data;
    },

    exportToEhr: async (id: string): Promise<{ status: string; message: string }> => {
        const response = await apiClient.post<{ status: string; message: string }>(`/triage/${id}/export`);
        return response.data;
    }
};

