import React, { useContext, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AccountContext } from "../auth/AccountContext";
import { AuthContext } from "../auth/AuthContext";

const HomePage: React.FC = () => {
  const authContext = useContext(AuthContext);
  const accountContext = useContext(AccountContext);
  const [inquiry, setInquiry] = useState<string>(""); // State to track inquiry
  const [policies, setPolicies] = useState<any>(null); // State to track policies
  const [chatResponse, setChatResponse] = useState<string | null>(null); // State to track chat response

  const navigate = useNavigate();
  const [loading, setLoading] = useState(false); // State to track loading
  const fileInputRef = useRef<HTMLInputElement>(null); // Ref for the file input

  if (!authContext) {
    return <div>Loading...</div>;
  }

  const handleListPolicies = async () => {
    setLoading(true);
    setPolicies(null); // Reset policies state
    try {
      const result = await accountContext?.listPolicies();
      setPolicies(
        result?.map((policy: any) => (
          <div>
            {Object.entries(policy).map(([key, value]: any) => (
              <p>
                {key}: {value}
              </p>
            ))}
            <img src={policy.image_url} alt="Policy" />
          </div>
        ))
      );
    } catch (error) {
      console.error("Error listing policies", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (event.target.files && event.target.files[0]) {
      setLoading(true);
      const file = event.target.files[0];
      try {
        await accountContext?.uploadPolicyImage(file); // Using the uploadPolicyImage method
      } catch (error) {
        console.error("Error uploading file", error);
      } finally {
        setLoading(false);
        // Reset the file input
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    }
  };
  const handleInquiry = async () => {
    setLoading(true);
    try {
      const response = await accountContext?.policyChat(inquiry);
      setChatResponse(response || null);
    } catch (error) {
      console.error("Error sending inquiry", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full flex justify-center p-20">
      <div className="w-[600px] flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl">Home Page</h1>
          <p className="text-lg">
            Hi {authContext?.user.name}, your email is {authContext?.user.email}
          </p>
        </div>
        <button
          className="p-2 bg-slate-300 w-[600px]"
          onClick={() => {
            authContext.logout();
            navigate("/login");
          }}
        >
          Logout
        </button>

        {/* Upload Button */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          style={{ display: "none" }} // Hide the actual file input
        />
        <button
          className="p-2 bg-slate-300 w-[600px]"
          onClick={() => fileInputRef.current?.click()} // Trigger file input click
          disabled={loading}
        >
          Upload Policy Image
        </button>

        <button
          className="p-2 bg-slate-300 w-[600px]"
          onClick={handleListPolicies}
          disabled={loading}
        >
          List Policies
        </button>

        {loading && <div className="text-center text-xl">Loading...</div>}

        {policies && (
          <div className="flex flex-col gap-2">
            <h1 className="text-4xl">Policies:</h1>
            {policies}
          </div>
        )}

        <div>
          <input
            type="text"
            value={inquiry}
            onChange={(e) => setInquiry(e.target.value)}
            placeholder="Enter your inquiry"
            className="p-2 border border-gray-300 rounded w-full"
          />
          <button
            className="p-2 bg-slate-300 w-[600px] mt-2"
            onClick={handleInquiry}
            disabled={loading}
          >
            Send Inquiry
          </button>
        </div>

        {chatResponse && (
          <div>
            <h2 className="text-3xl mt-4">Response:</h2>
            <p>{chatResponse}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;
