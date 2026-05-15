import { useEffect, useState } from "react";
import { LogOut, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

type MeResponse = {
  id: number;
  name: string;
  email: string;
};

export function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState<MeResponse | null>(null);

  useEffect(() => {
    api
      .get<MeResponse>("/auth/me")
      .then(({ data }) => setUser(data))
      .catch(() => navigate("/login"));
  }, [navigate]);

  function logout() {
    localStorage.removeItem("auth_token");
    navigate("/login");
  }

  return (
    <main className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Badge className="mb-3 gap-2" variant="secondary">
              <ShieldCheck className="h-3.5 w-3.5" />
              Sessione attiva
            </Badge>
            <h1 className="text-3xl font-semibold text-slate-950">Dashboard</h1>
          </div>
          <Button variant="outline" onClick={logout}>
            <LogOut className="h-4 w-4" />
            Esci
          </Button>
        </header>
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Profilo utente</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border bg-white p-4">
              <div className="text-sm text-muted-foreground">Nome</div>
              <div className="mt-1 font-medium">{user?.name ?? "Caricamento..."}</div>
            </div>
            <div className="rounded-lg border bg-white p-4">
              <div className="text-sm text-muted-foreground">Email</div>
              <div className="mt-1 font-medium">{user?.email ?? "Caricamento..."}</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
