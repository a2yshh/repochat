"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Mail, Lock, ArrowRight } from "lucide-react";

interface SignInProps {
  onSwitchToSignUp: () => void;
}

export default function SignIn({ onSwitchToSignUp }: SignInProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { signIn } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      if (rememberMe) {
        localStorage.setItem("rememberEmail", email);
      } else {
        localStorage.removeItem("rememberEmail");
      }

      await signIn(email, password);
    } catch (err: any) {
      setError(err.message || "Sign in failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full h-screen flex items-center justify-center px-4 bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-blue-500 bg-clip-text text-transparent">
            RepoChat
          </h1>
          <p className="text-slate-400">Sign in to your account</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900/40 backdrop-blur-xl border border-white/10 rounded-2xl p-8 space-y-6 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Input */}
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium text-slate-300">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-12 pr-4 py-3 bg-slate-800/50 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 transition-all"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-12 pr-4 py-3 bg-slate-800/50 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 transition-all"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="rememberMe"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded border-slate-400 text-blue-600 focus:ring-2 focus:ring-blue-400 cursor-pointer"
                disabled={isLoading}
              />
              <label htmlFor="rememberMe" className="text-sm text-slate-400 cursor-pointer">
                Remember me
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3 text-red-200 text-sm">
                {error}
              </div>
            )}

            {/* Sign In Button */}
            <button
              type="submit"
              disabled={isLoading || !email || !password}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 disabled:from-slate-600 disabled:to-slate-700 text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-blue-500/40 disabled:shadow-none flex items-center justify-center gap-2"
            >
              {isLoading ? "Signing in..." : "Sign In"}
              {!isLoading && <ArrowRight className="w-4 h-4" />}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-white/10"></div>
            <span className="text-xs text-slate-500">OR</span>
            <div className="flex-1 h-px bg-white/10"></div>
          </div>

          {/* Sign Up Link */}
          <button
            type="button"
            onClick={onSwitchToSignUp}
            disabled={isLoading}
            className="w-full py-3 border border-white/20 hover:border-white/40 text-slate-300 hover:text-white font-medium rounded-lg transition-all"
          >
            Create a new account
          </button>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-500">
          By signing in, you agree to our Terms of Service
        </p>
      </div>
    </div>
  );
}
