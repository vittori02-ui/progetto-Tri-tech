// ============================================================
// CardPrincipalePage.tsx - Dettaglio profilo utente (da API)
// ============================================================
import { useState, useEffect } from "react";
import { ArrowRight, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useNavigate, useSearchParams } from "react-router";
import { api } from "@/lib/api";
import type { AxiosError } from "axios";

// ============================================================
// Tipi corrispondenti ai modelli Pydantic del backend
// ============================================================

/** Skill associata (UserSkillResponse) */
type UserSkillItem = {
  id: number;
  skill_id: number;
  skill_name: string;
  level: string;
  user_id: number;
};

/** Profilo pubblico (UserPublicResponse) */
type PublicProfile = {
  id: number;
  name: string;
  bio: string;
  location: string;
};

/** Skill raggruppate */
type UserSkillsResponse = {
  offered_skills: UserSkillItem[];
  wanted_skills: UserSkillItem[];
};

export function CardPrincipalePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const userId = searchParams.get("id"); // Legge l'ID dall'URL (/card?id=XXX)

  // Stati per i dati API
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [offeredSkills, setOfferedSkills] = useState<UserSkillItem[]>([]);
  const [wantedSkills, setWantedSkills] = useState<UserSkillItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ============================================================
  // useEffect: carica i dati al mount
  // ============================================================
  useEffect(() => {
    if (!userId) {
      // Se nessun ID, usa ID 1 come fallback
      loadCardData(1);
      return;
    }
    loadCardData(Number(userId));
  }, [userId]);

  // ============================================================
  // Funzione: carica profilo + skill dall'API
  // ============================================================
  async function loadCardData(id: number) {
    setLoading(true);
    setError("");

    try {
      // Chiamate parallele: profilo pubblico + skill
      const [profileRes, skillsRes] = await Promise.all([
        api.get<PublicProfile>(`/users/public/${id}`),
        api.get<UserSkillsResponse>(`/users/${id}/skills`),
      ]);

      setProfile(profileRes.data);
      setOfferedSkills(skillsRes.data.offered_skills || []);
      setWantedSkills(skillsRes.data.wanted_skills || []);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      if (axiosErr.response?.status === 404) {
        setError("Utente non trovato.");
      } else {
        setError("Impossibile caricare i dati dell'utente.");
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
      <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(249,115,22,0.12),_transparent_28%),linear-gradient(180deg,_#0b0b0b_0%,_#050505_100%)] px-4 py-8 sm:px-8 lg:px-14">
        <div className="mx-auto flex min-h-[calc(100svh-4rem)] w-full max-w-6xl items-center justify-center rounded-[32px] border border-orange-500/15 bg-zinc-950/30 p-6 backdrop-blur-sm sm:p-10">
          <div className="text-center">
            <div className="animate-spin h-10 w-10 border-4 border-orange-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-zinc-400">Caricamento profilo...</p>
          </div>
        </div>
      </main>
    );
  }

  // ============================================================
  // Schermata di errore
  // ============================================================
  if (error) {
    return (
      <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(249,115,22,0.12),_transparent_28%),linear-gradient(180deg,_#0b0b0b_0%,_#050505_100%)] px-4 py-8 sm:px-8 lg:px-14">
        <div className="mx-auto flex min-h-[calc(100svh-4rem)] w-full max-w-6xl items-center justify-center rounded-[32px] border border-orange-500/15 bg-zinc-950/30 p-6 backdrop-blur-sm sm:p-10">
          <div className="text-center">
            <p className="text-red-400 mb-4">{error}</p>
            <button
              onClick={() => navigate(-1)}
              className="px-6 py-3 bg-orange-500 hover:bg-orange-600 rounded-2xl font-medium transition"
            >
              Indietro
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(249,115,22,0.12),_transparent_28%),linear-gradient(180deg,_#0b0b0b_0%,_#050505_100%)] px-4 py-8 sm:px-8 lg:px-14">
      <div className="mx-auto flex min-h-[calc(100svh-4rem)] w-full max-w-6xl items-center justify-center rounded-[32px] border border-orange-500/15 bg-zinc-950/30 p-6 backdrop-blur-sm sm:p-10">
        <Card className="w-full max-w-[420px] rounded-[32px] border border-orange-500/60 bg-zinc-950 text-white shadow-[0_0_0_1px_rgba(249,115,22,0.12),0_18px_60px_rgba(0,0,0,0.55)]">
          <CardContent className="p-6">
            <div className="rounded-[26px] border border-orange-500/20 bg-zinc-950/80 p-6">
              {/* FOTO PROFILO */}
              <div className="relative h-22 w-22">
                <img
                  src="https://cdn.phototourl.com/free/2026-05-12-bac6185b-c4fb-44db-bc6e-99673f2d71cd.jpg"
                  alt={`Foto profilo di ${profile?.name || "utente"}`}
                  className="h-22 w-22 rounded-full object-cover shadow-inner"
                />
                <span className="absolute bottom-1 right-1 h-4 w-4 rounded-full border-2 border-zinc-950 bg-emerald-500" />
              </div>

              {/* NOME + LUOGO (dall'API) */}
              <div className="mt-5">
                <h1 className="m-0 max-w-[280px] text-[2rem] leading-tight font-semibold tracking-[-0.03em] text-white sm:text-[2.2rem]">
                  {profile?.name || "Nome utente"}
                </h1>
                <div className="mt-2 flex items-center gap-1.5 text-sm text-zinc-400">
                  <MapPin className="h-4 w-4 text-zinc-500" />
                  <span>{profile?.location || "Localita non specificata"}</span>
                </div>
                <p className="mt-4 max-w-[250px] text-sm leading-7 text-zinc-400">
                  {profile?.bio || "Nessuna biografia disponibile."}
                </p>
              </div>

              {/* SKILL OFFERTE (dall'API) */}
              <div className="mt-6 border-t border-zinc-800 pt-5">
                <h2 className="text-lg font-semibold text-zinc-100">Offre</h2>
                <div className="mt-3 flex flex-wrap gap-2">
                  {offeredSkills.length === 0 ? (
                    <span className="text-xs text-zinc-600">Nessuna skill offerta</span>
                  ) : (
                    offeredSkills.map((skill) => (
                      <span
                        key={skill.id}
                        className="rounded-xl border border-emerald-500/20 bg-emerald-950/70 px-3 py-1.5 text-sm font-medium text-emerald-200"
                      >
                        {skill.skill_name}
                      </span>
                    ))
                  )}
                </div>
              </div>

              {/* SKILL CERCATE (dall'API) */}
              <div className="mt-5">
                <h2 className="text-lg font-semibold text-zinc-100">Cerca</h2>
                <div className="mt-3 flex flex-wrap gap-2">
                  {wantedSkills.length === 0 ? (
                    <span className="text-xs text-zinc-600">Nessuna skill cercata</span>
                  ) : (
                    wantedSkills.map((skill) => (
                      <span
                        key={skill.id}
                        className="rounded-xl border border-indigo-500/20 bg-indigo-950/70 px-3 py-1.5 text-sm font-medium text-indigo-200"
                      >
                        {skill.skill_name}
                      </span>
                    ))
                  )}
                </div>
              </div>

              {/* PULSANTE: naviga al profilo pubblico */}
              <Button
                onClick={() => {
                  if (profile) {
                    navigate(`/public?id=${profile.id}`);
                  } else {
                    navigate("/public");
                  }
                }}
                className="mt-8 h-12 w-full rounded-xl border border-orange-500 bg-transparent text-base font-semibold text-orange-400 hover:bg-orange-500 hover:text-black"
                variant="outline"
              >
                Vedi profilo
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
