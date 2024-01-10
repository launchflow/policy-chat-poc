import React, { useContext, useEffect } from "react";
import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AccountProvider } from "./auth/AccountContext";
import { AuthContext, AuthProvider } from "./auth/AuthContext";
import GoogleAuthCallback from "./auth/GoogleAuthCallback";
import ProtectedRoute from "./auth/ProtectedRoute";
import setupAxiosInterceptors from "./auth/setupAxiosInterceptors";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AccountProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/auth/google/callback"
              element={<GoogleAuthCallback />}
            />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </Router>
      </AccountProvider>

      <AxiosInterceptorSetup />
    </AuthProvider>
  );
};

const AxiosInterceptorSetup: React.FC = () => {
  const authContext = useContext(AuthContext);

  useEffect(() => {
    if (authContext) {
      setupAxiosInterceptors(authContext.refreshToken);
    }
  }, [authContext]);

  return null;
};

export default App;
