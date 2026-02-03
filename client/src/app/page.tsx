import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 flexflex-col items-center justify-center p-8 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-8 row-start-2 items-center text-center max-w-2xl mx-auto mt-20">
        <h1 className="text-4xl md:text-6xl font-bold text-slate-800 tracking-tight">
          MedGemma <span className="text-blue-600">Tele-Triage</span>
        </h1>
        <p className="text-lg text-slate-600">
          AI-powered intake agent connecting patients with effective care.
          Powered by MedASR, HeAR, and MedGemma.
        </p>

        <div className="flex gap-4 items-center flex-col sm:flex-row mt-8">
          <Link
            href="/patient"
            className="rounded-xl border border-transparent transition-colors flex items-center justify-center bg-blue-600 text-white gap-2 hover:bg-blue-700 text-lg h-14 px-8 shadow-lg hover:shadow-xl"
          >
            I am a Patient
          </Link>
          <Link
            href="/doctor"
            className="rounded-xl border border-slate-300 transition-colors flex items-center justify-center bg-white text-slate-700 gap-2 hover:bg-slate-100 text-lg h-14 px-8 shadow-sm hover:shadow-md"
          >
            I am a Clinician
          </Link>
        </div>
      </main>

      <footer className="mt-20 text-slate-400 text-sm md:absolute md:bottom-8">
        Built for MedGemma Impact Challenge 2026
      </footer>
    </div>
  );
}
