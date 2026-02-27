"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FileText,
    Database,
    ChevronRight,
    Search,
    Activity,
    ClipboardCheck,
    Clock,
    User,
    ArrowLeft,
    Share2,
    CheckCircle2
} from 'lucide-react';
import Link from 'next/link';

export default function EHRDashboard() {
    const [records, setRecords] = useState<any[]>([]);
    const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchRecords();
        const interval = setInterval(fetchRecords, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchRecords = async () => {
        setIsLoading(true);
        try {
            const res = await axios.get('http://localhost:8000/ehr/records');
            setRecords(res.data);
            if (res.data.length > 0 && !selectedRecord) {
                setSelectedRecord(res.data[0]);
            }
        } catch (e) {
            console.error("Error fetching EHR records:", e);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#F8FAFC]">
            {/* Header */}
            <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
                <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/doctor" className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-500">
                            <ArrowLeft size={20} />
                        </Link>
                        <div className="h-6 w-[1px] bg-slate-200" />
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-teal-900/10">
                                <Database size={18} />
                            </div>
                            <div>
                                <h1 className="text-lg font-bold text-slate-900 leading-tight">Mock EHR System</h1>
                                <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Interoperability Verification Portal</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2 text-xs font-medium text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                            FHIR R4 Endpoint Active
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-[1600px] mx-auto p-6 flex gap-6 h-[calc(100vh-64px)]">
                {/* Sidebar Queue */}
                <div className="w-80 flex flex-col gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                        <input
                            type="text"
                            placeholder="Search clinical records..."
                            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-xl bg-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                        />
                    </div>

                    <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                        <div className="space-y-2">
                            {isLoading ? (
                                [1, 2, 3].map(i => (
                                    <div key={i} className="h-24 bg-white rounded-xl border border-slate-100 animate-pulse" />
                                ))
                            ) : records.length === 0 ? (
                                <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 border-dashed">
                                    <FileText className="mx-auto text-slate-300 mb-2" size={32} />
                                    <p className="text-sm font-medium text-slate-500">No records exported yet</p>
                                </div>
                            ) : (
                                records.map((record, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => setSelectedRecord(record)}
                                        className={`w-full p-4 rounded-xl border text-left transition-all ${selectedRecord?.patient_id === record.patient_id
                                            ? 'bg-teal-50 border-teal-200 ring-1 ring-teal-200 shadow-lg shadow-teal-900/5'
                                            : 'bg-white border-slate-200 hover:border-teal-200 hover:shadow-md'
                                            }`}
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <span className="text-[10px] font-bold text-teal-600 bg-teal-100 px-2 py-0.5 rounded uppercase tracking-wider">FHIR R4</span>
                                            <span className="text-[10px] text-slate-400 font-medium">{new Date(record.exported_at).toLocaleTimeString()}</span>
                                        </div>
                                        <h3 className="text-sm font-bold text-slate-900 mb-1">Patient: {record.patient_id}</h3>
                                        <div className="flex items-center gap-2 text-[11px] text-slate-500 font-medium">
                                            <Clock size={12} /> {new Date(record.exported_at).toLocaleDateString()}
                                        </div>
                                    </button>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 bg-white rounded-2x border border-slate-200 shadow-sm overflow-hidden flex flex-col">
                    {selectedRecord ? (
                        <>
                            <div className="p-6 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-white rounded-xl border border-slate-200 flex items-center justify-center text-teal-600 shadow-sm">
                                        <User size={24} />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold text-slate-900">FHIR Clinical Document Bundle</h2>
                                        <p className="text-sm text-slate-500 font-medium">Record ID: {selectedRecord.fhir_bundle.id}</p>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-all">
                                        <Share2 size={20} />
                                    </button>
                                    <button className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-bold hover:bg-teal-700 transition-all flex items-center gap-2">
                                        <CheckCircle2 size={16} /> Verified R4 Format
                                    </button>
                                </div>
                            </div>

                            <div className="flex-1 flex overflow-hidden">
                                {/* Details Pane */}
                                <div className="w-1/2 p-6 border-r border-slate-100 overflow-y-auto overflow-x-hidden custom-scrollbar">
                                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Clinical Content (Parsed)</h3>

                                    <div className="space-y-6">
                                        <section>
                                            <h4 className="flex items-center gap-2 text-sm font-bold text-slate-800 mb-3 bg-slate-50 p-2 rounded-lg border border-slate-100">
                                                <ClipboardCheck size={16} className="text-teal-600" /> Composition (SOAP Note)
                                            </h4>
                                            <div className="pl-2 space-y-4">
                                                {selectedRecord.fhir_bundle.entry
                                                    ?.find((e: any) => e.resource.resourceType === 'Composition')
                                                    ?.resource?.section?.map((sec: any, i: number) => (
                                                        <div key={i} className="border-l-2 border-slate-100 pl-4 py-1">
                                                            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">{sec.title}</p>
                                                            <p className="text-sm text-slate-600 leading-relaxed font-medium">
                                                                {sec.text?.div?.replace(/<[^>]*>?/gm, '') || "No content available"}
                                                            </p>
                                                        </div>
                                                    )) || (
                                                        <p className="text-xs text-slate-400 italic">No clinical sections found in this bundle.</p>
                                                    )}
                                            </div>
                                        </section>

                                        <section>
                                            <h4 className="flex items-center gap-2 text-sm font-bold text-slate-800 mb-3 bg-slate-50 p-2 rounded-lg border border-slate-100">
                                                <Activity size={16} className="text-teal-600" /> Observations (Vitals)
                                            </h4>
                                            <div className="grid grid-cols-2 gap-3">
                                                {selectedRecord.fhir_bundle.entry
                                                    ?.filter((e: any) => e.resource.resourceType === 'Observation')
                                                    .map((obs: any, i: number) => (
                                                        <div key={i} className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
                                                            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">
                                                                {obs.resource.code?.coding?.[0]?.display || "Unknown Observation"}
                                                            </p>
                                                            <p className="text-lg font-bold text-slate-900">
                                                                {obs.resource.valueQuantity
                                                                    ? `${obs.resource.valueQuantity.value} ${obs.resource.valueQuantity.unit || ""}`
                                                                    : obs.resource.component
                                                                        ? `${obs.resource.component[0]?.valueQuantity?.value || "?"}/${obs.resource.component[1]?.valueQuantity?.value || "?"} mmHg`
                                                                        : 'N/A'
                                                                }
                                                            </p>
                                                        </div>
                                                    ))}
                                            </div>
                                        </section>
                                    </div>
                                </div>

                                {/* Raw JSON Pane */}
                                <div className="w-1/2 bg-[#0F172A] p-6 overflow-y-auto custom-scrollbar">
                                    <div className="flex justify-between items-center mb-4">
                                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                            <Database size={14} /> FHIR R4 Bundle JSON
                                        </h3>
                                        <button
                                            onClick={() => navigator.clipboard.writeText(JSON.stringify(selectedRecord.fhir_bundle, null, 2))}
                                            className="text-[10px] font-bold text-slate-400 hover:text-white transition-colors"
                                        >
                                            COPY JSON
                                        </button>
                                    </div>
                                    <pre className="text-[11px] font-mono text-teal-400 leading-relaxed">
                                        {JSON.stringify(selectedRecord.fhir_bundle, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center bg-slate-50/50 p-12 text-center">
                            <div className="w-20 h-20 bg-white rounded-3xl shadow-xl shadow-slate-200 border border-slate-100 flex items-center justify-center text-slate-300 mb-6">
                                <FileText size={40} />
                            </div>
                            <h2 className="text-xl font-bold text-slate-900 mb-2">Select a Clinical Record</h2>
                            <p className="text-sm text-slate-500 max-w-sm">
                                Once a triage record is finalized and moved to EHR, it will appear here in standardized FHIR R4 Resource format.
                            </p>
                        </div>
                    )}
                </div>
            </main>

            <style jsx global>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #E2E8F0;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #CBD5E1;
                }
                @font-face {
                    font-family: 'Inter';
                    src: url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                }
            `}</style>
        </div>
    );
}
