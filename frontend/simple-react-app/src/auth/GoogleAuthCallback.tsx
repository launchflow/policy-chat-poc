import React, { useContext, useEffect } from "react";
import { AuthContext } from "./AuthContext";

const GoogleAuthCallback: React.FC = () => {
  const authContext = useContext(AuthContext);

  useEffect(() => {
    // Post the message to the opener window
    if (window.opener && !window.opener.closed) {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get("code");

      if (code && authContext) {
        authContext.handleGoogleCallback(code).then(() => {
          const authData = {
            type: "oauth-response",
            success: true,
          };
          window.opener.postMessage(authData, "http://localhost:3001/login");
          window.close();
        });
      }
    }
  }, [authContext]);

  return (
    <div className="w-full p-20">
      <p className="text-4xl text-center">Loading...</p>
    </div>
  );
};

export default GoogleAuthCallback;
