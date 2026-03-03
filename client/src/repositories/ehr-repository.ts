import { apiClient } from '../api/api-client';

export interface EHRRecord {
    patient_id: string;
    exported_at: string;
    fhir_bundle: any;
}

export const ehrRepository = {
    getRecords: async (): Promise<EHRRecord[]> => {
        const response = await apiClient.get<EHRRecord[]>('/ehr/records');
        return response.data;
    }
};
