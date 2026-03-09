"use client"
import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { Stethoscope, Activity, CheckCircle2, ShieldAlert, LogOut, Clock, BrainCircuit, HeartPulse, Database } from 'lucide-react';
import { AiStatusBadge } from '@/components/AiStatusBadge';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { triageRepository } from '@/repositories';
import { TriageRecord, SOAPNote } from '@/types';

export default function DoctorPage() {
    const { user, token, logout, isLoading } = useAuth();
    const router = useRouter();
    const [queue, setQueue] = useState<TriageRecord[]>([]);
    const [filterSpecialty, setFilterSpecialty] = useState<string>('All');
    const [selectedPatient, setSelectedPatient] = useState<TriageRecord | null>(null);
    const [editedSoap, setEditedSoap] = useState<SOAPNote | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<string>('');

    useEffect(() => {
        if (!isLoading && (!user || user.role !== 'doctor')) {
            router.push('/login');
        }
    }, [user, isLoading, router]);

    useEffect(() => {
        if (user) {
            fetchQueue();
            const interval = setInterval(fetchQueue, 10000); // 10s — faster for demo
            return () => clearInterval(interval);
        }
    }, [user, filterSpecialty]);

    if (isLoading || !user || user.role !== 'doctor') {
        return null;
    }

    async function fetchQueue() {
        if (!user) return;
        try {
            const records = await triageRepository.getQueue(filterSpecialty === 'All' ? undefined : filterSpecialty);
            const filtered = records.filter(item => item.status === 'ready_for_review' || item.status === 'finalized' || item.status === 'exported');

            // Priority: Highest risk first, then UNSEEN first, then newest first
            const sorted = filtered.sort((a, b) => {
                // Secondary score for risk tiers
                const tierScore = (t: string) => {
                    if (t === 'EMERGENCY') return 4;
                    if (t === 'URGENT') return 3;
                    if (t === 'SEMI_URGENT') return 2;
                    return 1;
                };

                const scoreA = tierScore(a.triage_tier);
                const scoreB = tierScore(b.triage_tier);

                if (scoreA !== scoreB) return scoreB - scoreA;

                // If same priority, unseen comes first
                if (a.is_seen !== b.is_seen) return a.is_seen ? 1 : -1;

                // If same status, newest first
                return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            });

            setQueue(sorted);

            // Sync selected patient if it was updated in the background
            if (selectedPatient) {
                const updated = sorted.find(p => p.id === selectedPatient.id);
                if (updated && JSON.stringify(updated.soap_note) !== JSON.stringify(selectedPatient.soap_note)) {
                    setSelectedPatient(updated);
                    if (!editedSoap || (editedSoap.subjective === '' && updated.soap_note)) {
                        setEditedSoap(updated.soap_note ? { ...updated.soap_note } : { subjective: '', objective: '', assessment: '', plan: '' });
                    }
                }
            }
        } catch (e) {
            console.error(e);
        }
    }

    const selectPatient = async (patient: TriageRecord) => {
        setSelectedPatient(patient);
        setEditedSoap(patient.soap_note ? { ...patient.soap_note } : { subjective: '', objective: '', assessment: '', plan: '' });
        setSaveStatus('');

        // Mark as seen if not already
        if (!patient.is_seen) {
            try {
                await triageRepository.markAsSeen(patient.id);
                // Optimistic UI update
                setQueue(prev => prev.map(p => p.id === patient.id ? { ...p, is_seen: true } : p));
            } catch (e) {
                console.error("Failed to mark as seen", e);
            }
        }
    };

    const handleSoapChange = (section: keyof SOAPNote, value: string) => {
        if (editedSoap) {
            setEditedSoap({ ...editedSoap, [section]: value });
            setSaveStatus('');
        }
    };

    const saveSoap = async () => {
        if (!selectedPatient || !editedSoap) return;
        setIsSaving(true);
        try {
            await triageRepository.updateSoap(selectedPatient.id, editedSoap);
            setSaveStatus('Draft saved successfully');
            fetchQueue();
        } catch (e) {
            console.error(e);
            setSaveStatus('Error saving draft');
        } finally {
            setIsSaving(false);
        }
    };

    const approveTriage = async () => {
        if (!selectedPatient || !editedSoap) return;
        try {
            // First save any unsaved changes
            await triageRepository.updateSoap(selectedPatient.id, editedSoap);
            await triageRepository.finalize(selectedPatient.id);

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
            await triageRepository.exportToEhr(selectedPatient.id);
            alert("Record is being exported to FHIR format in the background.");
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
                            <AiStatusBadge />
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
                        <div className="mb-4 space-y-3">
                            <div className="flex justify-between items-end">
                                <div>
                                    <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Triage Queue</h2>
                                    <p className="text-sm text-slate-500 flex items-center gap-1 mt-1"><Activity size={14} /> AI Risk Sorted Queue</p>
                                </div>
                                <select
                                    value={filterSpecialty}
                                    onChange={(e) => setFilterSpecialty(e.target.value)}
                                    className="text-xs font-bold border rounded-lg px-2 py-1 bg-white outline-none focus:ring-2 focus:ring-primary/20"
                                >
                                    <option value="All">All Specialities</option>
                                    <option value="General Medicine">General Medicine</option>
                                    <option value="Cardiac">Cardiac</option>
                                    <option value="ENT">ENT</option>
                                    <option value="Pediatrics">Pediatrics</option>
                                    <option value="Orthopedics">Orthopedics</option>
                                </select>
                            </div>
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
                                            className={`p-4 rounded-xl border cursor-pointer transition-all transform hover:-translate-y-1 hover:shadow-md relative
                                        ${selectedPatient?.id === pt.id ? 'ring-2 ring-primary border-transparent' : 'border-slate-100 hover:border-primary/30'}
                                        ${pt.status === 'finalized' ? 'opacity-60 bg-slate-50' : 'bg-white'}
                                    `}
                                        >
                                            {!pt.is_seen && pt.status !== 'finalized' && (
                                                <div className="absolute -top-1 -right-1 flex h-3 w-3">
                                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                                                </div>
                                            )}
                                            <div className="flex justify-between items-start mb-2">
                                                <div className="flex flex-col">
                                                    <h3 className="font-bold text-slate-900 flex items-center gap-2">
                                                        Patient: {pt.patient_id}
                                                        {!pt.is_seen && <span className="text-[9px] bg-blue-600 text-white px-1.5 py-0.5 rounded font-black tracking-tighter">NEW</span>}
                                                    </h3>
                                                    <span className="text-slate-400 text-xs font-normal">({pt.patient_age || 'N/A'} yrs)</span>
                                                </div>
                                                <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border uppercase tracking-wider ${getRiskColor(pt.triage_tier)}`}>
                                                    {pt.triage_tier || 'Routine'}
                                                </span>
                                            </div>
                                            <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2">
                                                <span className="flex items-center gap-1 font-bold uppercase tracking-tight text-slate-400"><BrainCircuit size={10} /> {pt.specialty}</span>
                                                <span className="flex items-center gap-1 font-semibold">
                                                    <Clock size={10} />
                                                    {new Date(pt.created_at).toLocaleString([], {
                                                        day: '2-digit',
                                                        month: '2-digit',
                                                        hour: '2-digit',
                                                        minute: '2-digit',
                                                        hour12: false
                                                    })}
                                                </span>
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
                                            <span className="text-slate-400 font-medium ml-1">({selectedPatient.patient_age || 'N/A'} yrs)</span>
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
                                                    <div><span className="text-slate-500">Age:</span> <span className="font-semibold">{selectedPatient.patient_age || 'N/A'}</span></div>
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
                                                        onChange={(e) => handleSoapChange(section as keyof SOAPNote, e.target.value)}
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
