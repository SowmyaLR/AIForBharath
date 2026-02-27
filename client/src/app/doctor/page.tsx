"use client"
import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { Stethoscope, Activity, CheckCircle2, ShieldAlert, LogOut, Clock, BrainCircuit, HeartPulse, Database } from 'lucide-react';
import Link from 'next/link';
import axios from 'axios';
import { motion } from 'framer-motion';

export default function DoctorPage() {
    const { user, token, logout, isLoading } = useAuth();
    const router = useRouter();
    const [queue, setQueue] = useState<any[]>([]);
    const [selectedPatient, setSelectedPatient] = useState<any | null>(null);
    const [editedSoap, setEditedSoap] = useState<any>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<string>('');

    useEffect(() => {
        if (!isLoading && (!user || user.role !== 'doctor')) {
            router.push('/login');
        }
    }, [user, isLoading, router]);

    if (isLoading || !user || user.role !== 'doctor') {
        return null;
    }

    useEffect(() => {
        fetchQueue();
        const interval = setInterval(fetchQueue, 15000);
        return () => clearInterval(interval);
    }, []);

    const fetchQueue = async () => {
        try {
            const res = await axios.get('http://localhost:8000/triage/queue');
            const filtered = res.data.filter((item: any) => item.status === 'ready_for_review' || item.status === 'finalized');
            setQueue(filtered);
        } catch (e) {
            console.error(e);
        }
    };

    const selectPatient = (patient: any) => {
        setSelectedPatient(patient);
        setEditedSoap(patient.soap_note ? { ...patient.soap_note } : { subjective: '', objective: '', assessment: '', plan: '' });
        setSaveStatus('');
    };

    const handleSoapChange = (section: string, value: string) => {
        if (editedSoap) {
            setEditedSoap({ ...editedSoap, [section]: value });
            setSaveStatus('');
        }
    };

    const saveSoap = async () => {
        if (!selectedPatient || !editedSoap) return;
        setIsSaving(true);
        try {
            await axios.post(`http://localhost:8000/triage/${selectedPatient.id}/soap`, editedSoap);
            setSaveStatus('Draft saved successfully');
            // Update local state in queue if needed
            fetchQueue();
        } catch (e) {
            console.error(e);
            setSaveStatus('Error saving draft');
        } finally {
            setIsSaving(false);
        }
    };

    const approveTriage = async () => {
        if (!selectedPatient) return;
        try {
            // First save any unsaved changes
            await axios.post(`http://localhost:8000/triage/${selectedPatient.id}/soap`, editedSoap);

            await axios.post(`http://localhost:8000/triage/${selectedPatient.id}/finalize`);
            alert("Triage approved successfully. You can now move it to EHR.");
            setSelectedPatient({ ...selectedPatient, status: 'finalized' });
            fetchQueue();
        } catch (e) {
            console.error(e);
            alert("Error finalizing triage");
        }
    };

    const moveToEhr = async () => {
        if (!selectedPatient) return;
        try {
            await axios.post(`http://localhost:8000/triage/${selectedPatient.id}/export`);
            alert("Record is being exported to FHIR format in the background. You can view it in the FHIR Viewer later.");
            setSelectedPatient(null);
            fetchQueue();
        } catch (e) {
            console.error(e);
            alert("Error starting EHR export");
        }
    };

    const getRiskColor = (tier: string) => {
        if (tier === 'EMERGENCY') return 'text-red-700 bg-red-100 border-red-200 shadow-sm shadow-red-200';
        if (tier === 'URGENT') return 'text-orange-700 bg-orange-100 border-orange-200';
        if (tier === 'SEMI_URGENT') return 'text-amber-700 bg-amber-100 border-amber-200';
        return 'text-green-700 bg-green-100 border-green-200';
    };

    return (
        <div className="min-h-screen bg-slate-50">
            <nav className="bg-white shadow-sm border-b border-slate-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-2 text-primary font-bold text-xl">
                                <Stethoscope className="h-6 w-6" />
                                VaidyaSaarathi
                            </div>
                            <div className="h-6 w-[1px] bg-slate-200" />
                            <Link href="/ehr-records" className="flex items-center gap-2 text-slate-500 hover:text-teal-600 transition-colors">
                                <Database size={18} />
                                <span className="text-sm font-bold">FHIR Viewer</span>
                            </Link>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="flex flex-col items-end">
                                <span className="text-sm font-bold text-slate-900">{user.name}</span>
                                <span className="text-xs font-semibold text-primary">{user.specialty} Specialist</span>
                            </div>
                            <button onClick={logout} className="ml-2 text-slate-400 hover:text-red-500 transition-colors">
                                <LogOut size={20} />
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                    {/* Left Queue Panel */}
                    <div className="lg:col-span-4 flex flex-col h-[calc(100vh-140px)]">
                        <div className="mb-4">
                            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Triage Queue</h2>
                            <p className="text-sm text-slate-500 flex items-center gap-1 mt-1"><Activity size={14} /> Auto-sorted by HAI-DEF AI Risk Score</p>
                        </div>

                        <div className="bg-white rounded-2xl shadow-xl border border-slate-100 flex-1 overflow-y-auto w-full p-3 space-y-3">
                            {queue.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center p-8 text-slate-400 text-sm">
                                    <CheckCircle2 className="h-12 w-12 text-green-200 mb-2" />
                                    Queue is empty.
                                </div>
                            ) : (
                                queue.map((pt) => {
                                    return (
                                        <div
                                            key={pt.id}
                                            onClick={() => selectPatient(pt)}
                                            className={`p-4 rounded-xl border cursor-pointer transition-all transform hover:-translate-y-1 hover:shadow-md
                                        ${selectedPatient?.id === pt.id ? 'ring-2 ring-primary border-transparent' : 'border-slate-100 hover:border-primary/30'}
                                        ${pt.status === 'finalized' ? 'opacity-60 bg-slate-50' : 'bg-white'}
                                    `}
                                        >
                                            <div className="flex justify-between items-start mb-2">
                                                <h3 className="font-bold text-slate-900">Patient: {pt.patient_id}</h3>
                                                <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border uppercase tracking-wider ${getRiskColor(pt.triage_tier)}`}>
                                                    {pt.triage_tier || 'Routine'}
                                                </span>
                                            </div>
                                            <div className="flex items-center justify-between text-xs text-slate-500">
                                                <span className="flex items-center gap-1"><BrainCircuit size={12} /> {pt.specialty} Triage</span>
                                                <span className="flex items-center gap-1"><Clock size={12} /> {new Date(pt.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                            </div>
                                        </div>
                                    )
                                })
                            )}
                        </div>
                    </div>

                    {/* Right Clinical Panel */}
                    <div className="lg:col-span-8 flex flex-col h-[calc(100vh-140px)]">
                        {selectedPatient ? (
                            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="bg-white rounded-2xl shadow-xl border border-slate-100 flex-1 flex flex-col overflow-hidden">

                                {/* Header Banner */}
                                <div className="bg-slate-900 px-6 py-4 flex justify-between items-center text-white">
                                    <div>
                                        <h2 className="text-xl font-bold flex items-center gap-2">
                                            {selectedPatient.patient_id}
                                            {selectedPatient.status === 'finalized' && <span className="bg-green-500/20 text-green-300 border border-green-500/50 text-xs px-2 py-0.5 rounded ml-2">Finalized</span>}
                                        </h2>
                                        <p className="text-slate-400 text-sm flex items-center gap-1 mt-1">
                                            <span className="bg-white/10 px-2 py-0.5 rounded text-xs">{selectedPatient.language} Audio</span>
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-xs text-slate-400 uppercase tracking-wider font-bold mb-1">Triage Category</div>
                                        <div className={`px-4 py-1.5 rounded-full font-extrabold text-sm border ${getRiskColor(selectedPatient.triage_tier)}`}>
                                            {selectedPatient.triage_tier || 'ROUTINE'}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex-1 overflow-y-auto p-6 scroll-smooth">

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                                        <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-4">
                                            <h4 className="text-xs font-bold text-blue-800 uppercase tracking-wider mb-2 flex items-center gap-2"><Activity size={14} /> Translated Complaint</h4>
                                            <div className="text-sm text-slate-700 leading-relaxed italic border-l-2 border-blue-400 pl-3">
                                                "{selectedPatient.transcription || 'No transcription available.'}"
                                            </div>
                                        </div>

                                        <div className="bg-amber-50/50 border border-amber-100 rounded-xl p-4">
                                            <h4 className="text-xs font-bold text-amber-800 uppercase tracking-wider mb-2 flex items-center gap-2"><HeartPulse size={14} /> Nurse Vitals</h4>
                                            {selectedPatient.vitals ? (
                                                <div className="grid grid-cols-3 gap-2 text-sm">
                                                    <div><span className="text-slate-500">BP:</span> <span className="font-semibold">{selectedPatient.vitals.blood_pressure_systolic}/{selectedPatient.vitals.blood_pressure_diastolic}</span></div>
                                                    <div><span className="text-slate-500">HR:</span> <span className="font-semibold">{selectedPatient.vitals.heart_rate}</span></div>
                                                    <div><span className="text-slate-500">Temp:</span> <span className="font-semibold">{selectedPatient.vitals.temperature}°C</span></div>
                                                    <div><span className="text-slate-500">SpO2:</span> <span className="font-semibold text-teal-600">{selectedPatient.vitals.oxygen_saturation}%</span></div>
                                                    <div><span className="text-slate-500">Resp:</span> <span className="font-semibold">{selectedPatient.vitals.respiratory_rate}</span></div>
                                                </div>
                                            ) : (
                                                <div className="text-sm text-amber-600 italic">Pending nurse vitals submission...</div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="mb-4 flex items-center justify-between">
                                        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                                            <BrainCircuit className="text-primary" /> AI drafted SOAP Note
                                        </h3>
                                        <p className="text-xs text-slate-500">Edit fields to finalize clinical documentation.</p>
                                    </div>

                                    {editedSoap && (
                                        <div className="space-y-4">
                                            {['subjective', 'objective', 'assessment', 'plan'].map((section) => (
                                                <div key={section} className="flex flex-col group relative">
                                                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1 px-1">{section}</label>
                                                    <textarea
                                                        className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-primary/50 outline-none transition-all resize-none min-h-[100px]"
                                                        value={editedSoap[section as keyof typeof editedSoap] || ''}
                                                        onChange={(e) => handleSoapChange(section, e.target.value)}
                                                        readOnly={selectedPatient.status === 'finalized'}
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                </div>

                                <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-between items-center">
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center gap-2 text-xs text-amber-600 font-medium bg-amber-100 px-3 py-1.5 rounded-lg border border-amber-200">
                                            <ShieldAlert size={14} /> AI is an assistant. Validate before saving.
                                        </div>
                                        {saveStatus && <p className={`text-xs font-bold px-1 ${saveStatus.includes('Error') ? 'text-red-500' : 'text-green-600'}`}>{saveStatus}</p>}
                                    </div>

                                    {selectedPatient.status !== 'finalized' ? (
                                        <div className="flex gap-3">
                                            <button
                                                onClick={saveSoap}
                                                disabled={isSaving}
                                                className="px-6 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 font-bold hover:bg-slate-50 transition-all flex items-center gap-2"
                                            >
                                                {isSaving ? <Activity className="animate-spin" size={18} /> : <CheckCircle2 size={18} className="text-teal-500" />}
                                                Save Draft
                                            </button>
                                            <button
                                                onClick={approveTriage}
                                                className="px-6 py-2.5 rounded-xl bg-slate-900 text-white font-bold hover:bg-slate-800 shadow-lg shadow-slate-900/20 transition-all flex items-center gap-2"
                                            >
                                                <CheckCircle2 size={18} /> Approve & Finalize
                                            </button>
                                        </div>
                                    ) : (
                                        <button
                                            onClick={moveToEhr}
                                            className="px-6 py-2.5 rounded-xl bg-teal-600 text-white font-bold hover:bg-teal-700 shadow-lg shadow-teal-900/20 transition-all flex items-center gap-2"
                                        >
                                            <Activity size={18} /> Move to EHR (FHIR)
                                        </button>
                                    )}
                                </div>

                            </motion.div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 bg-white/50 rounded-2xl border border-slate-100 border-dashed">
                                <Stethoscope size={64} className="mb-4 text-slate-200" />
                                <h3 className="text-lg font-medium text-slate-600">No Patient Selected</h3>
                                <p className="mt-1">Select a patient from the queue to review triage analysis.</p>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
