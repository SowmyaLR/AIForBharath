"use client"
import { useState } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ShieldAlert, Activity, HeartPulse } from 'lucide-react';
import axios from 'axios';

export default function LoginPage() {
    const [hospitalId, setHospitalId] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await axios.post('http://localhost:8000/auth/login', {
                hospital_id: hospitalId,
                password: password
            });

            const { token, user } = response.data;
            login(token, user);

            // Redirect based on role
            if (user.role === 'receptionist' || user.role === 'nurse') router.push('/nurse');
            else if (user.role === 'doctor') router.push('/doctor');
            else router.push('/');

        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    // Quick fill buttons for hackathon demo
    const autofill = (id: string) => {
        setHospitalId(id);
        setPassword('password');
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
            {/* Background Decorations */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-teal-200/40 rounded-full blur-[120px] mix-blend-multiply" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-200/40 rounded-full blur-[120px] mix-blend-multiply" />

            <div className="sm:mx-auto sm:w-full sm:max-w-md z-10 relative">
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", bounce: 0.5 }}
                    className="mx-auto h-16 w-16 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-2xl shadow-lg flex items-center justify-center"
                >
                    <HeartPulse className="h-8 w-8 text-white" />
                </motion.div>
                <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-900 tracking-tight">
                    VaidyaSaarathi
                </h2>
                <p className="mt-2 text-center text-sm text-slate-600">
                    AI-Assisted Privacy-First Clinical Triage
                </p>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10 relative"
            >
                <div className="glass-panel py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10">
                    <form className="space-y-6" onSubmit={handleLogin}>
                        <div>
                            <label className="block text-sm font-medium text-slate-700">Hospital ID</label>
                            <div className="mt-1">
                                <input
                                    type="text"
                                    required
                                    value={hospitalId}
                                    onChange={(e) => setHospitalId(e.target.value)}
                                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm placeholder-slate-400 focus:outline-none focus:ring-teal-500 focus:border-teal-500 sm:text-sm bg-white/50"
                                    placeholder="Enter ID (e.g. nur_01)"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700">Password</label>
                            <div className="mt-1">
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm placeholder-slate-400 focus:outline-none focus:ring-teal-500 focus:border-teal-500 sm:text-sm bg-white/50"
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="text-red-500 text-sm flex items-center gap-1">
                                <ShieldAlert size={16} /> {error}
                            </div>
                        )}

                        <div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-md text-sm font-medium text-white bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-all transform active:scale-95"
                            >
                                {loading ? <Activity className="animate-spin" /> : "Sign in to Dashboard"}
                            </button>
                        </div>
                    </form>

                    <div className="mt-6">
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-slate-200" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-white/80 text-slate-500">Demo Quick Login</span>
                            </div>
                        </div>

                        <div className="mt-6 grid grid-cols-2 gap-3">
                            <button onClick={() => autofill('nur_01')} className="w-full inline-flex justify-center py-2 px-3 border border-slate-300 rounded-md shadow-sm bg-white text-xs font-medium text-slate-500 hover:bg-slate-50">
                                Nurse Intake
                            </button>
                            <button onClick={() => autofill('doc_cardio')} className="w-full inline-flex justify-center py-2 px-3 border border-slate-300 rounded-md shadow-sm bg-white text-xs font-medium text-slate-500 hover:bg-slate-50">
                                Doctor
                            </button>
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
