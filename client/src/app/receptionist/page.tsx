"use client"
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { Mic, Square, Save, Activity, UploadCloud, Users, LogOut } from 'lucide-react';
import axios from 'axios';
import { motion } from 'framer-motion';

export default function ReceptionistPage() {
    const { user, token, logout, isLoading } = useAuth();
    const router = useRouter();

    const [patientId, setPatientId] = useState('P-001'); // Default for demo
    const [language, setLanguage] = useState('English');
    const [isRecording, setIsRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
    const [uploadStatus, setUploadStatus] = useState<string>('');
    const [recordingTime, setRecordingTime] = useState(0);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        if (!isLoading && (!user || user.role !== 'receptionist')) {
            router.push('/login');
        }
    }, [user, isLoading, router]);

    if (isLoading || !user || user.role !== 'receptionist') {
        return null;
    }

    const startRecording = async () => {
        try {
            if (!navigator?.mediaDevices?.getUserMedia) {
                alert("Microphone API is not available. Please ensure you are accessing the app via 'localhost' or HTTPS, as browsers block microphones on unencrypted network IPs.");
                return;
            }
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

    const submitTriage = async () => {
        if (!audioBlob || uploadStatus === 'uploading' || uploadStatus === 'success') return;
        setUploadStatus('uploading');

        const formData = new FormData();
        formData.append('patient_id', patientId);
        formData.append('language', language);
        formData.append('audio', audioBlob, `triage_${Date.now()}.webm`);

        try {
            await axios.post('http://localhost:8000/triage/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    // Note: Bearer token would go here in full prod
                }
            });
            setUploadStatus('success');
            setTimeout(() => {
                setAudioBlob(null);
                setUploadStatus('');
                setRecordingTime(0);
            }, 3000);
        } catch (err) {
            console.error(err);
            setUploadStatus('error');
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

            <main className="max-w-4xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
                    <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Intake Dashboard</h1>
                    <p className="mt-2 text-slate-500">Record patient complaints and initiate AI triage analysis.</p>
                </motion.div>

                <div className="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
                    <div className="grid grid-cols-1 md:grid-cols-2">
                        {/* Left Panel: Patient Details */}
                        <div className="p-8 border-b md:border-b-0 md:border-r border-slate-100 bg-slate-50/50">
                            <h3 className="text-lg font-semibold text-slate-800 mb-6 flex items-center gap-2">
                                <Users size={20} className="text-teal-600" />
                                Patient Identification
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Patient ID / QR</label>
                                    <input
                                        type="text"
                                        value={patientId}
                                        onChange={(e) => setPatientId(e.target.value)}
                                        className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                                        placeholder="Scan QR or Enter ID"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Spoken Language</label>
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

                                <div className="mt-8 p-4 bg-blue-50/50 border border-blue-100 rounded-xl">
                                    <h4 className="text-xs font-bold text-blue-800 uppercase tracking-wider mb-2">Instructions</h4>
                                    <p className="text-sm text-blue-600 leading-relaxed">Ensure the patient speaks clearly into the microphone. AI models run locally ensuring privacy.</p>
                                </div>
                            </div>
                        </div>

                        {/* Right Panel: Audio Intake */}
                        <div className="p-8 flex flex-col justify-center items-center">

                            <div className="text-center mb-8">
                                <div className={`text-4xl font-mono mb-2 ${isRecording ? 'text-red-500' : 'text-slate-300'}`}>
                                    {formatTime(recordingTime)}
                                </div>
                                <p className="text-sm text-slate-500">
                                    {isRecording ? "Recording in progress..." : "Ready to record."}
                                </p>
                            </div>

                            <div className="flex gap-4 mb-8">
                                {!isRecording ? (
                                    <button
                                        onClick={startRecording}
                                        className="h-20 w-20 rounded-full bg-slate-100 flex items-center justify-center text-teal-600 hover:bg-teal-50 hover:text-teal-700 border-2 border-slate-200 hover:border-teal-200 transition-all active:scale-95 shadow-sm"
                                    >
                                        <Mic size={32} />
                                    </button>
                                ) : (
                                    <button
                                        onClick={stopRecording}
                                        className="h-20 w-20 rounded-full bg-red-50 flex items-center justify-center text-red-600 border-2 border-red-200 animate-pulse active:scale-95 shadow-sm"
                                    >
                                        <Square size={28} className="fill-current" />
                                    </button>
                                )}
                            </div>

                            {audioBlob && !isRecording && (
                                <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="w-full">
                                    <button
                                        onClick={submitTriage}
                                        disabled={uploadStatus === 'uploading'}
                                        className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg transition-all
                                    ${uploadStatus === 'success' ? 'bg-green-500 text-white shadow-green-200' :
                                                uploadStatus === 'error' ? 'bg-red-500 text-white shadow-red-200' :
                                                    'bg-teal-600 text-white hover:bg-teal-700 shadow-teal-200'}
                                `}
                                    >
                                        {uploadStatus === 'uploading' && <><Activity className="animate-spin" /> Analyzing Audio...</>}
                                        {uploadStatus === 'success' && <>Sent to Triage Queue!</>}
                                        {uploadStatus === 'error' && <>Upload Failed. Retry.</>}
                                        {uploadStatus === '' && <><UploadCloud /> Process Intake</>}
                                    </button>
                                </motion.div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
