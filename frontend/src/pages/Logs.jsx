import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";
import supabase from "../config/supabase";

function Logs() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    async function loadLogs() {
      try {
        const {
  data: { user },
} = await supabase.auth.getUser();

if (!user) return;

const response = await api.get("/logs", {
  params: {
    userId: user.id,
  },
});

setLogs(response.data.logs || []);
      } catch (error) {
        console.error(error);
      }
    }

    loadLogs();
  }, []);

  return (
    <div className="w-full">

      <div className="mb-8">

        <h1 className="text-4xl font-bold">
          Audit Logs
        </h1>

        <p className="text-slate-500 mt-2">
          Total Requests:
          <span className="font-semibold">
            {" "}
            {logs.length}
          </span>
        </p>

      </div>

      <Card>

        {logs.length === 0 ? (

          <div className="text-center py-16">

            <h2 className="text-2xl font-bold">
              No Audit Logs Found
            </h2>

            <p className="text-slate-500 mt-3">
              Analyze a clinical note to
              generate your first audit log.
            </p>

          </div>

        ) : (

          <div className="overflow-x-auto">

            <table className="w-full border-collapse">

              <thead>

                <tr className="bg-slate-100">

                  <th className="p-4 text-left">
                    Request ID
                  </th>

                  <th className="p-4 text-center">
                    PII Count
                  </th>

                  <th className="p-4 text-center">
                    Processing Time
                  </th>

                  <th className="p-4 text-left">
                    Timestamp
                  </th>

                </tr>

              </thead>

              <tbody>

                {logs.map((log, index) => (

                  <tr
                    key={log.requestId}
                    className={`border-b hover:bg-sky-50 transition ${
                      index % 2 === 0
                        ? "bg-white"
                        : "bg-slate-50"
                    }`}
                  >

                    <td className="p-4 font-mono text-sm">
                      {log.requestId}
                    </td>

                    <td className="p-4 text-center">

                      <span className="bg-sky-100 text-sky-700 px-3 py-1 rounded-full font-semibold">
                        {log.piiCount}
                      </span>

                    </td>

                    <td className="p-4 text-center">

                      <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full font-semibold">
                        {log.processingTime} ms
                      </span>

                    </td>

                    <td className="p-4">
                      {new Date(
                        log.timestamp
                      ).toLocaleString()}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </Card>

    </div>
  );
}

export default Logs;