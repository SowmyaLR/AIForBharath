"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";

const MOCK_CASES = [
    {
        id: "case-102",
        patientName: "John Doe",
        timestamp: "10:42 AM",
        riskScore: 0.15,
        chiefComplaint: "Persistent dry cough",
        soapSummary: "S: Dry cough x3 days, no fever. O: HeAR risk 0.15 (low). A: Allergic rhinitis vs viral URI. P: antihistamines, obs."
    },
    {
        id: "case-103",
        patientName: "Jane Smith",
        timestamp: "10:55 AM",
        riskScore: 0.82,
        chiefComplaint: "Productive cough, fever",
        soapSummary: "S: Productive cough, fever 38.5C. O: HeAR risk 0.82 (High). A: R/O Pneumonia. P: CXR, CBC, antibiotics pending metrics."
    }
];

export default function DoctorPage() {
    const [cases, setCases] = useState<any[]>([]);
    const [expandedCase, setExpandedCase] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'queue' | 'archive' | 'analytics'>('queue');

    // Archive State
    const [archivedCases, setArchivedCases] = useState<any[]>([]);
    const archivedIdsRef = useRef<Set<string>>(new Set());

    // Edit Mode State
    const [editingCaseId, setEditingCaseId] = useState<string | null>(null);
    const [editedContent, setEditedContent] = useState<string>("");

    // Start Polling
    useEffect(() => {
        const fetchQueue = async () => {
            try {
                const res = await fetch("http://127.00.1:8000/api/queue");
                if (res.ok) {
                    const data = await res.json();

                    // Filter out any cases that have been archived locally
                    // We use the Ref to get the latest set without needing to restart the interval
                    const activeQueue = data.filter((c: any) => !archivedIdsRef.current.has(c.id));

                    setCases(prev => {
                        // Simple equality check to prevent re-renders if data hasn't changed
                        if (JSON.stringify(prev) === JSON.stringify(activeQueue)) return prev;
                        return activeQueue;
                    });
                }
            } catch (error) {
                console.error("Failed to fetch queue", error);
            }
        };

        fetchQueue();
        const interval = setInterval(fetchQueue, 5000);
        return () => clearInterval(interval);
    }, []); // Empty dependency array = stable interval!

    const handleApprove = (caseId: string) => {
        const caseToApprove = cases.find(c => c.id === caseId);

        if (caseToApprove) {
            // 1. Add to Archive State (Display)
            setArchivedCases(prev => [caseToApprove, ...prev]);

            // 2. Add to ID Ref (Filtering)
            archivedIdsRef.current.add(caseId);

            // 3. Remove from Active Queue (Immediate UI update)
            setCases(prev => prev.filter(c => c.id !== caseId));

            setExpandedCase(null);
            // alert(`Case ${caseId} Approved & E-Signed.`); // Optional: Comments out alert for smoother flow
        }
    };

    const startEditing = (c: any) => {
        setEditingCaseId(c.id);
        setEditedContent(c.soapSummary);
    };

    const saveEdit = (caseId: string) => {
        setCases(prev => prev.map(c => {
            if (c.id === caseId) {
                return { ...c, soapSummary: editedContent };
            }
            return c;
        }));
        setEditingCaseId(null);
    };

    return (
        <div className="min-h-screen bg-slate-50 font-[family-name:var(--font-geist-sans)] flex">
            {/* Sidebar */}
            <aside className="w-72 bg-slate-900 text-white flex flex-col hidden md:flex shrink-0">
                <div className="p-8">
                    <h1 className="text-2xl font-bold tracking-tighter flex items-center gap-2">
                        <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">M</div>
                        MedGemma
                    </h1>
                    <p className="text-slate-500 text-xs mt-2 uppercase tracking-widest pl-1">Clinician Portal</p>
                </div>
                <nav className="flex-1 px-4 space-y-2">
                    <button
                        onClick={() => setActiveTab('queue')}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'queue' ? 'bg-blue-600/20 text-blue-300 border-l-2 border-blue-500' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}
                    >
                        <span className="font-semibold">Incoming Triage</span>
                        {cases.length > 0 && <span className="bg-blue-600 text-white px-2 py-0.5 rounded-full text-xs ml-auto shadow-sm shadow-blue-900/50">{cases.length}</span>}
                    </button>
                    <button
                        onClick={() => setActiveTab('archive')}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'archive' ? 'bg-blue-600/20 text-blue-300 border-l-2 border-blue-500' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}
                    >
                        <span>Patient Archive</span>
                        <span className="text-xs bg-slate-800 px-2 py-0.5 rounded-full ml-auto">{archivedCases.length}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('analytics')}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'analytics' ? 'bg-blue-600/20 text-blue-300 border-l-2 border-blue-500' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}
                    >
                        <span>Analytics</span>
                    </button>
                </nav>
                <div className="p-6 border-t border-slate-800">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-gradient-to-tr from-emerald-400 to-cyan-500 border-2 border-slate-900" />
                        <div>
                            <div className="text-sm font-bold text-slate-200">Dr. Sarah Connor</div>
                            <div className="text-xs text-slate-500">Chief Resident</div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Area */}
            <main className="flex-1 flex flex-col overflow-y-auto h-screen relative">
                <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 py-6 sticky top-0 z-20 flex justify-between items-end">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-800 tracking-tight">
                            {activeTab === 'queue' && "Triage Dashboard"}
                            {activeTab === 'archive' && "Patient Archive"}
                            {activeTab === 'analytics' && "Population Health"}
                        </h2>
                        <p className="text-slate-500 text-sm mt-1">Real-time analysis from MedGemma Agent</p>
                    </div>
                    <div className="flex gap-3">
                        <div className="px-4 py-2 bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-100 text-sm font-medium flex items-center gap-2">
                            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                            System Active
                        </div>
                    </div>
                </header>

                <div className="p-6 md:p-10 space-y-8 max-w-5xl mx-auto w-full">
                    {/* Render Content Based on Active Tab */}
                    {activeTab === 'analytics' && (
                        <div className="bg-white p-12 rounded-2xl border-2 border-dashed border-slate-200 text-center">
                            <div className="text-4xl mb-4">📊</div>
                            <h3 className="text-xl font-bold text-slate-700">Analytics Module</h3>
                            <p className="text-slate-500 mt-2">Population health trends and HeAR risk maps would appear here.</p>
                        </div>
                    )}

                    {activeTab === 'archive' && (
                        <div className="space-y-4">
                            {archivedCases.length === 0 ? (
                                <div className="p-12 text-center text-slate-500">No archived cases yet. Approve a case to see it here.</div>
                            ) : (
                                archivedCases.map((c: any) => (
                                    <div key={c.id} className="bg-slate-50 p-6 rounded-xl border border-slate-200 opacity-90 hover:opacity-100 transition-opacity">
                                        <div className="flex justify-between items-start">
                                            <div className="flex gap-4">
                                                <div className="h-10 w-10 bg-emerald-100 text-emerald-700 rounded-lg flex items-center justify-center font-bold">
                                                    {c.userInitials || "PT"}
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-bold text-slate-700">{c.patientName}</span>
                                                        <span className="text-[10px] font-bold bg-emerald-600 text-white px-2 py-0.5 rounded tracking-wide">E-SIGNED</span>
                                                    </div>
                                                    <p className="text-xs text-slate-400 mt-1">ID: {c.id} • {c.timestamp}</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="mt-4 bg-slate-50 p-3 rounded-lg border border-slate-100">
                                            <p className="text-sm text-slate-600 font-mono whitespace-pre-wrap">{c.soapSummary}</p>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === 'queue' && (
                        <>
                            {/* Metrics Row */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-2xl shadow-lg shadow-blue-200 text-white relative overflow-hidden group">
                                    <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-white/10 rounded-full group-hover:scale-110 transition-transform" />
                                    <div className="text-blue-100 text-sm font-medium uppercase tracking-wider">Pending Action</div>
                                    <div className="text-4xl font-bold mt-2">{cases.length}</div>
                                </div>
                                <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                                    <div className="text-slate-500 text-sm font-medium uppercase tracking-wider">HeAR Risk Index</div>
                                    <div className="flex items-end gap-2 mt-2">
                                        <span className="text-4xl font-bold text-slate-800">
                                            {cases.length > 0 ? (cases.reduce((acc: number, c: any) => acc + c.riskScore, 0) / cases.length).toFixed(2) : "0.0"}
                                        </span>
                                        <span className="text-sm text-slate-400 mb-2">/ 1.0</span>
                                    </div>
                                </div>
                                <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                                    <div className="text-slate-500 text-sm font-medium uppercase tracking-wider">Wait Time</div>
                                    <div className="text-4xl font-bold text-slate-800 mt-2">
                                        &lt; 1m
                                    </div>
                                </div>
                            </div>

                            {/* Case Queue */}
                            <div className="space-y-4">
                                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest pl-1">Priority Queue</h3>

                                {cases.length === 0 && (
                                    <div className="p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50">
                                        <div className="text-slate-400 font-medium">No active cases available.</div>
                                        <div className="text-sm text-slate-300 mt-2">Waiting for new Tele-Triage inputs...</div>
                                    </div>
                                )}

                                {cases.map((c: any) => {
                                    const isExpanded = expandedCase === c.id;
                                    const isHighRisk = c.riskScore > 0.6;
                                    const isEditing = editingCaseId === c.id;

                                    return (
                                        <div
                                            key={c.id}
                                            className={`bg-white rounded-2xl border transition-all duration-200 overflow-hidden ${isHighRisk ? 'border-amber-200 shadow-md shadow-amber-50' : 'border-slate-200 shadow-sm hover:shadow-md'
                                                }`}
                                        >
                                            {/* Card Header */}
                                            <div
                                                onClick={() => setExpandedCase(isExpanded ? null : c.id)}
                                                className="p-6 cursor-pointer flex justify-between items-start"
                                            >
                                                <div className="flex gap-4">
                                                    <div className={`h-12 w-12 rounded-xl flex items-center justify-center font-bold text-lg ${isHighRisk ? 'bg-amber-100 text-amber-600' : 'bg-blue-50 text-blue-600'
                                                        }`}>
                                                        {c.userInitials || "Pt"}
                                                    </div>
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <h4 className="font-bold text-lg text-slate-800">{c.patientName}</h4>
                                                            {isHighRisk && (
                                                                <span className="bg-amber-100 text-amber-700 text-[10px] uppercase font-bold px-2 py-0.5 rounded-full tracking-wide">High Risk</span>
                                                            )}
                                                        </div>
                                                        <p className="text-sm text-slate-500 font-medium mt-1 pr-6">{c.chiefComplaint}</p>
                                                    </div>
                                                </div>
                                                <div className="text-right shrink-0">
                                                    <div className="text-sm font-bold text-slate-700">{c.timestamp}</div>
                                                    <button className="text-xs text-blue-600 font-semibold mt-2 hover:underline">
                                                        {isExpanded ? "Collapse" : "View Assessment"}
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Expanded Details - SOAP Note */}
                                            {isExpanded && (
                                                <div className="bg-slate-50 border-t border-slate-100 px-6 py-6 animate-in slide-in-from-top-2">
                                                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                                        {/* Left Column: SOAP */}
                                                        <div className="lg:col-span-2 space-y-4">
                                                            <div className="flex items-center gap-2 border-b border-slate-200 pb-2 mb-2 justify-between">
                                                                <div className="flex items-center gap-2">
                                                                    <div className="h-5 w-5 bg-purple-600 text-white text-[10px] flex items-center justify-center font-bold rounded">AI</div>
                                                                    <h5 className="text-sm font-bold text-slate-700 uppercase tracking-wide">MedGemma SOAP Draft</h5>
                                                                </div>
                                                                {isEditing && <span className="text-xs text-amber-600 font-bold animate-pulse">EDITING MODE</span>}
                                                            </div>

                                                            {isEditing ? (
                                                                <textarea
                                                                    value={editedContent}
                                                                    onChange={(e) => setEditedContent(e.target.value)}
                                                                    className="w-full h-48 p-4 rounded-xl border-2 border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 font-mono text-sm shadow-inner"
                                                                />
                                                            ) : (
                                                                <div className="bg-white p-5 rounded-xl border border-slate-200 text-slate-600 text-sm leading-relaxed whitespace-pre-wrap font-mono shadow-sm">
                                                                    {c.soapSummary}
                                                                </div>
                                                            )}

                                                            <div className="flex gap-3 pt-2">
                                                                {isEditing ? (
                                                                    <button
                                                                        onClick={() => saveEdit(c.id)}
                                                                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors flex-1 shadow-md shadow-blue-200"
                                                                    >
                                                                        Save Changes
                                                                    </button>
                                                                ) : (
                                                                    <>
                                                                        <button
                                                                            onClick={() => handleApprove(c.id)}
                                                                            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg transition-colors flex-1 shadow-md shadow-emerald-200"
                                                                        >
                                                                            Approve & E-Sign
                                                                        </button>
                                                                        <button
                                                                            onClick={() => startEditing(c)}
                                                                            className="px-4 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-semibold rounded-lg transition-colors flex-1"
                                                                        >
                                                                            Edit Note
                                                                        </button>
                                                                    </>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {/* Right Column: Audio Analysis */}
                                                        <div className="space-y-4">
                                                            <h5 className="text-sm font-bold text-slate-700 uppercase tracking-wide">Acoustic Biomarkers (HeAR)</h5>
                                                            <div className="bg-white p-4 rounded-xl border border-slate-200">
                                                                <div className="space-y-4">
                                                                    <div>
                                                                        <div className="flex justify-between text-xs font-semibold text-slate-500 mb-1">
                                                                            <span>Risk Score</span>
                                                                            <span>{c.riskScore.toFixed(2)}</span>
                                                                        </div>
                                                                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                                                                            <div
                                                                                className={`h-full rounded-full ${c.riskScore > 0.5 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                                                                                style={{ width: `${c.riskScore * 100}%` }}
                                                                            />
                                                                        </div>
                                                                    </div>
                                                                    <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-500 leading-normal">
                                                                        Analysis indicates {c.riskScore > 0.5 ? "abnormal" : "normal"} respiratory patterns detected in audio segments.
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
