import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";
import supabase from "../config/supabase";

import {
  FileText,
  ShieldAlert,
  BarChart3,
} from "lucide-react";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

function Dashboard() {
  const [stats, setStats] = useState({
    totalDocuments: 0,
    totalPii: 0,
    avgTime: 0,
  });

  const [chartData, setChartData] = useState([]);
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        

        // Logged in user
const {
  data: { user },
} = await supabase.auth.getUser();

if (!user) return;

setUserEmail(user.email);

// Dashboard data
const response = await api.get("/logs", {
  params: {
    userId: user.id,
  },
});

const logs = response.data.logs || [];

        setStats({
          totalDocuments: logs.length,
          totalPii: logs.reduce(
            (sum, log) => sum + (log.piiCount || 0),
            0
          ),
          avgTime:
            logs.length > 0
              ? Math.round(
                  logs.reduce(
                    (sum, log) =>
                      sum + (log.processingTime || 0),
                    0
                  ) / logs.length
                )
              : 0,
        });

        const grouped = {};

        logs.forEach((log) => {
          const day = new Date(
            log.timestamp
          ).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          });

          grouped[day] =
            (grouped[day] || 0) +
            (log.piiCount || 0);
        });

        setChartData(
          Object.entries(grouped).map(
            ([day, pii]) => ({
              day,
              pii,
            })
          )
        );
      } catch (error) {
        console.error(error);
      }
    }

    loadDashboard();
  }, []);

  async function handleLogout() {
    await supabase.auth.signOut();
    window.location.href = "/login";
  }

  return (
    <div className="w-full">

      <div className="flex justify-between items-center mb-8">

        <div>
          <h1 className="text-4xl font-bold">
            Dashboard
          </h1>

          {userEmail && (
            <p className="text-slate-500 mt-2">
              Welcome,
              <span className="font-semibold">
                {" "}
                {userEmail}
              </span>
            </p>
          )}
        </div>

        <button
          onClick={handleLogout}
          className="bg-red-500 hover:bg-red-600 text-white px-5 py-2 rounded-lg"
        >
          Logout
        </button>

      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-8">

        <Card>
          <div className="flex justify-between items-center">
            <div>
              <p className="text-gray-500">
                Documents Processed
              </p>

              <h2 className="text-4xl font-bold mt-2">
                {stats.totalDocuments}
              </h2>
            </div>

            <FileText
              size={40}
              className="text-sky-500"
            />
          </div>
        </Card>

        <Card>
          <div className="flex justify-between items-center">
            <div>
              <p className="text-gray-500">
                PII Removed
              </p>

              <h2 className="text-4xl font-bold mt-2">
                {stats.totalPii}
              </h2>
            </div>

            <ShieldAlert
              size={40}
              className="text-sky-500"
            />
          </div>
        </Card>

        <Card>
          <div className="flex justify-between items-center">
            <div>
              <p className="text-gray-500">
                Avg Processing Time
              </p>

              <h2 className="text-4xl font-bold mt-2">
                {stats.avgTime} ms
              </h2>
            </div>

            <BarChart3
              size={40}
              className="text-sky-500"
            />
          </div>
        </Card>

      </div>

      <Card title="PII Elements Over Time">

        <div className="h-96">

          <ResponsiveContainer
            width="100%"
            height="100%"
          >

            <LineChart data={chartData}>

              <CartesianGrid strokeDasharray="3 3" />

              <XAxis dataKey="day" />

              <YAxis />

              <Tooltip />

              <Line
                type="monotone"
                dataKey="pii"
                stroke="#0ea5e9"
                strokeWidth={3}
              />

            </LineChart>

          </ResponsiveContainer>

        </div>

      </Card>

    </div>
  );
}

export default Dashboard;