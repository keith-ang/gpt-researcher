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
        // Retrieve token from cookies or localStorage
        const token = document.cookie
          .split("; ")
          .find((row) => row.startsWith("session="))
          ?.split("=")[1];

        const response = await fetch(`${process.env.NEXT_PUBLIC_GPTR_API_URL}/me`, {
          method: "GET",
          credentials: "include",
          headers: token ? { Authorization: `Bearer ${decodeURIComponent(token)}` } : {},
        });

        setIsLoggedIn(response.ok);
      } catch (error) {
        setIsLoggedIn(false);
      }
    }
    checkAuth();
  }, []);

  if (isLoggedIn === null) {
    return <></>;
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
