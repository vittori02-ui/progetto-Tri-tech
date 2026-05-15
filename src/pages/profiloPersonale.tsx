// ============================================================
// profiloPersonale.tsx - Pagina del profilo utente con API reali
// ============================================================
import { useState, useEffect, type FormEvent } from "react";
import { Search, ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import type { AxiosError } from "axios";

// ============================================================
// Tipi TypeScript corrispondenti ai modelli Pydantic del backend
// ============================================================

/** Risposta dall'endpoint /auth/me (UserMeResponse in models.py) */
type MeResponse = {
  id: number;
  name: string;
  email: string;
  bio: string;
  location: string;
};

/** Risposta dall'endpoint /skills/my (UserSkillResponse in models.py) */
type UserSkillResponse = {
  id: number;
  skill_id: number;
  skill_name: string;  // Corrisponde a 'name' nel modello Skill ma rinominato per chiarezza
  level: string;
  user_id: number;
};

/** Payload per creare/aggiornare una UserSkill (UserSkillCreate in models.py) */
type UserSkillPayload = {
  skill_name: string;
  level: string;
  type: string;        // "offered" o "wanted"
};

// ============================================================
// Componente principale
// ============================================================
export default function ProfiloPersonale() {
  // Stati per i dati utente e skill
  const [user, setUser] = useState<MeResponse | null>(null);
  const [skillsOfferte, setSkillsOfferte] = useState<UserSkillResponse[]>([]);
  const [searchSkills, setSearchSkills] = useState<UserSkillResponse[]>([]); // Skill cercate (solo UI)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Stati per la modifica del profilo
  const [isModified, setIsModified] = useState(false);
  const [bioText, setBioText] = useState("");

  // Stati per il popup di aggiunta skill
  const [showPopup, setShowPopup] = useState(false);
  const [skillType, setSkillType] = useState("offerte");
  
  // Stati per il form nel popup
  const [newSkillName, setNewSkillName] = useState("");
  const [newSkillLevel, setNewSkillLevel] = useState("Intermedio");
  const [savingSkill, setSavingSkill] = useState(false);
  const [skillError, setSkillError] = useState("");

  // ============================================================
  // useEffect: carica i dati al mount del componente
  // ============================================================
  useEffect(() => {
    loadProfileData();
  }, []);

  // ============================================================
  // Funzione: carica profilo + skill dall'API
  // ============================================================
  async function loadProfileData() {
    setLoading(true);
    setError("");

    try {
      // Chiamata parallela: /auth/me per i dati utente e /skills/my per le skill
      const [meResponse, skillsResponse] = await Promise.all([
        api.get<MeResponse>("/auth/me"),
        api.get<UserSkillResponse[]>("/skills/my"),
      ]);

      // Popola gli stati con i dati ricevuti
      setUser(meResponse.data);
      setBioText(meResponse.data.bio || "");
      setSkillsOfferte(skillsResponse.data);
      // Le skill "cercate" sono separate solo nell'UI; per ora usiamo un array vuoto
      // In futuro: si può aggiungere un campo "type" su UserSkill
      setSearchSkills([]);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      if (axiosErr.response?.status === 401) {
        setError("Sessione scaduta. Effettua di nuovo il login.");
        // Reindirizza al login dopo 2 secondi
        setTimeout(() => { window.location.href = "/login"; }, 2000);
      } else {
        setError("Errore nel caricamento del profilo. Assicurati che il backend sia attivo.");
      }
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // Funzione: Salva la bio aggiornata
  // ============================================================
  async function handleSaveProfile() {
    try {
      // PUT /auth/profile con la bio aggiornata
      const { data } = await api.put<MeResponse>("/auth/profile", {
        bio: bioText,
      });
      setUser(data); // Aggiorna i dati locali
      setIsModified(false); // Resetta lo stato di modifica
    } catch (err) {
      console.error("Errore salvataggio profilo:", err);
      setError("Errore durante il salvataggio del profilo.");
    }
  }

  // ============================================================
  // Funzione: Aggiunge una nuova skill (Salva Skill)
  // Invia i dati al backend via POST /skills/my
  // ============================================================
  async function handleAddSkill() {
    if (!newSkillName.trim()) {
      setSkillError("Inserisci un nome per la skill.");
      return;
    }
    if (!newSkillLevel) {
      setSkillError("Seleziona un livello.");
      return;
    }

    setSavingSkill(true);
    setSkillError("");

    try {
      // Costruisce il payload secondo UserSkillCreate (skill_name, level)
      const payload: UserSkillPayload = {
        skill_name: newSkillName.trim(),
        level: newSkillLevel,
        type: skillType === "offerte" ? "offered" : "wanted",
      };

      // POST /skills/my per creare l'associazione utente-skill
      const { data } = await api.post<UserSkillResponse>("/skills/my", payload);

      // Aggiunge la nuova skill alla lista locale
      // Determina se è "offerta" o "cercata" in base al radiobutton selezionato
      if (skillType === "offerte") {
        setSkillsOfferte((prev) => [...prev, data]);
      } else {
        setSearchSkills((prev) => [...prev, data]);
      }

      // Chiude il popup e resetta i campi
      setShowPopup(false);
      setNewSkillName("");
      setNewSkillLevel("Intermedio");
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      setSkillError(axiosErr.response?.data?.detail || "Errore nell'aggiunta della skill.");
    } finally {
      setSavingSkill(false);
    }
  }

  // ============================================================
  // Funzione: Rimuove una skill
  // DELETE /skills/my/{user_skill_id}
  // ============================================================
  async function handleRemoveSkill(skillId: number, isOfferta: boolean) {
    try {
      // Chiamata DELETE per rimuovere l'associazione
      await api.delete(`/skills/my/${skillId}`);

      // Rimuove dalla lista locale
      if (isOfferta) {
        setSkillsOfferte((prev) => prev.filter((s) => s.id !== skillId));
      } else {
        setSearchSkills((prev) => prev.filter((s) => s.id !== skillId));
      }
    } catch (err) {
      console.error("Errore rimozione skill:", err);
      setError("Errore durante la rimozione della skill.");
    }
  }

  // ============================================================
  // Mappa colori per i livelli delle skill (UI invariata)
  // ============================================================
  const levelColors: Record<string, string> = {
    Principiante: "bg-yellow-100 text-yellow-800",
    Intermedio: "bg-blue-100 text-blue-800",
    Avanzato: "bg-green-100 text-green-800",
  };

  // Determina quali skill mostrare in base al radiobutton
  const currentSkills = skillType === "offerte" ? skillsOfferte : searchSkills;

  // ============================================================
  // Schermata di caricamento
  // ============================================================
  if (loading) {
    return (
      <div className="min-h-screen bg-black p-6 flex justify-center items-start text-white">
        <div className="text-center mt-20">
          <div className="animate-spin h-10 w-10 border-4 border-orange-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-zinc-400">Caricamento profilo...</p>
        </div>
      </div>
    );
  }

  // ============================================================
  // Schermata di errore
  // ============================================================
  if (error && !user) {
    return (
      <div className="min-h-screen bg-black p-6 flex justify-center items-start text-white">
        <div className="text-center mt-20">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={loadProfileData}
            className="bg-orange-500 text-black px-6 py-2 rounded-xl font-bold hover:bg-orange-600"
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  // ============================================================
  // Render principale (UI identica all'originale + integrazione API)
  // ============================================================
  return (
    <div className="min-h-screen bg-black p-6 flex justify-center items-start text-white">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ========================= */}
        {/* CARD PROFILO */}
        {/* ========================= */}
        <div className="bg-black rounded-3xl border border-orange-500 shadow-[0_0_15px_rgba(249,115,22,0.1)] p-6 lg:col-span-1">
          <div className="flex flex-col items-center text-center">
            {/* FOTO PROFILO */}
            <div className="w-32 h-32 rounded-full bg-zinc-900 flex items-center justify-center overflow-hidden border-4 border-orange-500">
              <img
                src="https://cdn.phototourl.com/free/2026-05-12-bac6185b-c4fb-44db-bc6e-99673f2d71cd.jpg"
                alt={user?.name || "Profile"}
                className="w-full h-full object-cover"
              />
            </div>
            {/* NOME UTENTE (dall'API) */}
            <h1 className="text-3xl font-semibold">
              {user?.name || "Username"}
            </h1>
            {/* LOCALITA (dall'API) */}
            <p className="text-slate-500 text-sm mt-1">
              {user?.location || "Localita non impostata"}
            </p>
            {/* BIO */}
            <div className="mt-5 w-full">
              <h2 className="text-3xl font-semibold">Bio</h2>
              {/* Textarea bio con valore dall'API */}
              <textarea
                value={bioText}
                onChange={(e) => {
                  setBioText(e.target.value);
                  setIsModified(true); // Segnala che ci sono modifiche
                }}
                placeholder="Scrivi una breve bio..."
                className="
                  w-full
                  min-h-[120px]
                  rounded-2xl
                  border
                  border-orange-500
                  bg-black
                  p-3
                  text-white
                  outline-none
                  focus:ring-2
                  focus:ring-orange-400
                  placeholder:text-orange-500/50
                  resize-none
                "
              />
            </div>
            {/* Pulsante salva/indietro */}
            {isModified ? (
              <button
                onClick={handleSaveProfile} // Salva la bio via API
                className="
                  mt-5
                  w-full
                  bg-black
                  text-orange-500
                  border-2
                  border-orange-500
                  py-3
                  rounded-2xl
                  font-bold
                  hover:bg-orange-500
                  hover:text-black
                  transition-all
                "
              >
                Salva Profilo
              </button>
            ) : (
              <button
                onClick={() => window.history.back()}
                className="
                  mt-5
                  w-full
                  flex
                  items-center
                  justify-center
                  gap-2
                  bg-black
                  text-orange-500
                  border-2
                  border-orange-500
                  py-3
                  rounded-2xl
                  font-bold
                  hover:bg-orange-500
                  hover:text-black
                  transition-all
                "
              >
                <ArrowLeft size={20} />
                Indietro
              </button>
            )}
          </div>
        </div>

        {/* ========================= */}
        {/* SEZIONE SKILL */}
        {/* ========================= */}
        <div className="lg:col-span-2 space-y-4">
          <br />
          {/* BARRA DI RICERCA + RADIOBUTTON */}
          <div className="relative mb-1">
            <input
              type="text"
              placeholder="Cerca skill..."
              className="
                w-full
                mb-5
                bg-black
                border-2
                border-orange-500
                rounded-2xl
                p-3
                text-white
                outline-none
                focus:ring-2
                focus:ring-orange-400
                placeholder:text-orange-500/30
              "
            />
            <div className="absolute right-3 top-1/3 -translate-y-1/2 flex items-center gap-2">
              {/* Radiobutton: Offerte / Cercate */}
              <label className="flex items-center gap-1 text-[20] text-orange-500">
                <input
                  type="radio"
                  name="skillType"
                  checked={skillType === "offerte"}
                  onChange={() => setSkillType("offerte")}
                  className="accent-orange-500"
                />
                Offerte
              </label>
              <label className="flex items-center gap-1 text-[20] text-orange-500">
                <input
                  type="radio"
                  name="skillType"
                  checked={skillType === "cercate"}
                  onChange={() => setSkillType("cercate")}
                  className="accent-orange-500"
                />
                Cercate
              </label>
              <Search size={20} className="text-orange-500" />
            </div>
          </div>

          {/* SKILL OFFERTE (dati dall'API) */}
          <div className="bg-black rounded-3xl border-2 !border-orange-500 p-6 shadow-lg">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold">Skill Offerte</h2>
                <p className="text-zinc-500 text-sm">Competenze che puoi offrire</p>
              </div>
              <button
                onClick={() => {
                  setShowPopup(true);
                  setSkillType("offerte"); // Imposta il tipo su "offerte"
                }}
                className="bg-orange-500 text-black px-5 py-2 rounded-xl font-bold hover:bg-orange-600 transition"
              >
                + Aggiungi
              </button>
            </div>
            <div className="flex flex-wrap gap-3">
              {skillsOfferte.length === 0 ? (
                <p className="text-zinc-500 text-sm">Nessuna skill aggiunta. Clicca "+ Aggiungi".</p>
              ) : (
                skillsOfferte.map((skill) => (
                  <div key={skill.id} className="flex items-center gap-3 bg-zinc-900 border !border-orange-500/30 px-4 py-3 rounded-2xl">
                    <div>
                      <p className="font-medium text-white">{skill.skill_name}</p>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${levelColors[skill.level] || "bg-gray-100 text-gray-800"}`}>
                        {skill.level}
                      </span>
                    </div>
                    {/* Pulsante Rimuovi: chiama DELETE /skills/my/{id} */}
                    <button
                      onClick={() => handleRemoveSkill(skill.id, true)}
                      className="text-red-500 hover:text-red-400 text-sm font-bold ml-2"
                    >
                      Rimuovi
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* SKILL CERCATE (dati dall'API) */}
          <div className="bg-black rounded-3xl border-2 !border-orange-500 p-6 shadow-lg">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold">Skill Cercate</h2>
                <p className="text-zinc-500 text-sm">Competenze che vuoi imparare</p>
              </div>
              <button
                onClick={() => {
                  setShowPopup(true);
                  setSkillType("cercate"); // Imposta il tipo su "cercate"
                }}
                className="bg-orange-500 text-black px-5 py-2 rounded-xl font-bold hover:bg-orange-600 transition"
              >
                + Aggiungi
              </button>
            </div>
            <div className="flex flex-wrap gap-3">
              {searchSkills.length === 0 ? (
                <p className="text-zinc-500 text-sm">Nessuna skill cercata. Clicca "+ Aggiungi".</p>
              ) : (
                searchSkills.map((skill) => (
                  <div key={skill.id} className="flex items-center gap-3 bg-zinc-900 border !border-orange-500/30 px-4 py-3 rounded-2xl">
                    <div>
                      <p className="font-medium text-white">{skill.skill_name}</p>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${levelColors[skill.level] || "bg-gray-100 text-gray-800"}`}>
                        {skill.level}
                      </span>
                    </div>
                    <button
                      onClick={() => handleRemoveSkill(skill.id, false)}
                      className="text-red-500 hover:text-red-400 text-sm font-bold ml-2"
                    >
                      Rimuovi
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ========================= */}
      {/* POPUP: Aggiungi Nuova Skill */}
      {/* ========================= */}
      {showPopup && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="w-[500px]">
            <div className="bg-black rounded-3xl border-2 border-orange-500 p-6 shadow-lg">
              <h2 className="text-xl font-bold mb-4 text-orange-500">
                Aggiungi Nuova Skill
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Input: Nome skill */}
                <input
                  type="text"
                  placeholder="Nome skill (es. React)"
                  value={newSkillName}
                  onChange={(e) => setNewSkillName(e.target.value)}
                  className="
                    bg-black
                    border-2
                    border-orange-500
                    rounded-2xl
                    p-3
                    text-white
                    outline-none
                    focus:ring-2
                    focus:ring-orange-400
                    placeholder:text-orange-500/30
                  "
                />
                {/* Select: Livello */}
                <select
                  value={newSkillLevel}
                  onChange={(e) => setNewSkillLevel(e.target.value)}
                  className="
                    bg-black
                    border-2
                    border-orange-500
                    rounded-2xl
                    p-3
                    text-white
                    outline-none
                    focus:ring-2
                    focus:ring-orange-400
                  "
                >
                  <option className="bg-black text-white">Principiante</option>
                  <option className="bg-black text-white">Intermedio</option>
                  <option className="bg-black text-white">Avanzato</option>
                </select>
              </div>

              {/* Messaggio di errore nel popup */}
              {skillError && (
                <p className="text-red-400 text-sm mt-2">{skillError}</p>
              )}

              <div className="flex gap-3 mt-6">
                {/* Pulsante: Salva Skill (chiama POST /skills/my) */}
                <button
                  onClick={handleAddSkill}
                  disabled={savingSkill}
                  className="
                    flex-1
                    bg-orange-500
                    text-black
                    py-3
                    rounded-2xl
                    font-bold
                    hover:bg-orange-600
                    transition
                    disabled:opacity-50
                  "
                >
                  {savingSkill ? "Salvataggio..." : "Salva Skill"}
                </button>
                {/* Pulsante: Annulla */}
                <button
                  onClick={() => {
                    setShowPopup(false);
                    setNewSkillName("");
                    setNewSkillLevel("Intermedio");
                    setSkillError("");
                  }}
                  className="
                    flex-1
                    bg-zinc-800
                    text-white
                    py-3
                    rounded-2xl
                    font-bold
                    hover:bg-zinc-700
                    transition
                    border
                    border-orange-500/20
                  "
                >
                  Annulla
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
