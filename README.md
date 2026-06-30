# 🏥 HIPAA Privacy Proxy MVP

A full-stack AI-powered healthcare application that protects sensitive patient information before sending clinical notes to a Large Language Model (Google Gemini) for analysis.

The application automatically detects and masks Personally Identifiable Information (PII/PHI), sends only de-identified data to Gemini AI, restores the original information after analysis, and stores audit logs for compliance.

---

## 🚀 Live Demo

**Frontend (Vercel)**  
https://hipaa-privacy-guardrail.vercel.app

**Backend (Render)**  
https://hipaa-privacy-guardrail.onrender.com

---

## ✨ Features

- 🔒 Automatic PHI/PII masking
- 🤖 AI-powered clinical note summarization using Google Gemini
- 🔁 Secure token restoration after AI analysis
- 📋 Audit logging for every request
- ☁️ Cloud deployment using Vercel and Render
- 🗄️ Audit logs stored in Supabase
- ⚡ Fast React frontend
- 🌐 RESTful Express.js backend

---

## 🏗️ System Architecture

```
                Clinical Note
                      │
                      ▼
             React Frontend (Vercel)
                      │
                      ▼
          Express Backend (Render)
                      │
      ┌───────────────┴───────────────┐
      │                               │
      ▼                               ▼
 PHI Scrubber                 Audit Logger
      │                               │
      ▼                               ▼
Masked Clinical Note          Supabase Database
      │
      ▼
 Google Gemini API
      │
      ▼
AI Clinical Summary
      │
      ▼
Re-identification Engine
      │
      ▼
Final Restored Clinical Summary
```

---

## 🛠️ Tech Stack

### Frontend
- React
- Vite
- Axios
- CSS

### Backend
- Node.js
- Express.js
- Google Gemini API
- Supabase
- dotenv

### Database
- Supabase PostgreSQL

### Deployment
- Vercel
- Render

---

## 📂 Project Structure

```
hipaa-privacy-guardrail/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── services/
│   └── ...
│
├── backend/
│   ├── config/
│   ├── routes/
│   ├── services/
│   ├── server.js
│   └── ...
│
└── README.md
```

---

## 🔄 Workflow

1. User submits a clinical note.
2. Sensitive patient information is detected and masked.
3. The de-identified note is sent to Google Gemini.
4. Gemini generates a clinical summary.
5. Original patient information is restored.
6. An audit log is recorded in Supabase.
7. The final summary is returned to the user.

---

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/Yami2912/hipaa-privacy-guardrail.git
```

### Backend

```bash
cd backend
npm install
npm run dev
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🔐 Security

- Patient identifiers are masked before AI processing.
- Sensitive API keys are managed through secure environment variables.
- Audit logs provide traceability for requests.
- The application demonstrates a HIPAA-inspired de-identification workflow.

---

## 🚧 Future Improvements

- User authentication
- Role-based access control
- PDF report generation
- OCR support for scanned medical records
- Exportable analysis history
- Docker containerization
- Unit and integration testing

---

## 👩‍💻 Author

**Yami Patel**

GitHub: https://github.com/Yami2912

---

## 📄 License

This project is intended for educational and portfolio purposes. It demonstrates secure handling of clinical text using AI and is not intended for production healthcare environments without additional compliance, security, and regulatory measures.
