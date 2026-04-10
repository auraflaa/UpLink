import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import GitHubAnalyzerPage from './pages/GitHubAnalyzerPage';
import ResumeUploadPage from './pages/ResumeUploadPage';

function App() {
  return (
    <BrowserRouter>
      {/* Background blobs present on every page */}
      <div className="bg-blobs">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
      </div>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/github-analyzer" element={<GitHubAnalyzerPage />} />
        <Route path="/resume-upload" element={<ResumeUploadPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
