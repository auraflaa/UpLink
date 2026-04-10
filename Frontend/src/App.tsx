import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import ResumePage from "./pages/ResumePage";
import GithubPage from "./pages/GithubPage";
import EventsPage from "./pages/EventsPage";
import SettingsPage from "./pages/SettingsPage";
import EnterprisePage from "./pages/EnterprisePage";
import DashboardLayout from "./components/DashboardLayout";
import { ThemeProvider } from "./components/theme-provider";
import { ToastProvider } from "./components/ui/use-toast";

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="uplink-ui-theme">
      <ToastProvider>
        <BrowserRouter>
          <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/enterprise" element={<EnterprisePage />} />
          <Route path="/login" element={<LoginPage />} />
          
          {/* Authenticated Routes wrapped in DashboardLayout */}
          <Route element={<DashboardLayout />}>
            <Route path="/home" element={<HomePage />} />
            <Route path="/resume" element={<ResumePage />} />
            <Route path="/github" element={<GithubPage />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  );
}
