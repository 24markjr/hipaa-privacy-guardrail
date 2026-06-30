import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import supabase from "../config/supabase";

export default function Signup() {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [dob, setDob] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const handleSignup = async () => {
    if (
      !fullName ||
      !dob ||
      !phone ||
      !email ||
      !password ||
      !confirmPassword
    ) {
      alert("Please fill all fields.");
      return;
    }

    if (password !== confirmPassword) {
      alert("Passwords do not match.");
      return;
    }

    try {
      // Create Auth User
      const { data, error } =
        await supabase.auth.signUp({
          email,
          password,
        });

      if (error) {
        alert(error.message);
        return;
      }

      // Save profile
      const { error: profileError } =
        await supabase
          .from("profiles")
          .insert([
            {
              user_id: data.user.id,
              full_name: fullName,
              dob,
              phone,
              email,
            },
          ]);

      if (profileError) {
        alert(profileError.message);
        return;
      }

      alert("Account created successfully!");

      navigate("/login");
    } catch (err) {
      console.error(err);
      alert("Something went wrong.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">

      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">

        <h1 className="text-3xl font-bold mb-6 text-center">
          Create Account
        </h1>

        <input
          className="w-full border rounded-lg p-3 mb-4"
          placeholder="Full Name"
          value={fullName}
          onChange={(e) =>
            setFullName(e.target.value)
          }
        />

        <input
          type="date"
          className="w-full border rounded-lg p-3 mb-4"
          value={dob}
          onChange={(e) =>
            setDob(e.target.value)
          }
        />

        <input
          className="w-full border rounded-lg p-3 mb-4"
          placeholder="Phone Number"
          value={phone}
          onChange={(e) =>
            setPhone(e.target.value)
          }
        />

        <input
          type="email"
          className="w-full border rounded-lg p-3 mb-4"
          placeholder="Email"
          value={email}
          onChange={(e) =>
            setEmail(e.target.value)
          }
        />

        <input
          type="password"
          className="w-full border rounded-lg p-3 mb-4"
          placeholder="Password"
          value={password}
          onChange={(e) =>
            setPassword(e.target.value)
          }
        />

        <input
          type="password"
          className="w-full border rounded-lg p-3 mb-6"
          placeholder="Confirm Password"
          value={confirmPassword}
          onChange={(e) =>
            setConfirmPassword(e.target.value)
          }
        />

        <button
          onClick={handleSignup}
          className="w-full bg-sky-500 hover:bg-sky-600 text-white py-3 rounded-lg"
        >
          Create Account
        </button>

        <p className="text-center mt-6">
          Already have an account?{" "}
          <Link
            to="/login"
            className="text-sky-600 font-semibold"
          >
            Login
          </Link>
        </p>

      </div>

    </div>
  );
}