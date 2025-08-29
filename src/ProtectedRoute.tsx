// src/ProtectedRoute.tsx
import { ReactNode, useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { supabase } from '@/supabaseClient';

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const [checking, setChecking] = useState(true);
  const [ok, setOk] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const { data } = await supabase.auth.getSession();
      if (!mounted) return;
      setOk(!!data.session);
      setChecking(false);
    })();
    const { data: sub } = supabase.auth.onAuthStateChange((_e, s) => setOk(!!s));
    return () => sub.subscription.unsubscribe();
  }, []);

  if (checking) return null; // or a spinner
  return ok ? <>{children}</> : <Navigate to="/" replace />;
}
