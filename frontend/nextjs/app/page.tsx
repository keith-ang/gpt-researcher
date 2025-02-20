"use client"
import { useState, useEffect } from "react";
import Home from "@/pages/Home";
import Login from "@/pages/Login";
import LogoutButton from "@/components/LogoutButton";


export default function App() {
  // Initialize as null so we know when the check is complete.
  const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(null);

  useEffect(() => {
    async function checkAuth() {
      try {
        const response = await fetch("http://localhost:8000/me", {
          method: "GET",
          credentials: "include",
        });
        setIsLoggedIn(response.ok);
      } catch (error) {
        setIsLoggedIn(false);
      }
    }
    checkAuth();
  }, []);

  if (isLoggedIn === null) {
    return <div>Loading...</div>;
  }

  return isLoggedIn ? (
    <>
      <Home />
      <LogoutButton onLogout={() => setIsLoggedIn(false)} />
    </>
  ) : (
    <Login onLogin={() => setIsLoggedIn(true)} />
  );
}
