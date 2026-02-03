"use client";

import { useState, useRef } from "react";
import Link from "next/link";

export default function PatientPage() {
    const [recording, setRecording] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [messages, setMessages] = useState<{ role: 'ai' | 'user', content: string }[]>([
        { role: 'ai', content: "Hello. I am your AI triage assistant. Please describe your symptoms. You can speak freely." }
    ]);

    // Refs for media recording
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    const [patientId, setPatientId] = useState("");

    const handleToggleRecord = async () => {
        if (!recording) {
            if (!patientId.trim()) {
                alert("Please enter a Patient ID first.");
                return;
            }
            // Start Recording
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const mediaRecorder = new MediaRecorder(stream);
                mediaRecorderRef.current = mediaRecorder;
                audioChunksRef.current = [];

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunksRef.current.push(event.data);
                    }
                };

                mediaRecorder.start();
                setRecording(true);
            } catch (err) {
                console.error("Error accessing microphone:", err);
                alert("Could not access microphone. Please check permissions.");
            }
        } else {
            // Stop Recording
            if (mediaRecorderRef.current) {
                mediaRecorderRef.current.stop();
                setRecording(false);
                setProcessing(true);

                mediaRecorderRef.current.onstop = async () => {
                    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

                    // Create FormData
                    const formData = new FormData();
                    formData.append('audio_file', audioBlob, 'recording.webm');
                    formData.append('patient_id', patientId);

                    try {
                        const response = await fetch('http://127.0.0.1:8000/api/triage', {
                            method: 'POST',
                            body: formData,
                        });

                        if (response.ok) {
                            const data = await response.json();
                            setMessages(prev => [
                                ...prev,
                                { role: 'user', content: "Audio sent. (Transcript: " + data.transcript + ")" },
                                { role: 'ai', content: "I've analyzed your symptoms. " + data.risk_data.interpretation + " A SOAP note has been generated for your clinician." }
                            ]);
                            // Clear ID for next patient after short delay
                            setTimeout(() => {
                                setPatientId("");
                                setMessages([{ role: 'ai', content: "Ready for next patient. Please enter ID." }]);
                            }, 5000);
                        } else {
                            setMessages(prev => [
                                ...prev,
                                { role: 'user', content: "Error sending audio." },
                                { role: 'ai', content: "I'm having trouble reaching the server. Please try again." }
                            ]);
                        }
                    } catch (error) {
                        console.error("Upload error", error);
                        setMessages(prev => [
                            ...prev,
                            { role: 'ai', content: "Connection error. Ensure backend is running." }
                        ]);
                    } finally {
                        setProcessing(false);
                        // Stop all tracks to release mic
                        mediaRecorderRef.current?.stream.getTracks().forEach(track => track.stop());
                    }
                };
            }
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 font-[family-name:var(--font-geist-sans)] flex flex-col">
            <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-10 flex justify-between items-center bg-opacity-90 backdrop-blur-md">
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">M</div>
                    <span className="text-xl font-bold text-slate-800 tracking-tight">MedGemma</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 mr-4 bg-slate-100 rounded-lg px-3 py-1.5 border border-slate-200 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent transition-all">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">ID</span>
                        <input
                            type="text"
                            placeholder="Patient ID / MRN"
                            value={patientId}
                            onChange={(e) => setPatientId(e.target.value)}
                            className="bg-transparent border-none outline-none text-sm font-semibold text-slate-700 w-32 placeholder:font-normal placeholder:text-slate-400"
                        />
                    </div>
                    <Link href="/" className="bg-slate-100 hover:bg-slate-200 text-slate-600 px-4 py-2 rounded-full text-sm font-medium transition-colors">
                        Exit
                    </Link>
                </div>
            </header>

            <main className="flex-1 max-w-2xl w-full mx-auto p-4 md:p-6 flex flex-col">
                {/* Chat Stream */}
                <div className="flex-1 space-y-6 overflow-y-auto mb-6 pb-4">
                    {messages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.role === 'ai' ? 'justify-start' : 'justify-end'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                            <div className={`flex gap-3 max-w-[85%] ${msg.role === 'ai' ? 'flex-row' : 'flex-row-reverse'}`}>
                                {msg.role === 'ai' && (
                                    <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex-shrink-0 flex items-center justify-center text-white text-xs shadow-md">
                                        AI
                                    </div>
                                )}
                                <div className={`p-4 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed ${msg.role === 'ai'
                                    ? 'bg-white text-slate-700 border border-slate-100 rounded-tl-none'
                                    : 'bg-blue-600 text-white rounded-tr-none'
                                    }`}>
                                    {msg.content}
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Processing State - Agentic Steps */}
                    {processing && (
                        <div className="flex justify-start animate-in fade-in">
                            <div className="flex gap-3 max-w-[85%]">
                                <div className="h-8 w-8 rounded-full bg-slate-200 flex-shrink-0 animate-pulse" />
                                <div className="space-y-3">
                                    <div className="bg-white p-4 rounded-xl rounded-tl-none border border-slate-100 shadow-sm space-y-3 min-w-[280px]">
                                        <div className="flex items-center gap-3 text-sm text-slate-600">
                                            <div className="h-4 w-4 bg-emerald-500 rounded-full animate-bounce" />
                                            <span className="font-semibold">Whisper Medium Analysis...</span>
                                        </div>
                                        <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
                                            <div className="h-full bg-blue-500 w-2/3 animate-[shimmer_1.5s_infinite]" />
                                        </div>
                                        <div className="text-xs text-slate-400 pl-7">
                                            Scanning for acoustic markers & translating headers...
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Interaction Area (Fixed Bottom) */}
                <div className="bg-white p-2 rounded-3xl shadow-2xl border border-slate-100 flex items-center gap-4 relative overflow-hidden">
                    {/* Background Animation for Recording */}
                    {recording && (
                        <div className="absolute inset-0 bg-red-50 z-0 animate-pulse" />
                    )}

                    <div className="flex-1 z-10 pl-6">
                        {recording ? (
                            <div className="flex items-center gap-1 h-8">
                                {[...Array(5)].map((_, i) => (
                                    <div key={i} className="w-1 bg-red-400 rounded-full animate-[bounce_1s_infinite]" style={{ animationDelay: `${i * 0.1}s`, height: '60%' }} />
                                ))}
                                <span className="ml-3 text-red-500 font-semibold tracking-wide">Recording...</span>
                            </div>
                        ) : (
                            <span className="text-slate-400 font-medium">Tap microphone to answer...</span>
                        )}
                    </div>

                    <button
                        onClick={handleToggleRecord}
                        disabled={processing}
                        className={`z-10 h-16 w-16 rounded-2xl flex items-center justify-center transition-all duration-300 transform hover:scale-105 active:scale-95 ${recording
                            ? 'bg-red-500 shadow-lg shadow-red-200 rotate-0'
                            : 'bg-slate-900 shadow-xl shadow-slate-200 hover:bg-black'
                            } ${processing ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {recording ? (
                            <div className="h-6 w-6 bg-white rounded-md" />
                        ) : (
                            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                        )}
                    </button>
                </div>
                <div className="text-center mt-4 text-xs text-slate-400 font-medium">
                    Powered by <span className="text-slate-600">Google MedGemma</span> & <span className="text-slate-600">HeAR</span>
                </div>
            </main>
        </div>
    );
}
