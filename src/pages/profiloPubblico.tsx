// ============================================================
// profiloPubblico.tsx - Profilo pubblico di un utente (da API)
// ============================================================
import { useNavigate, useSearchParams } from "react-router";
import { useState, useEffect } from "react";
import { Search, MapPin } from "lucide-react";
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

/** Profilo pubblico utente (UserPublicResponse) */
type PublicProfile = {
  id: number;
  name: string;
  bio: string;
  location: string;
};

/** Skill raggruppate per utente */
type UserSkillsResponse = {
  offered_skills: UserSkillItem[];
  wanted_skills: UserSkillItem[];
};

export default function ProfiloPubblico() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const userId = searchParams.get("id"); // Legge l'ID dall'URL (/public?id=XXX)

  // Stati per i dati API
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [offeredSkills, setOfferedSkills] = useState<UserSkillItem[]>([]);
  const [wantedSkills, setWantedSkills] = useState<UserSkillItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Stati UI (invariati)
  const [tab, setTab] = useState("panoramica");
  const [status, setStatus] = useState<"idle" | "pending" | "accepted" | "declined">("idle");
  const [showPopup, setShowPopup] = useState(false);
  const [popupMsg, setPopupMsg] = useState("");
  const [openMenu, setOpenMenu] = useState(false);

  // ============================================================
  // useEffect: carica il profilo pubblico al mount
  // ============================================================
  useEffect(() => {
    if (!userId) {
      setError("ID utente non specificato.");
      setLoading(false);
      return;
    }
    loadPublicProfile(Number(userId));
  }, [userId]);

  // ============================================================
  // Funzione: carica profilo pubblico + skill dall'API
  // ============================================================
  async function loadPublicProfile(id: number) {
    setLoading(true);
    setError("");

    try {
      // Chiamate parallele: profilo + skill
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
        setError("Errore nel caricamento del profilo pubblico.");
      }
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // Handler richiesta (UI locale, futura integrazione API)
  // ============================================================
  const handleRequestClick = () => {
    if (status === "idle") {
      setStatus("pending");
      setPopupMsg("Invio richiesta completato con successo");
      setShowPopup(true);
      setTimeout(() => setShowPopup(false), 2500);
    } else if (status === "pending") {
      setPopupMsg("Richiesta annullata");
      setShowPopup(true);
      setTimeout(() => {
        setShowPopup(false);
        setStatus("idle");
      }, 3000);
    }
  };

  // ============================================================
  // Schermata di caricamento
  // ============================================================
  if (loading) {
    return (
      <div className="min-h-screen bg-black p-6 flex justify-center text-white">
        <div className="text-center mt-20">
          <div className="animate-spin h-10 w-10 border-4 border-orange-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-zinc-400">Caricamento profilo pubblico...</p>
        </div>
      </div>
    );
  }

  // ============================================================
  // Schermata di errore
  // ============================================================
  if (error || !profile) {
    return (
      <div className="min-h-screen bg-black p-6 flex justify-center text-white">
        <div className="text-center mt-20">
          <p className="text-red-400 mb-4">{error || "Profilo non disponibile."}</p>
          <button
            onClick={() => navigate(-1)}
            className="bg-orange-500 text-black px-6 py-2 rounded-xl font-bold hover:bg-orange-600"
          >
            Indietro
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black p-6 flex justify-center text-white">
      <div className="w-full max-w-4xl space-y-6">

        {/* HEADER (dati dall'API) */}
        <div className="bg-zinc-950 rounded-3xl border border-orange-500 p-6 shadow-[0_0_20px_rgba(249,115,22,0.15)]">
          <div className="flex flex-col md:flex-row md:items-start gap-6">

            {/* FOTO */}
            <div className="w-28 h-28 md:w-32 md:h-32 rounded-full overflow-hidden border-4 border-orange-500 bg-zinc-900">
              <img
                src="https://cdn.phototourl.com/free/2026-05-12-bac6185b-c4fb-44db-bc6e-99673f2d71cd.jpg"
                className="w-full h-full object-cover"
                alt={profile.name}
              />
            </div>

            {/* INFO (dall'API) */}
            <div className="flex-1 text-left">
              <h2 className="text-3xl font-semibold">{profile.name}</h2>
              {/* Location dall'API */}
              <div className="flex items-center gap-2 text-zinc-400 text-sm mt-1">
                <MapPin size={16} className="text-orange-500" />
                <span>{profile.location || "Localita non specificata"}</span>
              </div>
              {/* Bio dall'API */}
              <p className="text-zinc-400 text-sm mt-2">
                {profile.bio || "Nessuna biografia disponibile."}
              </p>
            </div>

            {/* BOTTONI */}
            <div className="flex gap-2">
              <button
                onClick={handleRequestClick}
                className={`px-4 py-2 text-sm rounded-lg transition ${
                  status === "idle"
                    ? "bg-orange-500 hover:bg-orange-600 text-white"
                    : status === "pending"
                      ? "bg-yellow-600 hover:bg-yellow-700 text-white"
                      : status === "accepted"
                        ? "bg-green-600 hover:bg-green-700 text-white"
                        : "bg-red-600 hover:bg-red-700 text-white"
                }`}
              >
                {status === "idle"
                  ? "Invia richiesta"
                  : status === "pending"
                    ? "In attesa di risposta..."
                    : status === "accepted"
                      ? "Richiesta accettata"
                      : "Richiesta declinata"}
              </button>
              <div className="relative">
                <button
                  onClick={() => setOpenMenu((v) => !v)}
                  className="px-3 py-2 text-sm bg-zinc-800 hover:bg-zinc-700 rounded-lg transition"
                >
                  ...
                </button>
                {openMenu && (
                  <div className="absolute right-0 mt-2 w-40 bg-zinc-900 border border-zinc-700 rounded-xl shadow-lg overflow-hidden z-50">
                    <button
                      onClick={() => {
                        alert("Utente bloccato");
                        setOpenMenu(false);
                      }}
                      className="w-full text-left px-4 py-2 text-sm hover:bg-zinc-800"
                    >
                      Blocca
                    </button>
                    <button
                      onClick={() => {
                        alert("Segnalazione inviata");
                        setOpenMenu(false);
                      }}
                      className="w-full text-left px-4 py-2 text-sm hover:bg-zinc-800 text-red-400"
                    >
                      Segnala
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* TAB */}
          <div className="flex gap-6 mt-6 border-b border-zinc-800">
            {[
              { id: "panoramica", label: "Panoramica" },
              { id: "offerte", label: "Skill offerte" },
              { id: "cercate", label: "Skill cercate" },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`pb-3 text-sm border-b-2 transition ${
                  tab === t.id
                    ? "border-orange-500 text-white"
                    : "border-transparent text-zinc-400 hover:text-white"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* PANORAMICA (dati dall'API) */}
        {tab === "panoramica" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-zinc-950 rounded-2xl border border-zinc-800 p-5">
              <h3 className="text-lg font-semibold mb-3">Bio</h3>
              <p className="text-zinc-400 text-sm">
                {profile.bio || "Nessuna biografia disponibile."}
              </p>
            </div>
            <div className="bg-zinc-950 rounded-2xl border border-zinc-800 p-5">
              <h3 className="text-lg font-semibold mb-3">Skill offerte</h3>
              <div className="flex flex-wrap gap-2">
                {offeredSkills.length === 0 ? (
                  <span className="text-zinc-500 text-sm">Nessuna skill offerta.</span>
                ) : (
                  offeredSkills.map((s, i) => (
                    <span
                      key={i}
                      className="bg-orange-500/20 text-orange-400 px-3 py-1 rounded-full text-sm"
                    >
                      {s.skill_name}
                    </span>
                  ))
                )}
              </div>
            </div>
            <div className="bg-zinc-950 rounded-2xl border border-zinc-800 p-5">
              <h3 className="text-lg font-semibold mb-3">Skill cercate</h3>
              <div className="flex flex-wrap gap-2">
                {wantedSkills.length === 0 ? (
                  <span className="text-zinc-500 text-sm">Nessuna skill cercata.</span>
                ) : (
                  wantedSkills.map((s, i) => (
                    <span
                      key={i}
                      className="bg-orange-500/20 text-orange-400 px-3 py-1 rounded-full text-sm"
                    >
                      {s.skill_name}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* POPUP INFO */}
        {showPopup && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/60 z-50">
            <div className="bg-zinc-900 border border-orange-500 text-white px-6 py-4 rounded-2xl shadow-lg">
              <p className="text-sm">{popupMsg}</p>
            </div>
          </div>
        )}

        {/* SKILL OFFERTE (dall'API) */}
        {tab === "offerte" && (
          <div>
            <div className="relative mb-5">
              <input
                type="text"
                placeholder="Cerca skill Offerte..."
                className="
                  w-full
                  bg-black
                  border-2
                  border-orange-500
                  rounded-2xl
                  p-3
                  pr-44
                  text-white
                  outline-none
                  focus:ring-2
                  focus:ring-orange-400
                  placeholder:text-orange-500/30
                "
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-3">
                <Search size={18} className="text-orange-500" />
              </div>
            </div>
            <div className="bg-zinc-950 rounded-2xl border border-zinc-800 p-5">
              <h3 className="text-lg font-semibold mb-3">Skill offerte</h3>
              <div className="flex flex-wrap gap-2">
                {offeredSkills.length === 0 ? (
                  <p className="text-zinc-500 text-sm">Nessuna skill offerta.</p>
                ) : (
                  offeredSkills.map((s, i) => (
                    <span
                      key={i}
                      className="bg-orange-500/20 text-orange-400 px-3 py-1 rounded-full text-sm"
                    >
                      {s.skill_name}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* SKILL CERCATE (dall'API) */}
        {tab === "cercate" && (
          <div>
            <div className="relative mb-5">
              <input
                type="text"
                placeholder="Cerca skill Cercate"
                className="
                  w-full
                  bg-black
                  border-2
                  border-orange-500
                  rounded-2xl
                  p-3
                  pr-44
                  text-white
                  outline-none
                  focus:ring-2
                  focus:ring-orange-400
                  placeholder:text-orange-500/30
                "
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-3">
                <Search size={18} className="text-orange-500" />
              </div>
            </div>
            <div className="bg-zinc-950 rounded-2xl border border-zinc-800 p-5">
              <h3 className="text-lg font-semibold mb-3">Skill cercate</h3>
              <div className="flex flex-wrap gap-2">
                {wantedSkills.length === 0 ? (
                  <p className="text-zinc-500 text-sm">Nessuna skill cercata.</p>
                ) : (
                  wantedSkills.map((s, i) => (
                    <span
                      key={i}
                      className="bg-orange-500/20 text-orange-400 px-3 py-1 rounded-full text-sm"
                    >
                      {s.skill_name}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
