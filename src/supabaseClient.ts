// src/supabaseClient.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('[Supabase] Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY');
  // Return a dummy client so the app doesn't crash on public pages
  // You can also gate any auth-only code behind checks for these vars.
}

export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    })
  : (null as any); // guard usages accordingly

export const getDashboardRedirect = () =>
  (window.location.origin.includes('localhost')
    ? 'http://localhost:5173/dashboard'
    : 'https://taulayer.com/dashboard');
