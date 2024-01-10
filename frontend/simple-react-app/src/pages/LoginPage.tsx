import React, { useContext, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../auth/AuthContext";

const LoginPage: React.FC = () => {
  const authContext = useContext(AuthContext);
  const navigate = useNavigate();

  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const error = urlParams.get("error");

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (
        event.origin !== "http://localhost:3001" ||
        event.data.type !== "oauth-response"
      ) {
        return;
      }
      authContext?.reload();
      navigate("/");
    };
    window.addEventListener("message", handleMessage);
    return () => {
      window.removeEventListener("message", handleMessage);
    };
  }, [authContext, navigate]);

  return (
    <div className="w-full flex justify-center p-20">
      <div className="w-[600px] flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl">Login Page</h1>
          <p className="text-lg">To continue, please sign in with Google.</p>
        </div>
        <button className="p-2 bg-slate-300" onClick={authContext?.login}>
          Sign in with Google
        </button>
        {error && <p>{error}</p>}
      </div>
    </div>
  );
};

export default LoginPage;
