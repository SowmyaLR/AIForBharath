"use client"
import { useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.push('/login');
      } else {
        if (user.role === 'receptionist') router.push('/receptionist');
        else if (user.role === 'nurse') router.push('/nurse');
        else if (user.role === 'doctor') router.push('/doctor');
      }
    }
  }, [user, isLoading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="animate-pulse flex flex-col items-center">
        <div className="h-12 w-12 bg-teal-200 rounded-full mb-4"></div>
        <div className="text-teal-600 font-medium tracking-wide">Routing...</div>
      </div>
    </div>
  );
}
