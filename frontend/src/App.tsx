import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import '@/index.css';

const NotFound: React.FC = () => (
  <div className="min-h-screen bg-bg-0 flex items-center justify-center text-center">
    <div>
      <p className="t-label text-text-3 mb-4">404</p>
      <h1 className="t-heading text-text-0 mb-4">Page not found</h1>
      <Link to="/" className="btn btn-outline btn-md">Return Home</Link>
    </div>
  </div>
);

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/"                  element={<LandingPage />} />
        <Route path="/upload"            element={<UploadPage />} />
        <Route path="/results/:caseId"   element={<ResultsPage />} />
        <Route path="*"                  element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;
