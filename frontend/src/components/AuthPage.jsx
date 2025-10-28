import React, { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

const serverBaseURL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

export default function AuthPage() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ username: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const endpoint = isLogin
        ? `${serverBaseURL}/api/auth/login`
        : `${serverBaseURL}/api/auth/register`;

      const payload = isLogin
        ? { email: formData.email, password: formData.password }
        : { username: formData.username, email: formData.email, password: formData.password };

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Something went wrong");
      }

      if (isLogin) {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("username", data.username);
        localStorage.setItem("email", data.email);

        setSuccess("Login successful!");
        setTimeout(() => navigate("/"), 1000);
      } else {
        setSuccess("Registration successful! Please login.");
        setIsLogin(true);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* ✅ All styling unchanged */}
      <style>{`
        .auth-page {
          position: relative;
          min-height: 100vh;
          display: flex;
          justify-content: center;
          align-items: center;
          overflow: hidden;
          background: linear-gradient(to bottom, #000000, #0f172a, #1e293b);
          color: white;
          font-family: 'Poppins', sans-serif;
        }

        .auth-page::before,
        .auth-page::after {
          content: "";
          position: absolute;
          width: 600px;
          height: 600px;
          border-radius: 50%;
          filter: blur(120px);
          opacity: 0.25;
          z-index: 1;
        }
        .auth-page::before {
          top: -150px;
          left: -200px;
          background: rgba(0, 255, 255, 0.5);
        }
        .auth-page::after {
          bottom: -150px;
          right: -200px;
          background: rgba(0, 114, 255, 0.5);
        }

        .auth-card {
          position: relative;
          z-index: 2;
          width: 420px;
          padding: 2.5rem;
          border-radius: 20px;
          background: rgba(30, 41, 59, 0.6);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(0, 255, 255, 0.3);
          box-shadow: 0 0 30px rgba(0, 255, 255, 0.2);
          text-align: center;
        }

        h2 {
          font-size: 2rem;
          font-weight: 700;
          color: #00e0ff;
          text-shadow: 0 0 12px rgba(0, 255, 255, 0.4);
          margin-bottom: 0.4rem;
        }

        p {
          font-size: 0.95rem;
          color: #a9b3c1;
          margin-bottom: 1.5rem;
        }

        .input-group {
          margin-bottom: 1rem;
        }

        .input-group input {
          width: 100%;
          padding: 12px 15px;
          border-radius: 10px;
          border: none;
          outline: none;
          background: rgba(255, 255, 255, 0.1);
          color: white;
          font-size: 1rem;
          transition: all 0.3s ease;
        }

        .input-group input:focus {
          box-shadow: 0 0 10px #00e0ff;
        }

        .auth-btn {
          width: 100%;
          padding: 12px;
          border: none;
          border-radius: 10px;
          background: linear-gradient(135deg, #00e0ff, #0072ff);
          color: white;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: 0.3s ease;
          margin-top: 0.5rem;
        }

        .auth-btn:hover {
          transform: scale(1.05);
          box-shadow: 0 0 15px #00e0ff;
        }

        .switch-text {
          margin-top: 1rem;
          color: #bbb;
          font-size: 0.9rem;
        }

        .switch-text span {
          color: #00e0ff;
          cursor: pointer;
          text-decoration: underline;
        }

        .back-btn {
          margin-top: 1.5rem;
          background: transparent;
          border: 1px solid #00e0ff;
          color: #00e0ff;
          padding: 8px 20px;
          border-radius: 10px;
          cursor: pointer;
          transition: 0.3s ease;
        }

        .back-btn:hover {
          background: #00e0ff;
          color: #111;
          box-shadow: 0 0 12px #00e0ff;
        }
      `}</style>

      <div className="auth-page">
        <motion.div
          className="auth-card"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h2>{isLogin ? "Welcome Back 👋" : "Create Account ✨"}</h2>
          <p>{isLogin ? "Login to explore CineSense" : "Join CineSense for personalized recommendations"}</p>

          {error && <p style={{ color: "#ff6b6b" }}>{error}</p>}
          {success && <p style={{ color: "#00ffb3" }}>{success}</p>}

          <form onSubmit={handleSubmit}>
            {!isLogin && (
              <div className="input-group">
                <input
                  type="text"
                  name="username"
                  placeholder="Username"
                  value={formData.username}
                  onChange={handleChange}
                  required={!isLogin}
                />
              </div>
            )}

            <div className="input-group">
              <input
                type="email"
                name="email"
                placeholder="Email Address"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="input-group">
              <input
                type="password"
                name="password"
                placeholder={isLogin ? "Password" : "Create Password"}
                value={formData.password}
                onChange={handleChange}
                required
                minLength={6}
              />
            </div>

            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? "Processing..." : isLogin ? "Login" : "Register"}
            </button>
          </form>

          <p className="switch-text">
            {isLogin ? "Don’t have an account? " : "Already have an account? "}
            <span onClick={() => setIsLogin(!isLogin)}>
              {isLogin ? "Register" : "Login"}
            </span>
          </p>

          <button className="back-btn" onClick={() => navigate("/")}>
            ⬅ Back
          </button>
        </motion.div>
      </div>
    </>
  );
}
