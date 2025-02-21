"use client"
import React, { useState } from "react";
import Head from "next/head";

type LoginProps = {
  onLogin: () => void;
};

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(""); // State to hold error message

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setError("");

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_GPTR_API_URL}/login`, {
        method: "POST",
        credentials: "include", 
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(), 
      });

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.detail || "Login failed"); 
        return;
      }

      onLogin(); 

    } catch (error) {
      console.error("Error during login:", error);
      setError("An error occurred. Please try again.");
    }
  };

  return (
    <>
      <Head>
        <title>Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </Head>
      <div style={backgroundStyle}>
        <form onSubmit={handleSubmit} style={formStyle}>
          <h2 style={headingStyle}>Login</h2>

          {error && <p style={errorStyle}>{error}</p>} {/* Display error message */}

          <div style={inputGroupStyle}>
            <label htmlFor="email" style={labelStyle}>Email:</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={inputStyle}
              required
            />
          </div>

          <div style={inputGroupStyle}>
            <label htmlFor="password" style={labelStyle}>Password:</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={inputStyle}
              required
            />
          </div>

          <button type="submit" style={buttonStyle}>Login</button>
        </form>
      </div>
    </>
  );
};

// Inline styles for the background
const backgroundStyle: React.CSSProperties = {
  background: "linear-gradient(180deg, #141a2d, #065e65)",
  minHeight: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const formStyle: React.CSSProperties = {
  backgroundColor: "#fff",
  padding: "2rem",
  borderRadius: "8px",
  boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  width: "300px",
  display: "flex",
  flexDirection: "column",
};

const headingStyle: React.CSSProperties = {
  fontSize: "2rem",
  marginBottom: "1.5rem",
  textAlign: "center",
  color: "#333",
};

const inputGroupStyle: React.CSSProperties = {
  marginBottom: "1rem",
  display: "flex",
  flexDirection: "column",
};

const labelStyle: React.CSSProperties = {
  marginBottom: "0.5rem",
  fontSize: "0.9rem",
  color: "#666",
};

const inputStyle: React.CSSProperties = {
  padding: "0.5rem",
  fontSize: "1rem",
  borderRadius: "4px",
  border: "1px solid #ccc",
};

const buttonStyle: React.CSSProperties = {
  padding: "0.75rem",
  fontSize: "1rem",
  borderRadius: "4px",
  border: "none",
  backgroundColor: "#333",
  color: "#fff",
  cursor: "pointer",
  marginTop: "1rem",
};

const errorStyle: React.CSSProperties = {
  color: "red",
  fontSize: "0.9rem",
  textAlign: "center",
  marginBottom: "1rem",
};

export default Login;