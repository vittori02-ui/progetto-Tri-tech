// ============================================================
// App.tsx - Router principale con protezione delle rotte
// ============================================================
import { BrowserRouter, Route, Routes, Navigate } from "react-router";
import SkillProfilePage from "./pages/profiloPersonale";
import ProfiloPubblico from "./pages/profiloPubblico";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { PaginaRicercaPage } from "./pages/PaginaRicercaPage";
import { CardPrincipalePage } from "./pages/CardPrincipalePage";
import HomePages from "./pages/HomePages";
import { DashboardPage } from "./pages/DashboardPage";
import './App.css'

// ============================================================
// Componente: ProtectedRoute
// Avvolge le rotte che richiedono autenticazione.
// Se il token non è presente nel localStorage, reindirizza a /login.
// ============================================================
function ProtectedRoute({ children }: { children: React.ReactNode }) {
    // Legge il token dal localStorage
    const token = localStorage.getItem("auth_token");

    // Se non c'è il token, reindirizza alla pagina di login
    if (!token) {
        return <Navigate to="/login" replace />;
    }

    // Se il token esiste, mostra il contenuto protetto
    return <>{children}</>;
}

// ============================================================
// Componente: PublicRoute (opzionale)
// Se l'utente è già autenticato, reindirizza alla home
// Utile per login/register per non farli vedere a utenti loggati
// ============================================================
function PublicRoute({ children }: { children: React.ReactNode }) {
    const token = localStorage.getItem("auth_token");

    // Se già loggato, vai alla home
    if (token) {
        return <Navigate to="/home" replace />;
    }

    return <>{children}</>;
}

// ============================================================
// Componente principale App
// Definisce tutte le rotte dell'applicazione
// ============================================================
function App() {
  return (
    <>
       <BrowserRouter>
        <Routes>
          <Route path="/">
            {/* Rotte pubbliche (accessibili senza login) */}
            <Route path="login" element={<PublicRoute><LoginPage /></PublicRoute>} />
            <Route path="register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

            {/* Rotte protette (richiedono token JWT) */}
            <Route index element={<ProtectedRoute><SkillProfilePage /></ProtectedRoute>} />
            <Route path="public" element={<ProtectedRoute><ProfiloPubblico /></ProtectedRoute>} />
            <Route path="search" element={<ProtectedRoute><PaginaRicercaPage /></ProtectedRoute>} />
            <Route path="card" element={<ProtectedRoute><CardPrincipalePage /></ProtectedRoute>} />
            <Route path="home" element={<ProtectedRoute><HomePages /></ProtectedRoute>} />
            <Route path="dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />

            {/* Rotta di fallback: se nessuna corrispondenza, vai a home */}
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App
