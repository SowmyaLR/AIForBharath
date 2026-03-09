"use client"
import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit, Zap, Moon } from 'lucide-react';

type AiStatus = 'ready' | 'warming_up' | 'sleeping' | 'unavailable' | 'loading';

interface StatusConfig {
    label: string;
    icon: React.ReactNode;
    bgClass: string;
    textClass: string;
    dotClass: string;
    pulse: boolean;
}

const STATUS_CONFIG: Record<AiStatus, StatusConfig> = {
    loading: {
        label: 'AI Checking...',
        icon: <BrainCircuit size={13} />,
        bgClass: 'bg-slate-100',
        textClass: 'text-slate-500',
        dotClass: 'bg-slate-400',
        pulse: false,
    },
    ready: {
        label: 'AI Ready',
        icon: <BrainCircuit size={13} />,
        bgClass: 'bg-green-50 border border-green-200',
        textClass: 'text-green-700',
        dotClass: 'bg-green-500',
        pulse: false,
    },
    warming_up: {
        label: 'AI Warming Up',
        icon: <Zap size={13} />,
        bgClass: 'bg-amber-50 border border-amber-200',
        textClass: 'text-amber-700',
        dotClass: 'bg-amber-500',
        pulse: true,
    },
    sleeping: {
        label: 'AI Sleeping',
        icon: <Moon size={13} />,
        bgClass: 'bg-blue-50 border border-blue-200',
        textClass: 'text-blue-600',
        dotClass: 'bg-blue-400',
        pulse: false,
    },
    unavailable: {
        label: 'AI Unavailable',
        icon: <BrainCircuit size={13} />,
        bgClass: 'bg-slate-100',
        textClass: 'text-slate-500',
        dotClass: 'bg-slate-400',
        pulse: false,
    },
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Poll intervals:
// warming_up → 2 min (GPU takes 3-4 min to boot, no point polling every 15s)
// ready      → 5 min (just a keep-alive to notice if GPU scales down)
const POLL_INTERVAL_WARMING = 2 * 60 * 1000;  // 2 minutes
const POLL_INTERVAL_READY = 5 * 60 * 1000;  // 5 minutes

export function AiStatusBadge() {
    const [status, setStatus] = useState<AiStatus>('loading');
    const [tooltip, setTooltip] = useState<string>('');
    const [showTooltip, setShowTooltip] = useState(false);
    const statusRef = useRef<AiStatus>('loading'); // track status without re-creating effect
    const mountedRef = useRef(false);              // guard against React StrictMode double-mount

    const fetchStatus = useCallback(async (isWarmup = false) => {
        try {
            const url = `${API_URL}/ai/status${isWarmup ? '?warmup=true' : ''}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error('fetch failed');
            const data = await res.json();
            setStatus(data.status as AiStatus);
            statusRef.current = data.status as AiStatus;
            setTooltip(data.message || '');
        } catch {
            setStatus('unavailable');
            statusRef.current = 'unavailable';
        }
    }, []);

    useEffect(() => {
        // React StrictMode in dev double-mounts components.
        // This guard ensures we only set up ONE interval.
        if (mountedRef.current) return;
        mountedRef.current = true;

        // On page load: fire warmup=true ONCE (backend debounces within 5 min)
        fetchStatus(true);

        let interval: NodeJS.Timeout;

        const scheduleNext = () => {
            clearInterval(interval);
            const current = statusRef.current;
            // Don't poll at all if unavailable or still loading
            if (current === 'unavailable') return;
            const delay = current === 'ready' ? POLL_INTERVAL_READY : POLL_INTERVAL_WARMING;
            interval = setInterval(() => {
                if (!document.hidden) {         // skip if tab is hidden
                    fetchStatus(false).then(scheduleNext); // re-schedule after each call
                }
            }, delay);
        };

        // Schedule first poll after initial warmup fetch
        fetchStatus(true).then(scheduleNext);

        // When tab becomes visible again, fetch immediately (no warmup)
        const handleVisible = () => {
            if (!document.hidden) fetchStatus(false).then(scheduleNext);
        };
        document.addEventListener('visibilitychange', handleVisible);

        return () => {
            clearInterval(interval);
            document.removeEventListener('visibilitychange', handleVisible);
            mountedRef.current = false;
        };
    }, [fetchStatus]);

    const config = STATUS_CONFIG[status];

    return (
        <div className="relative flex items-center">
            <motion.div
                layout
                title={tooltip}
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold cursor-default select-none transition-all duration-300 ${config.bgClass} ${config.textClass}`}
            >
                {/* Status dot */}
                <span className="relative flex h-2 w-2 flex-shrink-0">
                    {config.pulse && (
                        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${config.dotClass}`} />
                    )}
                    <span className={`relative inline-flex rounded-full h-2 w-2 ${config.dotClass}`} />
                </span>

                {config.icon}
                {config.label}
            </motion.div>

            {/* Tooltip */}
            <AnimatePresence>
                {showTooltip && tooltip && (
                    <motion.div
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 4 }}
                        className="absolute top-full mt-2 left-1/2 -translate-x-1/2 z-50 w-56 bg-slate-900 text-white text-[11px] rounded-lg px-3 py-2 shadow-xl pointer-events-none text-center leading-relaxed"
                    >
                        {tooltip}
                        <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-900 rotate-45" />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
