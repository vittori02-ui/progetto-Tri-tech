// ============================================================
// PaginaRicercaPage.tsx - Pagina di ricerca utenti con API reali
// ============================================================
import { useState, useEffect, useCallback } from "react";
import {
  ChevronDown,
  ChevronRight,
  FolderOpen,
  MapPin,
  Search,
  Settings,
  User,
  Wrench,
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

/** Utente dalla ricerca (UserSearchResponse) */
type UserSearchItem = {
  id: number;
  name: string;
  bio: string;
  location: string;
  offered_skills: UserSkillItem[];
  wanted_skills: UserSkillItem[];
};

// Menu laterale (statico)
const menuItems = [
  { label: "Ricerca", icon: Search, active: true },
  { label: "Richieste", icon: FolderOpen, active: false },
  { label: "Profilo", icon: User, active: false },
  { label: "Impostazioni", icon: Settings, active: false },
];

export function PaginaRicercaPage() {
  const navigate = useNavigate();

  // Stati per la ricerca
  const [profiles, setProfiles] = useState<UserSearchItem[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Stati per i filtri UI
  const [showOfferedSkills, setShowOfferedSkills] = useState(true);
  const [showSoughtSkills, setShowSoughtSkills] = useState(true);

  // ============================================================
  // Funzione: carica i risultati della ricerca dall'API
  // ============================================================
  const searchUsers = useCallback(async (searchQuery: string) => {
    setLoading(true);
    setError("");

    try {
      // GET /users/search?q=... con il testo della ricerca
      const { data } = await api.get<UserSearchItem[]>("/users/search", {
        params: { q: searchQuery },
      });
      setProfiles(data);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      if (axiosErr.response?.status === 401) {
        // Token scaduto → reindirizza al login
        localStorage.removeItem("auth_token");
        navigate("/login");
      } else {
        setError("Errore nel caricamento dei risultati. Backend attivo?");
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  // ============================================================
  // useEffect: carica tutti gli utenti al mount (ricerca vuota)
  // ============================================================
  useEffect(() => {
    searchUsers("");
  }, [searchUsers]);

  // ============================================================
  // Handler: cerca quando l'utente preme Invio
  // ============================================================
  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      searchUsers(query);
    }
  }

  // ============================================================
  // Filtra i profili in base ai toggle (offered/wanted)
  // ============================================================
  const filteredProfiles = profiles.filter((profile) => {
    // Se entrambi i toggle sono attivi, mostra tutto
    if (showOfferedSkills && showSoughtSkills) return true;
    // Se solo "offerte" è attivo, mostra solo chi ha skill offerte
    if (showOfferedSkills && !showSoughtSkills) {
      return profile.offered_skills.length > 0;
    }
    // Se solo "cercate" è attivo, mostra solo chi ha skill cercate
    if (!showOfferedSkills && showSoughtSkills) {
      return profile.wanted_skills.length > 0;
    }
    return false;
  });

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(249,115,22,0.12),_transparent_25%),linear-gradient(180deg,_#090909_0%,_#050505_100%)] px-3 py-3 sm:px-5 sm:py-5">
      <div className="mx-auto flex min-h-[calc(100svh-1.5rem)] w-full max-w-[1280px] overflow-hidden rounded-[28px] border border-orange-500/15 bg-[#0b0b0c] shadow-[0_24px_80px_rgba(0,0,0,0.45)]">
        {/* SIDEBAR */}
        <aside className="flex w-[235px] shrink-0 flex-col border-r border-zinc-900 bg-[#090a0b]">
          <div className="border-b border-zinc-900 px-5 py-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-orange-500/35 bg-orange-500/10">
                <Wrench className="h-5 w-5 text-orange-400" />
              </div>
              <div className="text-left">
                <div className="text-xs uppercase tracking-[0.22em] text-orange-400/70">Skill Match</div>
                <div className="text-lg font-semibold text-white">Ricerca</div>
              </div>
            </div>
          </div>
          <nav className="flex-1 px-3 py-4">
            <div className="space-y-2">
              {menuItems.map(({ label, icon: Icon, active }) => (
                <button
                  key={label}
                  type="button"
                  className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm transition-colors ${
                    active
                      ? "border border-orange-500/25 bg-orange-500/10 text-orange-300"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="font-medium">{label}</span>
                </button>
              ))}
            </div>
          </nav>
          <div className="border-t border-zinc-900 p-4">
            <div className="flex items-center gap-3 rounded-2xl bg-zinc-950 px-3 py-3">
              <img
                src="https://cdn.phototourl.com/free/2026-05-12-bac6185b-c4fb-44db-bc6e-99673f2d71cd.jpg"
                alt="Mario Rossi"
                className="h-10 w-10 rounded-full object-cover"
              />
              <div className="min-w-0 text-left">
                <div className="truncate text-sm font-medium text-white">Mario Rossi</div>
                <div className="text-xs text-zinc-500">Profilo attivo</div>
              </div>
            </div>
          </div>
        </aside>

        {/* CONTENUTO PRINCIPALE */}
        <section className="flex-1 bg-[#101113] p-5 sm:p-7">
          <div className="rounded-[26px] border border-zinc-900 bg-[#121316] p-5 sm:p-6">
            <h1 className="m-0 text-left text-[2rem] font-semibold leading-tight tracking-[-0.03em] text-white sm:text-[2.3rem]">
              Ricerca
            </h1>

            {/* BARRA DI RICERCA (cerca in tempo reale su Enter) */}
            <div className="relative mt-5">
              <Search className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-zinc-500" />
              <input
                type="text"
                placeholder="Cerca per nome, skill o parola chiave..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                className="h-13 w-full rounded-2xl border border-zinc-800 bg-[#17181b] px-4 pr-12 text-sm text-white outline-none ring-0 placeholder:text-zinc-500 focus:border-orange-500/60"
              />
            </div>

            {/* FILTRI */}
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                aria-pressed={showOfferedSkills}
                className={`inline-flex h-11 items-center gap-2 rounded-xl border px-4 text-sm font-medium transition-colors ${
                  showOfferedSkills
                    ? "border-orange-500/35 bg-orange-500/10 text-orange-300"
                    : "border-zinc-800 bg-[#17181b] text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
                }`}
                onClick={() => setShowOfferedSkills((v) => !v)}
              >
                <span className={`flex h-5 w-5 items-center justify-center rounded text-xs font-bold ${
                  showOfferedSkills
                    ? "bg-orange-500 text-black"
                    : "border border-zinc-700 bg-transparent text-transparent"
                }`}>✓</span>
                Skill offerte
              </button>
              <button
                type="button"
                aria-pressed={showSoughtSkills}
                className={`inline-flex h-11 items-center gap-2 rounded-xl border px-4 text-sm font-medium transition-colors ${
                  showSoughtSkills
                    ? "border-orange-500/35 bg-orange-500/10 text-orange-300"
                    : "border-zinc-800 bg-[#17181b] text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
                }`}
                onClick={() => setShowSoughtSkills((v) => !v)}
              >
                <span className={`flex h-5 w-5 items-center justify-center rounded text-xs font-bold ${
                  showSoughtSkills
                    ? "bg-orange-500 text-black"
                    : "border border-zinc-700 bg-transparent text-transparent"
                }`}>✓</span>
                Skill cercate
              </button>
              <button
                type="button"
                className="inline-flex h-11 min-w-[132px] items-center justify-between rounded-xl border border-zinc-800 bg-[#17181b] px-4 text-sm text-zinc-300"
              >
                Livello
                <ChevronDown className="h-4 w-4 text-zinc-500" />
              </button>
              <button
                type="button"
                className="inline-flex h-11 min-w-[185px] items-center justify-between rounded-xl border border-zinc-800 bg-[#17181b] px-4 text-sm text-zinc-300"
              >
                Tutte le categorie
                <ChevronDown className="h-4 w-4 text-zinc-500" />
              </button>
            </div>

            {/* NUMERO RISULTATI (dall'API) */}
            <div className="mt-5 text-left text-sm text-zinc-500">
              Risultati trovati: {filteredProfiles.length}
            </div>

            {/* LISTA RISULTATI */}
            <div className="mt-5 space-y-4">
              {loading ? (
                // Stato caricamento
                <div className="text-center py-10">
                  <div className="animate-spin h-8 w-8 border-4 border-orange-500 border-t-transparent rounded-full mx-auto mb-3"></div>
                  <p className="text-zinc-500 text-sm">Ricerca in corso...</p>
                </div>
              ) : error ? (
                // Stato errore
                <div className="text-center py-10">
                  <p className="text-red-400 text-sm mb-3">{error}</p>
                  <button
                    onClick={() => searchUsers(query)}
                    className="text-orange-500 hover:underline text-sm"
                  >
                    Riprova
                  </button>
                </div>
              ) : filteredProfiles.length === 0 ? (
                // Nessun risultato
                <div className="text-center py-10">
                  <p className="text-zinc-500 text-sm">Nessun utente trovato con i criteri selezionati.</p>
                </div>
              ) : (
                // Profili filtrati dall'API
                filteredProfiles.map((profile) => (
                  <article
                    key={profile.id}
                    className="grid gap-4 rounded-[24px] border border-zinc-800 bg-[#17181b] p-4 transition-colors hover:border-orange-500/30 sm:grid-cols-[1.6fr_1fr_auto] sm:p-5"
                  >
                    {/* COLONNA SINISTRA: immagine + info */}
                    <div className="flex gap-4">
                      <img
                        src="https://cdn.phototourl.com/free/2026-05-12-bac6185b-c4fb-44db-bc6e-99673f2d71cd.jpg"
                        alt={profile.name}
                        className="h-18 w-18 shrink-0 rounded-full object-cover"
                      />
                      <div className="min-w-0 text-left">
                        <h2 className="m-0 text-[1.85rem] font-semibold leading-tight tracking-[-0.03em] text-white">
                          {profile.name}
                        </h2>
                        <div className="mt-1 flex items-center gap-1.5 text-sm text-zinc-500">
                          <MapPin className="h-4 w-4" />
                          <span>{profile.location || "Localita non specificata"}</span>
                        </div>
                        <p className="mt-4 max-w-[430px] text-sm leading-6 text-zinc-400">
                          {profile.bio || "Nessuna biografia disponibile."}
                        </p>
                      </div>
                    </div>

                    {/* COLONNA CENTRALE: skill offerte + cercate (dall'API) */}
                    <div className="space-y-4 text-left">
                      {/* Skill offerte */}
                      <div>
                        <div className="text-sm font-semibold text-zinc-200">Offre</div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {profile.offered_skills.length === 0 ? (
                            <span className="text-xs text-zinc-600">Nessuna</span>
                          ) : (
                            profile.offered_skills.map((skill) => (
                              <span
                                key={skill.id}
                                className="rounded-xl border border-emerald-500/20 bg-emerald-950/70 px-3 py-1.5 text-xs font-medium text-emerald-200"
                              >
                                {skill.skill_name}
                              </span>
                            ))
                          )}
                        </div>
                      </div>
                      {/* Skill cercate */}
                      <div>
                        <div className="text-sm font-semibold text-zinc-200">Cerca</div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {profile.wanted_skills.length === 0 ? (
                            <span className="text-xs text-zinc-600">Nessuna</span>
                          ) : (
                            profile.wanted_skills.map((skill) => (
                              <span
                                key={skill.id}
                                className="rounded-xl border border-indigo-500/20 bg-indigo-950/70 px-3 py-1.5 text-xs font-medium text-indigo-200"
                              >
                                {skill.skill_name}
                              </span>
                            ))
                          )}
                        </div>
                      </div>
                    </div>

                    {/* COLONNA DESTRA: pulsante navigazione */}
                    <div className="flex items-center justify-end">
                      <button
                        onClick={() => navigate(`/card?id=${profile.id}`)}
                        type="button"
                        className="flex h-10 w-10 items-center justify-center rounded-full border border-zinc-800 bg-zinc-950 text-zinc-400 transition-colors hover:border-orange-500/35 hover:text-orange-300"
                      >
                        <ChevronRight className="h-5 w-5" />
                      </button>
                    </div>
                  </article>
                ))
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
