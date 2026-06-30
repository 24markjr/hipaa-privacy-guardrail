import Card from "../components/Card";
import {
  FileText,
  Shield,
  Database,
  Bot,
  UserCheck,
  CheckCircle,
} from "lucide-react";

function Architecture() {
  const steps = [
    { title: "Clinical Note", icon: <FileText size={32} /> },
    { title: "PII Scrubber", icon: <Shield size={32} /> },
    { title: "Token Vault", icon: <Database size={32} /> },
    { title: "Gemini AI", icon: <Bot size={32} /> },
    { title: "Re-Identifier", icon: <UserCheck size={32} /> },
    { title: "Safe Response", icon: <CheckCircle size={32} /> },
  ];

  return (
    <>
      <h1 className="text-5xl font-bold mb-8">
        System Architecture
      </h1>

      <Card>
        <div className="flex flex-col items-center gap-6 py-8">

          {steps.map((step, index) => (
            <div
              key={index}
              className="flex flex-col items-center"
            >
              <div className="bg-white shadow-md rounded-2xl border border-slate-200 w-72 p-6 flex flex-col items-center">
                <div className="text-sky-500 mb-3">
                  {step.icon}
                </div>

                <h3 className="font-semibold text-lg">
                  {step.title}
                </h3>
              </div>

              {index !== steps.length - 1 && (
                <div className="text-4xl text-sky-500 my-2">
                  ↓
                </div>
              )}
            </div>
          ))}

        </div>
      </Card>
    </>
  );
}

export default Architecture;