"use client"
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { Mic, Square, Save, Activity, UploadCloud, Users, LogOut, Thermometer, Droplets, HeartPulse, Wind, AlertTriangle, Circle, Shield, Info, XCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { triageRepository, patientRepository } from '@/repositories';
import { TriageRecord } from '@/types';

export default function NurseIntakePage() {
    const { user, token, logout, isLoading } = useAuth();
    const router = useRouter();

    const [patientId, setPatientId] = useState('P-001');
    const [language, setLanguage] = useState('English');
    const [vitals, setVitals] = useState({
        temp: 37.0,
        bp_sys: 120,
        bp_dia: 80,
        hr: 75,
        rr: 16,
        spo2: 98,
        age: 30
    });

    const [isRecording, setIsRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
    const [uploadStatus, setUploadStatus] = useState<string>('');
    const [recordingTime, setRecordingTime] = useState(0);
    const [triageId, setTriageId] = useState<string | null>(null);
    const [finalZone, setFinalZone] = useState<string | null>(null);
    const [preliminaryZone, setPreliminaryZone] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [precautions, setPrecautions] = useState<string[]>([]);
    const [reasoningStep, setReasoningStep] = useState<string | null>(null);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    // Idempotency key — generated once per component mount, regenerated after each submission
    const idempotencyKeyRef = useRef<string>(crypto.randomUUID());

    useEffect(() => {
        if (!isLoading && (!user || user.role !== 'nurse')) {
            router.push('/login');
        }
    }, [user, isLoading, router]);

    if (isLoading || !user || user.role !== 'nurse') {
        return null;
    }

    const handleVitalsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setVitals({
            ...vitals,
            [e.target.name]: parseFloat(e.target.value) || 0
        });
    };

    const startRecording = async () => {
        try {
            if (!navigator?.mediaDevices?.getUserMedia) {
                alert("Microphone API is not available. Please ensure you are accessing the app via 'localhost' or HTTPS.");
                return;
            }
            setFinalZone(null);
            setPreliminaryZone(null);
            setErrorMessage(null);
            setTriageId(null);
            setUploadStatus(''); // Reset upload status for next submission
            setAudioBlob(null);
            // Regenerate idempotency key for each new recording
            idempotencyKeyRef.current = crypto.randomUUID();
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });

            mediaRecorderRef.current.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorderRef.current.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                setAudioBlob(blob);
                chunksRef.current = [];
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
            setRecordingTime(0);
            timerRef.current = setInterval(() => setRecordingTime(prev => prev + 1), 1000);

        } catch (err) {
            console.error("Microphone error:", err);
            alert("Could not access microphone.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
            setIsRecording(false);
            if (timerRef.current) clearInterval(timerRef.current);
        }
    };

    const reasoningSequence = [
        "Analyzing hemodynamic stability...",
        "Cross-referencing with clinical red-flags...",
        "Consulting MedGemma Protocol engine...",
        "Synthesizing immediate precautions..."
    ];

    const submitTriage = async () => {
        if (!audioBlob || uploadStatus === 'uploading' || uploadStatus === 'success') return;
        setUploadStatus('uploading');
        setPrecautions([]);
        setErrorMessage(null);
        setReasoningStep(reasoningSequence[0]);

        // Interface interaction timer
        let stepIdx = 0;
        const stepInterval = setInterval(() => {
            stepIdx++;
            if (stepIdx < reasoningSequence.length) {
                setReasoningStep(reasoningSequence[stepIdx]);
            }
        }, 1200);

        // Stage 1: Create Triage with Vitals (Synchronous Fast-Path)
        const vitalsData = new FormData();
        vitalsData.append('patient_id', patientId);
        vitalsData.append('patient_age', vitals.age.toString());
        vitalsData.append('temp', vitals.temp.toString());
        vitalsData.append('bp_sys', vitals.bp_sys.toString());
        vitalsData.append('bp_dia', vitals.bp_dia.toString());
        vitalsData.append('hr', vitals.hr.toString());
        vitalsData.append('rr', vitals.rr.toString());
        vitalsData.append('spo2', vitals.spo2.toString());

        try {
            console.log("Stage 1: Submitting Vitals...");
            const record = await triageRepository.createVitalsTriage(vitalsData, idempotencyKeyRef.current);
            clearInterval(stepInterval);
            setReasoningStep(null);
            setTriageId(record.id);

            if (record.vitals_status === 'ABNORMAL') {
                setPreliminaryZone('ABNORMAL');
                setPrecautions(record.preliminary_precautions || []);
            } else {
                setPreliminaryZone('STABLE');
            }

            // Stage 2: Upload Audio (Asynchronous Background Path)
            console.log("Stage 2: Uploading Audio for mapping...");
            const audioData = new FormData();
            audioData.append('audio', audioBlob, `triage_${Date.now()}.webm`);
            audioData.append('language', language);

            await triageRepository.uploadAudio(record.id, audioData);

            setUploadStatus('processed'); // We mark it as processed because the nurse's job is done

            // Auto-reset after a delay so they can do the next patient
            setTimeout(() => {
                setAudioBlob(null);
                setRecordingTime(0);
                setVitals({
                    temp: 37.0, bp_sys: 120, bp_dia: 80, hr: 75, rr: 16, spo2: 98, age: 30
                });
            }, 6000);

        } catch (err) {
            clearInterval(stepInterval);
            setReasoningStep(null);
            console.error("Submission failed:", err);
            setUploadStatus('error');
            setErrorMessage("Failed to submit triage case. Please check connectivity.");
        }
    };


    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Navigation Bar */}
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

            <main className="max-w-6xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
                    <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
                        <Thermometer className="text-teal-600" />
                        Clinical Intake Dashboard
                    </h1>
                    <p className="mt-2 text-slate-500">Unified capture for patient vitals and symptoms audio.</p>
                </motion.div>

                <div className="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
                    <div className="grid grid-cols-1 lg:grid-cols-2">
                        {/* Left Panel: Patient & Vitals */}
                        <div className="p-8 border-b lg:border-b-0 lg:border-r border-slate-100 bg-slate-50/50">
                            <h3 className="text-lg font-semibold text-slate-800 mb-6 flex items-center gap-2">
                                <Users size={20} className="text-teal-600" />
                                Patient & Clinical Vitals
                            </h3>

                            <div className="space-y-6">
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Patient ID</label>
                                        <input
                                            type="text"
                                            value={patientId}
                                            onChange={(e) => setPatientId(e.target.value)}
                                            className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                                            placeholder="P-001"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Age</label>
                                        <input
                                            type="number"
                                            name="age"
                                            value={vitals.age}
                                            onChange={handleVitalsChange}
                                            className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                                            placeholder="30"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Language</label>
                                        <select
                                            value={language}
                                            onChange={(e) => setLanguage(e.target.value)}
                                            className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                                        >
                                            <option value="English">English</option>
                                            <option value="Tamil">Tamil / தமிழ்</option>
                                            <option value="Hindi">Hindi / हिंदी</option>
                                            <option value="Telugu">Telugu / తెలుగు</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-slate-200">
                                    <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Vitals Entry</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="relative">
                                            <label className="block text-xs font-semibold text-slate-500 mb-1">Temp (°C)</label>
                                            <input type="number" step="0.1" name="temp" value={vitals.temp} onChange={handleVitalsChange} className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-teal-500" />
                                            <Thermometer className="absolute right-3 top-7 text-slate-300" size={16} />
                                        </div>
                                        <div className="relative">
                                            <label className="block text-xs font-semibold text-slate-500 mb-1">O2 Sat (%)</label>
                                            <input type="number" name="spo2" value={vitals.spo2} onChange={handleVitalsChange} className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-teal-500" />
                                            <Droplets className="absolute right-3 top-7 text-slate-300" size={16} />
                                        </div>
                                        <div className="relative">
                                            <label className="block text-xs font-semibold text-slate-500 mb-1">BP Sys/Dia</label>
                                            <div className="flex gap-1">
                                                <input type="number" name="bp_sys" value={vitals.bp_sys} onChange={handleVitalsChange} className="w-1/2 px-2 py-2 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-teal-500 text-center" />
                                                <span className="flex items-center text-slate-400">/</span>
                                                <input type="number" name="bp_dia" value={vitals.bp_dia} onChange={handleVitalsChange} className="w-1/2 px-2 py-2 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-teal-500 text-center" />
                                            </div>
                                        </div>
                                        <div className="relative">
                                            <label className="block text-xs font-semibold text-slate-500 mb-1">Heart Rate</label>
                                            <input type="number" name="hr" value={vitals.hr} onChange={handleVitalsChange} className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-teal-500" />
                                            <HeartPulse className="absolute right-3 top-7 text-slate-300" size={16} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Right Panel: Audio Intake */}
                        <div className="p-8 flex flex-col justify-center items-center bg-white">
                            <h3 className="text-lg font-semibold text-slate-800 self-start mb-10 flex items-center gap-2">
                                <Mic size={20} className="text-teal-600" />
                                Symptom Audio Capture
                            </h3>

                            <div className="text-center mb-8 relative">
                                {isRecording && (
                                    <div className="absolute -top-10 left-1/2 -translate-x-1/2 h-8 w-32 flex items-end justify-center gap-1">
                                        {[...Array(8)].map((_, i) => (
                                            <motion.div
                                                key={i}
                                                animate={{ height: [4, 16, 4] }}
                                                transition={{ repeat: Infinity, duration: 0.5, delay: i * 0.1 }}
                                                className="w-1 bg-teal-400 rounded-full"
                                            />
                                        ))}
                                    </div>
                                )}
                                <div className={`text-5xl font-mono mb-2 ${isRecording ? 'text-red-500' : 'text-slate-300'}`}>
                                    {formatTime(recordingTime)}
                                </div>
                                <p className="text-sm font-medium text-slate-400 italic">
                                    {isRecording ? "Listening for symptoms..." : "Ready to capture audio"}
                                </p>
                            </div>

                            <div className="flex gap-4 mb-10">
                                {!isRecording ? (
                                    <button
                                        onClick={startRecording}
                                        className="h-24 w-24 rounded-full bg-slate-100 flex items-center justify-center text-teal-600 hover:bg-teal-50 hover:text-teal-700 border-2 border-slate-200 hover:border-teal-300 transition-all active:scale-95 shadow-xl shadow-slate-100 group"
                                    >
                                        <Mic size={40} className="group-hover:scale-110 transition-transform" />
                                    </button>
                                ) : (
                                    <button
                                        onClick={stopRecording}
                                        className="h-24 w-24 rounded-full bg-red-50 flex items-center justify-center text-red-600 border-2 border-red-200 animate-pulse active:scale-95 shadow-xl shadow-red-100"
                                    >
                                        <Square size={32} className="fill-current" />
                                    </button>
                                )}
                            </div>

                            {audioBlob && !isRecording && (
                                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full">
                                    <button
                                        onClick={submitTriage}
                                        disabled={uploadStatus === 'uploading' || uploadStatus === 'processed'}
                                        className={`w-full py-4 rounded-2xl font-bold flex items-center justify-center gap-2 shadow-2xl transition-all
                                    ${(uploadStatus === 'success' || uploadStatus === 'processed') ? 'bg-green-500 text-white shadow-green-200' :
                                                uploadStatus === 'error' ? 'bg-red-500 text-white shadow-red-200' :
                                                    'bg-teal-600 text-white hover:bg-teal-700 shadow-teal-200'}
                                `}
                                    >
                                        {uploadStatus === 'uploading' && (
                                            <div className="flex flex-col items-center">
                                                <Activity className="animate-spin mb-1" />
                                                <div className="text-[10px] uppercase tracking-widest font-black opacity-80">{reasoningStep}</div>
                                            </div>
                                        )}
                                        {uploadStatus === 'processed' && <>Triage Case Created Successfully!</>}
                                        {uploadStatus === 'error' && <>Submission Failed. Retry?</>}
                                        {uploadStatus === '' && <><UploadCloud /> Submit Triage Case</>}
                                    </button>
                                </motion.div>
                            )}

                            {/* Universal Zone Indicator */}
                            <AnimatePresence>
                                {(uploadStatus === 'uploading' || finalZone || uploadStatus === 'processed') && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 10 }}
                                        className="mt-8 w-full"
                                    >
                                        <div className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all duration-500 ${uploadStatus === 'processed' ? (preliminaryZone === 'ABNORMAL' ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200') : 'bg-slate-50 border-slate-200 border-dashed'}`}>
                                            <div className="flex items-center gap-3 self-start">
                                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white ${uploadStatus === 'uploading' ? 'bg-slate-400' :
                                                    finalZone === 'EMERGENCY' ? 'bg-red-500' :
                                                        finalZone === 'URGENT' ? 'bg-orange-500' :
                                                            finalZone === 'SEMI_URGENT' ? 'bg-yellow-500' :
                                                                'bg-green-500'
                                                    }`}>
                                                    <Info size={18} />
                                                </div>
                                                <div>
                                                    <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Patient Care Path</h4>
                                                    <p className="text-[10px] text-slate-500 font-medium">Automatic Zone Assignment</p>
                                                </div>
                                            </div>

                                            {uploadStatus === 'uploading' ? (
                                                <div className="flex flex-col items-center py-8 w-full">
                                                    <div className="relative mb-6">
                                                        <Activity className="text-teal-500 animate-spin" size={48} />
                                                        <motion.div
                                                            animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.6, 0.3] }}
                                                            transition={{ repeat: Infinity, duration: 2 }}
                                                            className="absolute inset-0 bg-teal-200 rounded-full filter blur-xl -z-10"
                                                        />
                                                    </div>
                                                    <p className="text-sm font-black text-slate-800 uppercase tracking-tighter mb-1">MedGemma reasoning active</p>
                                                    <p className="text-[11px] text-teal-600 font-bold animate-pulse">{reasoningStep}</p>
                                                    <div className="mt-6 w-48 h-1 bg-slate-100 rounded-full overflow-hidden">
                                                        <motion.div
                                                            initial={{ x: "-100%" }}
                                                            animate={{ x: "100%" }}
                                                            transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                                                            className="w-full h-full bg-teal-500"
                                                        />
                                                    </div>
                                                </div>
                                            ) : uploadStatus === 'processed' ? (
                                                <div className="flex flex-col items-center w-full py-4 text-center">
                                                    <div className={`mb-4 w-20 h-20 rounded-3xl flex items-center justify-center shadow-lg transition-transform hover:scale-105 duration-300 ${preliminaryZone === 'ABNORMAL' ? 'bg-red-500 text-white' : 'bg-green-500 text-white'}`}>
                                                        {preliminaryZone === 'ABNORMAL' ? <AlertTriangle size={48} /> : <Shield size={48} />}
                                                    </div>
                                                    <h2 className={`text-2xl font-black uppercase tracking-tighter ${preliminaryZone === 'ABNORMAL' ? 'text-red-600' : 'text-green-600'}`}>
                                                        {preliminaryZone} VITALS
                                                    </h2>

                                                    {preliminaryZone === 'ABNORMAL' && precautions.length > 0 && (
                                                        <div className="mt-4 w-full text-left bg-white p-4 rounded-xl border border-red-100 shadow-inner">
                                                            <p className="text-[10px] font-bold text-red-500 uppercase tracking-widest mb-2 flex items-center gap-1">
                                                                <Shield size={10} /> MedGemma First Aid Actions
                                                            </p>
                                                            <ul className="space-y-2">
                                                                {precautions.map((p, i) => (
                                                                    <motion.li
                                                                        initial={{ opacity: 0, x: -10 }}
                                                                        animate={{ opacity: 1, x: 0 }}
                                                                        transition={{ delay: i * 0.1 }}
                                                                        key={i}
                                                                        className="text-xs text-slate-700 flex items-start gap-2"
                                                                    >
                                                                        <div className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1 flex-shrink-0" />
                                                                        {p}
                                                                    </motion.li>
                                                                ))}
                                                            </ul>
                                                        </div>
                                                    )}

                                                    <div className="mt-6 flex flex-col items-center gap-1">
                                                        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase">
                                                            <Activity size={12} className="text-teal-500" /> Full AI Analysis Sent
                                                        </div>
                                                        <p className="text-[10px] text-slate-400">Doctor will review SOAP note in queue.</p>
                                                    </div>
                                                </div>
                                            ) : errorMessage ? (
                                                <div className="flex flex-col items-center py-4 w-full text-center">
                                                    <XCircle className="text-red-400 mb-3" size={40} />
                                                    <p className="text-sm font-bold text-red-600 mb-1">Submission Failed</p>
                                                    <p className="text-xs text-slate-500 max-w-[220px]">{errorMessage}</p>
                                                    <button
                                                        onClick={() => { setErrorMessage(null); setUploadStatus(''); }}
                                                        className="mt-3 text-xs text-teal-600 underline"
                                                    >Try Again</button>
                                                </div>
                                            ) : null}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>
                </div>

                <p className="mt-8 text-center text-slate-400 text-sm">
                    Privacy Note: Audio and clinical data are processed within the hospital's private AWS instance.
                </p>
            </main>
        </div>
    );
}
