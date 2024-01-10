import axios from "axios";
import { jwtDecode } from "jwt-decode";
import React, { ReactNode, createContext, useEffect, useState } from "react";

type Credentials = {
  access_token: string;
  refresh_token: string;
};

type User = {
  name: string;
  email: string;
};

interface AuthContextType {
  user: any;
  login: () => void;
  logout: () => void;
  refreshToken: () => Promise<any>;
  handleGoogleCallback: (code: string) => Promise<void>;
  reload: () => void;
  credentials: () => Credentials;
}

export const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

const parseCredentials = (credentials: Credentials): User => {
  const decodedToken = jwtDecode(credentials.access_token) as any;
  const userInfo = {
    name: decodedToken.payload.name as string,
    email: decodedToken.payload.email as string,
  } as User;
  return userInfo;
};

const openPopup = (url: string) => {
  const width = 400;
  const height = 600;
  const left = (window.innerWidth - width) / 2;
  const top = (window.innerHeight - height) / 2;
  window.open(
    url,
    "Auth",
    `toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=yes, copyhistory=no, width=${width}, height=${height}, top=${top}, left=${left}`
  );
};

// Authorization Code flow - Token swap happens on the backend
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<{
    name: string;
    email: string;
  } | null>(null);

  const login = async () => {
    try {
      const response = await axios.get("http://localhost:8000/auth/google/url");
      // window.location.href = response.data.url;
      openPopup(response.data.url);
    } catch (error) {
      console.error("Error fetching Google login URL", error);
    }
  };

  const logout = async () => {
    try {
      await axios.get("http://localhost:8000/auth/logout", {
        headers: {
          Authorization: `Bearer ${
            JSON.parse(localStorage.getItem("credentials") || "{}")
              .refresh_token
          }`,
        },
      });
    } catch (error) {
      console.error("Error fetching Google login URL", error);
    }
    localStorage.removeItem("credentials");
    setUser(null);
  };

  const refreshToken = async () => {
    try {
      const response = await axios.get("http://localhost:8000/auth/refresh", {
        headers: {
          Authorization: `Bearer ${
            JSON.parse(localStorage.getItem("credentials") || "{}")
              .refresh_token
          }`,
        },
      });
      const userInfo = parseCredentials(response.data);
      setUser(userInfo);
      localStorage.setItem("credentials", JSON.stringify(response.data));
      return JSON.parse(localStorage.getItem("credentials") || "{}");
    } catch (error) {
      console.error("Error refreshing token", error);
    }
  };

  const handleGoogleCallback = async (code: string) => {
    // Send the code to your auth server and handle the response
    const response = await axios.get(
      `http://localhost:8000/auth/google/token?code=${code}`
    );
    const userInfo = parseCredentials(response.data);
    setUser(userInfo);
    localStorage.setItem("credentials", JSON.stringify(response.data));
  };

  const reload = async () => {
    const storedCredentials = localStorage.getItem("credentials");
    if (storedCredentials) {
      // Logic to set user data based on credentials
      const credentials = JSON.parse(storedCredentials);
      const userInfo = parseCredentials(credentials);
      setUser(userInfo);
    }
  };

  const credentials = () => {
    return JSON.parse(localStorage.getItem("credentials") || "{}");
  };

  useEffect(() => {
    const storedCredentials = localStorage.getItem("credentials");
    if (storedCredentials) {
      // Logic to set user data based on credentials
      const credentials = JSON.parse(storedCredentials);
      const userInfo = parseCredentials(credentials);
      setUser(userInfo);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        refreshToken,
        handleGoogleCallback,
        reload,
        credentials,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
