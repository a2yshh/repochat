"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface User {
  id: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check if user is already logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem("authToken");
        const savedUser = localStorage.getItem("user");

        if (token && savedUser) {
          setUser(JSON.parse(savedUser));
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error("Auth check failed:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      const response = await axios.post(`${API_URL}/api/auth/signin`, {
        email,
        password,
      });

      const { token, user: userData } = response.data;
      
      localStorage.setItem("authToken", token);
      localStorage.setItem("user", JSON.stringify(userData));
      
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || "Sign in failed");
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      const response = await axios.post(`${API_URL}/api/auth/signup`, {
        email,
        password,
      });

      const { token, user: userData } = response.data;
      
      localStorage.setItem("authToken", token);
      localStorage.setItem("user", JSON.stringify(userData));
      
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || "Sign up failed");
    }
  };

  const signOut = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("user");
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
