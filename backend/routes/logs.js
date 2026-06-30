const express = require("express");
const router = express.Router();
const supabase = require("../config/supabase");

router.get("/", async (req, res) => {
  try {
    const userId = req.query.userId;

    if (!userId) {
      return res.status(400).json({
        error: "User ID is required",
      });
    }

    const { data, error } = await supabase
      .from("audit_logs")
      .select("*")
      .eq("user_id", userId)
      .order("timestamp", {
        ascending: false,
      });

    if (error) {
      return res.status(500).json({
        error: error.message,
      });
    }

    const logs = data.map((log) => ({
      id: log.id,
      requestId: log.request_id,
      timestamp: log.timestamp,
      piiCount: log.pii_count,
      tokensCreated: log.tokens_created,
      processingTime: log.processing_time,
    }));

    res.json({ logs });
  } catch (err) {
    console.error(err);

    res.status(500).json({
      error: "Server Error",
    });
  }
});

module.exports = router;