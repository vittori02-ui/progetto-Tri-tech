// ============================================================
// HomePages.tsx - Home page con dati reali dall'API
// ============================================================
import { useState, useEffect } from "react";
import {
  Search,
  Bell,
  MessageCircle,
  MapPin,
  Star,
  ArrowRight,
} from "lucide-react";
import { useNavigate } from "react-router";
import { api } from "@/lib/api";
import type { AxiosError } from "axios";

// ============================================================
// Tipi corrispondenti ai modelli Pydantic del backend
// ============================================================

/** Skill associata a un utente (UserSkillResponse) */
type UserSkillItem = {
  id: number;
  skill_id: number;
  skill_name: string;
  level: string;
  user_id: number;
};

/** Utente dal search (UserSearchResponse in models.py) */
type UserSearchItem = {
  id: number;
  name: string;
  bio: string;
  location: string;
  offered_skills: UserSkillItem[];
  wanted_skills: UserSkillItem[];
};

/** Statistiche dashboard (DashboardStats) */
type StatsData = {
  total_users: number;
  total_skills: number;
  total_matches: number;
};

export default function HomePages() {
  const navigate = useNavigate();
  const [utenti, setUtenti] = useState<UserSearchItem[]>([]);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ============================================================
  // useEffect: carica utenti e statistiche al mount
  // ============================================================
  useEffect(() => {
    loadHomeData();
  }, []);

  // ============================================================
  // Funzione: carica dati dalla API
  // ============================================================
  async function loadHomeData() {
    setLoading(true);
    setError("");

    try {
      // Carica utenti (ricerca vuota = tutti) e statistiche in parallelo
      const [usersRes, statsRes] = await Promise.all([
        api.get<UserSearchItem[]>("/users/search?q="),
        api.get<StatsData>("/users/stats"),
      ]);

      setUtenti(usersRes.data);
      setStats(statsRes.data);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      if (axiosErr.response?.status === 401) {
        // Token scaduto o non valido
        localStorage.removeItem("auth_token");
        navigate("/login");
      } else {
        setError("Impossibile caricare i dati. Verifica che il backend sia avviato.");
      }
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // Schermata di caricamento
  // ============================================================
  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-10 w-10 border-4 border-orange-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-zinc-400">Caricamento home...</p>
        </div>
      </div>
    );
  }

  // ============================================================
  // Schermata di errore
  // ============================================================
  if (error) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={loadHomeData}
            className="bg-orange-500 text-black px-6 py-2 rounded-xl font-bold hover:bg-orange-600"
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* NAVBAR */}
      <header className="border-b border-zinc-800 bg-zinc-950 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          {/* LOGO */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-orange-500 flex items-center justify-center font-bold text-black">
              S
            </div>
            <div>
              <h1 className="text-xl font-bold text-orange-500">SkillSwap</h1>
              <p className="text-xs text-zinc-500">Scambio competenze</p>
            </div>
          </div>

          {/* SEARCH */}
          <div className="hidden md:flex flex-1 max-w-2xl relative">
            <Search
              size={18}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500"
            />
            <input
              type="text"
              placeholder="Cerca skill, utenti o tecnologie..."
              className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl pl-12 pr-4 py-3 outline-none focus:border-orange-500 transition"
            />
          </div>

          {/* ACTIONS */}
          <div className="flex items-center gap-3">
            <button className="w-11 h-11 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center hover:border-orange-500 transition">
              <Bell size={18} />
            </button>
            <button className="w-11 h-11 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center hover:border-orange-500 transition">
              <MessageCircle size={18} />
            </button>
            <div className="w-11 h-11 rounded-full overflow-hidden border-2 border-orange-500">
              <img
                src="https://i.pravatar.cc/300?img=12"
                alt="profile"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </header>

      {/* HERO CON STATS REALI */}
      <section className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* LEFT */}
          <div className="bg-zinc-950 border border-orange-500 rounded-3xl p-8 shadow-[0_0_30px_rgba(249,115,22,0.12)]">
            <p className="text-orange-500 text-sm font-medium mb-4">
              Marketplace interno competenze
            </p>
            <h2 className="text-5xl font-bold leading-tight">
              Impara.<br />Insegna.<br />Connettiti.
            </h2>
            <p className="text-zinc-400 mt-6 max-w-xl leading-relaxed">
              Trova colleghi compatibili con le tue skill, organizza
              sessioni di scambio 1:1 e migliora le tue competenze.
            </p>
            <div className="flex gap-4 mt-8">
              <button className="px-6 py-3 bg-orange-500 hover:bg-orange-600 rounded-2xl font-medium transition">
                Inizia ora
              </button>
              <button className="px-6 py-3 bg-zinc-900 border border-zinc-800 hover:border-orange-500 rounded-2xl font-medium transition">
                Cerca utenti
              </button>
            </div>
          </div>

          {/* RIGHT STATS (dati reali dall'API) */}
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-zinc-950 border border-zinc-800 rounded-3xl p-6">
              <p className="text-zinc-500 text-sm">Utenti attivi</p>
              <h3 className="text-4xl font-bold mt-3 text-orange-500">
                {stats?.total_users ?? 0}
              </h3>
            </div>
            <div className="bg-zinc-950 border border-zinc-800 rounded-3xl p-6">
              <p className="text-zinc-500 text-sm">Match completati</p>
              <h3 className="text-4xl font-bold mt-3 text-orange-500">
                {stats?.total_matches ?? 0}
              </h3>
            </div>
            <div className="bg-zinc-950 border border-zinc-800 rounded-3xl p-6">
              <p className="text-zinc-500 text-sm">Skill disponibili</p>
              <h3 className="text-4xl font-bold mt-3 text-orange-500">
                {stats?.total_skills ?? 0}
              </h3>
            </div>
            <div className="bg-zinc-950 border border-zinc-800 rounded-3xl p-6">
              <p className="text-zinc-500 text-sm">Rating medio</p>
              <h3 className="text-4xl font-bold mt-3 text-orange-500">4.9</h3>
            </div>
          </div>
        </div>
      </section>

      {/* USER SECTION (dati reali dall'API /users/search) */}
      <section className="max-w-7xl mx-auto px-6 pb-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h3 className="text-3xl font-bold">Match consigliati</h3>
            <p className="text-zinc-500 mt-1">Colleghi compatibili con le tue skill</p>
          </div>
          <button className="flex items-center gap-2 text-orange-500 hover:text-orange-400 transition">
            Vedi tutti
            <ArrowRight size={16} />
          </button>
        </div>

        {/* CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {utenti.length === 0 ? (
            <p className="text-zinc-500 col-span-full text-center py-10">
              Nessun utente trovato. Invita i tuoi colleghi a registrarsi!
            </p>
          ) : (
            utenti.map((utente) => (
              <div
                key={utente.id}
                className="bg-zinc-950 border border-zinc-800 rounded-3xl p-6 hover:border-orange-500 transition duration-300"
              >
                {/* TOP */}
                <div className="flex items-start gap-4">
                  <div className="w-20 h-20 rounded-full overflow-hidden border-2 border-orange-500">
                    <img
                      src="https://i.pravatar.cc/300?img=12"
                      alt={utente.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1">
                    <h4 className="text-xl font-semibold">{utente.name}</h4>
                    <div className="flex items-center gap-2 text-zinc-400 text-sm mt-1">
                      <MapPin size={14} className="text-orange-500" />
                      <span>{utente.location || "Localita non specificata"}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <div className="flex items-center gap-1 text-yellow-400 text-sm">
                        <Star size={14} fill="currentColor" />4.8
                      </div>
                    </div>
                  </div>
                </div>

                {/* OFFERTE (dall'API) */}
                <div className="mt-6">
                  <p className="text-sm text-zinc-500 mb-3">Skill offerte</p>
                  <div className="flex flex-wrap gap-2">
                    {utente.offered_skills.length === 0 ? (
                      <span className="text-xs text-zinc-600">Nessuna</span>
                    ) : (
                      utente.offered_skills.map((skill) => (
                        <span
                          key={skill.id}
                          className="px-3 py-1 rounded-full bg-green-900/30 text-green-400 text-xs"
                        >
                          {skill.skill_name}
                        </span>
                      ))
                    )}
                  </div>
                </div>

                {/* CERCATE (dall'API) */}
                <div className="mt-5">
                  <p className="text-sm text-zinc-500 mb-3">Skill cercate</p>
                  <div className="flex flex-wrap gap-2">
                    {utente.wanted_skills.length === 0 ? (
                      <span className="text-xs text-zinc-600">Nessuna</span>
                    ) : (
                      utente.wanted_skills.map((skill) => (
                        <span
                          key={skill.id}
                          className="px-3 py-1 rounded-full bg-blue-900/30 text-blue-400 text-xs"
                        >
                          {skill.skill_name}
                        </span>
                      ))
                    )}
                  </div>
                </div>

                {/* BUTTON: naviga al profilo pubblico */}
                <button
                  onClick={() => navigate(`/public?id=${utente.id}`)}
                  className="w-full mt-7 py-3 bg-orange-500 hover:bg-orange-600 rounded-2xl font-medium transition"
                >
                  Visualizza profilo
                </button>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
