export interface User {
    id: string;
    hospital_id: string;
    name: string;
    role: string;
    specialty?: string | null;
}

export interface AuthResponse {
    token: string;
    user: User;
    expires_in: number;
}

export interface UserSession {
    user_id: string;
    role: string;
    specialty?: string | null;
    issued_at: number;
    expires_at: number;
}
