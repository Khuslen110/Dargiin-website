import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useAuth } from "./auth/AuthProvider";
import { AppShell } from "./components/layout/AppShell";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import PeopleListPage from "./pages/PeopleListPage";
import StructurePage from "./pages/StructurePage";
import PersonDetailPage from "./pages/PersonDetailPage";
import PersonFormPage from "./pages/PersonFormPage";
import ImportPage from "./pages/ImportPage";
import UsersPage from "./pages/UsersPage";
import AuditPage from "./pages/AuditPage";
import ProfilePage from "./pages/ProfilePage";
import NotFoundPage from "./pages/NotFoundPage";

function FullScreenLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-night-950">
      <div className="flex flex-col items-center gap-3 text-fg/50">
        <Loader2 className="h-7 w-7 animate-spin text-acid-400" />
        <p className="text-sm">Ачаалж байна…</p>
      </div>
    </div>
  );
}

function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <FullScreenLoader />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

function AdminRoute() {
  const { user } = useAuth();
  if (!user?.is_admin) return <Navigate to="/" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="people" element={<PeopleListPage />} />
          <Route path="structure" element={<StructurePage />} />
          <Route path="people/new" element={<PersonFormPage />} />
          <Route path="people/:personId" element={<PersonDetailPage />} />
          <Route path="people/:personId/edit" element={<PersonFormPage />} />
          <Route path="imports" element={<ImportPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route element={<AdminRoute />}>
            <Route path="users" element={<UsersPage />} />
            <Route path="audit" element={<AuditPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
