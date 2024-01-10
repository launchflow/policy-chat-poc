import React, { useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "./AuthContext";

interface ProtectedRouteProps {
  children: JSX.Element;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const auth = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (!auth?.user) {
      // Redirect to the login page if the user is not authenticated
      navigate("/login");
    }
  }, [auth, navigate]);

  // If the user is authenticated, render the children components
  // Otherwise, this component will not render anything and the useEffect hook will handle the redirection
  return auth?.user ? children : null;
};

export default ProtectedRoute;
