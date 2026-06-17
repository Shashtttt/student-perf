import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import NeuralAdvantage from './components/NeuralAdvantage';
import CoreCapabilities from './components/CoreCapabilities';
import Ecosystem from './components/Ecosystem';
import IntegrationSafety from './components/IntegrationSafety';
import MeasurableEvolution from './components/MeasurableEvolution';
import Footer from './components/Footer';
import LiveSessions from './components/LiveSessions';
import MentorsList from './components/MentorsList';
import LoginPage from './components/LoginPage';
import StudentDashboard from './components/StudentDashboard';
import MentorDashboard from './components/MentorDashboard';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    if (typeof window !== 'undefined') {
      return !!localStorage.getItem('aetherlearn_current_user');
    }
    return false;
  });

  const [currentUser, setCurrentUser] = useState(() => {
    if (typeof window !== 'undefined') {
      const user = localStorage.getItem('aetherlearn_current_user');
      return user ? JSON.parse(user) : null;
    }
    return null;
  });

  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('aetherlearn_current_user') ? 'Dashboard' : 'Curriculum';
    }
    return 'Curriculum';
  });

  const handleLoginSuccess = (user) => {
    localStorage.setItem('aetherlearn_current_user', JSON.stringify(user));
    setIsLoggedIn(true);
    setCurrentUser(user);
    setActiveTab('Dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('aetherlearn_current_user');
    setIsLoggedIn(false);
    setCurrentUser(null);
    setActiveTab('Curriculum');
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0b0f19] text-slate-900 dark:text-slate-100 flex flex-col font-sans antialiased selection:bg-brand-500/10 dark:selection:bg-brand-500/30 selection:text-brand-600 dark:selection:text-brand-450 transition-colors duration-300 overflow-x-hidden">
      {activeTab !== 'Login' && activeTab !== 'Dashboard' && (
        <Navbar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          isLoggedIn={isLoggedIn}
          currentUser={currentUser}
          onLogout={handleLogout}
        />
      )}
      
      <main className="flex-grow flex flex-col items-center justify-center">
        {activeTab === 'Dashboard' && isLoggedIn && (
          (currentUser?.role === 'Mentor' || currentUser?.role === 'Teacher') ? (
            <MentorDashboard 
              user={currentUser} 
              onLogout={handleLogout} 
              onUserUpdate={(updatedUser) => {
                setCurrentUser(updatedUser);
                localStorage.setItem('aetherlearn_current_user', JSON.stringify(updatedUser));
              }}
            />
          ) : (
            <StudentDashboard 
              user={currentUser} 
              onLogout={handleLogout} 
              onUserUpdate={(updatedUser) => {
                setCurrentUser(updatedUser);
                localStorage.setItem('aetherlearn_current_user', JSON.stringify(updatedUser));
              }}
            />
          )
        )}
        {activeTab === 'Curriculum' && (
          <>
            <Hero />
            <NeuralAdvantage />
            <CoreCapabilities />
            <Ecosystem />
            <IntegrationSafety />
            <MeasurableEvolution />
          </>
        )}
        {activeTab === 'Live Sessions' && <LiveSessions />}
        {activeTab === 'Mentors' && <MentorsList />}
        {activeTab === 'Login' && (
          <LoginPage 
            onBackToHome={() => setActiveTab(isLoggedIn ? 'Dashboard' : 'Curriculum')} 
            onLoginSuccess={handleLoginSuccess}
          />
        )}
      </main>

      {activeTab !== 'Login' && activeTab !== 'Dashboard' && (
        <Footer 
          setActiveTab={setActiveTab} 
          isLoggedIn={isLoggedIn}
          onLogout={handleLogout}
        />
      )}
    </div>
  );
}

export default App;
