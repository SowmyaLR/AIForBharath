"use client"
import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { HeartPulse, Activity, UserPlus, FileHeart, LogOut, Search } from 'lucide-react';
import axios from 'axios';
import { motion } from 'framer-motion';

export default function NursePage() {
    const { user, token, logout, isLoading } = useAuth();
    const router = useRouter();
    const [queue, setQueue] = useState<any[]>([]);
    const [selectedPatient, setSelectedPatient] = useState<any | null>(null);
    const [vitals, setVitals] = useState({
        temperature: 37.0,
        blood_pressure_systolic: 120,
        blood_pressure_diastolic: 80,
        heart_rate: 75,
        respiratory_rate: 16,
        oxygen_saturation: 98
    });

    useEffect(() => {
        if (!isLoading && (!user || user.role !== 'nurse')) {
            router.push('/login');
        }
    }, [user, isLoading, router]);

    if (isLoading || !user || user.role !== 'nurse') {
        return null;
    }

    useEffect(() => {
        fetchQueue();
        // Poll every 10 seconds for demo (WebSocket in prod)
        const interval = setInterval(fetchQueue, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchQueue = async () => {
        try {
            const res = await axios.get('http://localhost:8000/triage/queue');
            // Filter for patients who need vitals or are in progress
            setQueue(res.data.filter((item: any) => item.status !== 'finalized'));
        } catch (e) {
            console.error(e);
        }
    };

    const handleVitalsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setVitals({
            ...vitals,
            [e.target.name]: parseFloat(e.target.value) || 0
        });
    };

    const getRiskColor = (tier: string) => {
        if (tier === 'EMERGENCY') return 'text-red-700 bg-red-100 border-red-200 shadow-sm shadow-red-200';
        if (tier === 'URGENT') return 'text-orange-700 bg-orange-100 border-orange-200';
        if (tier === 'SEMI_URGENT') return 'text-amber-700 bg-amber-100 border-amber-200';
        return 'text-green-700 bg-green-100 border-green-200';
    };

    const submitVitals = async () => {
        if (!selectedPatient) return;
        try {
            await axios.post(`http://localhost:8000/triage/${selectedPatient.id}/vitals`, {
                ...vitals,
                recorded_at: new Date().toISOString(),
                recorded_by: user.id
            });
            alert('Vitals saved successfully!');
            setSelectedPatient(null);
            fetchQueue();
        } catch (e) {
            console.error("Failed to save vitals:", e);
            alert("Error saving vitals.");
        }
    };

    return (
        <div className="min-h-screen bg-slate-50">
            <nav className="bg-white shadow-sm border-b border-slate-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center gap-2 text-teal-700 font-bold text-xl">
                            <Activity className="h-6 w-6" />
                            VaidyaSaarathi
                        </div>
                        <div className="flex items-center gap-4">
                            <span className="text-sm font-medium text-slate-600 bg-slate-100 px-3 py-1 rounded-full">{user.name}</span>
                            <button onClick={logout} className="text-slate-400 hover:text-red-500 transition-colors">
                                <LogOut size={20} />
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-end mb-8">
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
                            <HeartPulse className="text-teal-600 h-8 w-8" />
                            Nursing Station
                        </h1>
                        <p className="mt-2 text-slate-500">Select a patient to record or update vital signs.</p>
                    </motion.div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Col: Queue */}
                    <div className="lg:col-span-1 bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden h-[calc(100vh-250px)] flex flex-col">
                        <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                            <h3 className="font-semibold text-slate-700">Patient Queue</h3>
                            <span className="bg-teal-100 text-teal-800 text-xs font-bold px-2 py-1 rounded-full">{queue.length} Active</span>
                        </div>
                        <div className="overflow-y-auto flex-1 p-2 space-y-2">
                            {queue.length === 0 ? (
                                <div className="text-center p-8 text-slate-400 text-sm">No patients waiting.</div>
                            ) : queue.map((patient: any) => (
                                <div
                                    key={patient.id}
                                    onClick={() => setSelectedPatient(patient)}
                                    className={`p-4 rounded-xl cursor-pointer transition-all border ${selectedPatient?.id === patient.id ? 'bg-teal-50 border-teal-200 shadow-sm' : 'bg-white border-transparent hover:bg-slate-50'}`}
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h4 className="font-semibold text-slate-900">{patient.patient_id}</h4>
                                            <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                                                <Activity size={12} /> AI Tier: <span className={`font-bold ${getRiskColor(patient.triage_tier).split(' ')[0]}`}>{patient.triage_tier || 'ROUTINE'}</span>
                                            </p>
                                        </div>
                                        {patient.vitals && <span className="text-[10px] font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded uppercase">Vitals Logged</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Right Col: Vitals Form */}
                    <div className="lg:col-span-2">
                        {selectedPatient ? (
                            <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
                                <div className="flex items-center gap-3 mb-8 pb-4 border-b border-slate-100">
                                    <div className="h-12 w-12 rounded-full bg-teal-100 flex items-center justify-center text-teal-700">
                                        <UserPlus size={24} />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold text-slate-900">Patient: {selectedPatient.patient_id}</h2>
                                        <p className="text-sm text-slate-500">Record clinical measurements</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-4 border-r border-slate-50 pr-6">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1">Temperature (°C)</label>
                                            <input type="number" step="0.1" name="temperature" value={vitals.temperature} onChange={handleVitalsChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none" />
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-sm font-medium text-slate-700 mb-1">BP Systolic</label>
                                                <input type="number" name="blood_pressure_systolic" value={vitals.blood_pressure_systolic} onChange={handleVitalsChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none" />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-slate-700 mb-1">BP Diastolic</label>
                                                <input type="number" name="blood_pressure_diastolic" value={vitals.blood_pressure_diastolic} onChange={handleVitalsChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none" />
                                            </div>
                                        </div>
                                    </div>
                                    <div className="space-y-4 pl-0 md:pl-6">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1">Heart Rate (bpm)</label>
                                            <input type="number" name="heart_rate" value={vitals.heart_rate} onChange={handleVitalsChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1">Resp. Rate (bpm)</label>
                                            <input type="number" name="respiratory_rate" value={vitals.respiratory_rate} onChange={handleVitalsChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1">O2 Saturation (%)</label>
                                            <input type="number" name="oxygen_saturation" value={vitals.oxygen_saturation} onChange={handleVitalsChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none" />
                                        </div>
                                    </div>
                                </div>

                                <div className="mt-10 flex justify-end gap-3 border-t border-slate-100 pt-6">
                                    <button onClick={() => setSelectedPatient(null)} className="px-6 py-2.5 rounded-xl text-slate-600 font-medium hover:bg-slate-100 transition-colors">Cancel</button>
                                    <button onClick={submitVitals} className="px-6 py-2.5 rounded-xl bg-teal-600 text-white font-medium hover:bg-teal-700 shadow-lg shadow-teal-200 transition-all flex items-center gap-2">
                                        <FileHeart size={18} /> Save Vitals
                                    </button>
                                </div>
                            </motion.div>
                        ) : (
                            <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-slate-400 bg-white/50 rounded-2xl border border-slate-100 border-dashed">
                                <Search size={48} className="mb-4 text-slate-200" />
                                <p>Select a patient from the queue to start.</p>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
