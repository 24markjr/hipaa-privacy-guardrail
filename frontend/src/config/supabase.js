import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

console.log("URL:", supabaseUrl);
console.log("KEY START:", supabaseAnonKey?.slice(0, 20));

const supabase = createClient(
  supabaseUrl,
  supabaseAnonKey
);

window.supabase = supabase;

export default supabase;