const express = require("express");
const cors = require("cors");
require("dotenv").config();

const analyzeRoute = require("./routes/analyze");
const logsRoute = require("./routes/logs");

const app = express();

app.use(cors());
app.use(express.json());

app.use("/api/analyze", analyzeRoute);
app.use("/api/logs", logsRoute);

app.get("/", (req, res) => {
  res.send("HIPAA Privacy Proxy Running");
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});