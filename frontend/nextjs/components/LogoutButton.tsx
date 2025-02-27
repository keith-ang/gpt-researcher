"use client";

import React from "react";
import styles from '../styles/LogoutButton.module.css'

type LogoutButtonProps = {
  onLogout: () => void;
};

const LogoutButton: React.FC<LogoutButtonProps> = ({ onLogout }) => {
  const handleLogout = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_GPTR_API_URL}/logout`, {
        method: "POST",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Logout failed");
      }

      onLogout(); // Call parent function to handle logout logic
    } catch (error) {
      console.error("Error during logout:", error);
    }
  };

  return (
    <button onClick={handleLogout} className={styles.logoutButton}>
      Logout
    </button>
  );
};

export default LogoutButton;
