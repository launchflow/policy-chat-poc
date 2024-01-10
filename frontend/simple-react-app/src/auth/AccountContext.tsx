import axios from "axios";
import React, { createContext, useContext } from "react";
import { AuthContext } from "./AuthContext";

interface AccountContextType {
  listPolicies: () => Promise<any>;
  uploadPolicyImage: (file: File) => Promise<void>; // Added method signature for uploadPolicyImage
  policyChat: (user_inquiry: string) => Promise<string>;
}

export const AccountContext = createContext<AccountContextType | null>(null);

interface AccountProviderProps {
  children: React.ReactNode;
}

export const AccountProvider: React.FC<AccountProviderProps> = ({
  children,
}) => {
  const authContext = useContext(AuthContext);

  const listPolicies = async () => {
    if (authContext) {
      const accessToken = authContext.credentials().access_token;
      console.log("Access token: ", accessToken);

      try {
        const response = await axios.get("http://localhost:8000/list", {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
        return response.data;
      } catch (error) {
        console.error("Error fetching accounts", error);
      }
    }
  };

  const uploadPolicyImage = async (file: File) => {
    if (authContext) {
      const accessToken = authContext.credentials().access_token;

      const formData = new FormData();
      formData.append("policy_file", file);

      try {
        const response = await axios.post(
          "http://localhost:8000/upload",
          formData,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
              "Content-Type": "multipart/form-data",
            },
          }
        );
      } catch (error) {
        console.error("Error uploading policy image", error);
      }
    }
  };

  const policyChat = async (user_inquiry: string) => {
    if (authContext) {
      const accessToken = authContext.credentials().access_token;

      try {
        const response = await axios.post(
          "http://localhost:8000/chat",
          {
            user_inquiry: user_inquiry,
          },
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );
        return response.data;
      } catch (error) {
        console.error("Error fetching accounts", error);
      }
    }
  };

  return (
    <AccountContext.Provider
      value={{
        listPolicies: listPolicies,
        uploadPolicyImage: uploadPolicyImage,
        policyChat: policyChat,
      }}
    >
      {children}
    </AccountContext.Provider>
  );
};
