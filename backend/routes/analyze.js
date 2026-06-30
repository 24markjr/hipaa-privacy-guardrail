const express = require("express");

const scrubText = require("../services/scrubber");
const restoreTokens = require("../services/reidentifier");
const summarizeClinicalNote = require("../services/aiService");
const logAudit = require("../services/logger");
const supabase = require("../config/supabase");

const router = express.Router();

router.post("/", async (req, res) => {
  try {
    const startTime = Date.now();

    const { note, userId } = req.body;

    console.log("Request body:", req.body);
console.log("Received userId:", userId);

    if (!note) {
      return res.status(400).json({
        success: false,
        message: "Note is required",
      });
    }

    const scrubbed = scrubText(note);

    const aiSummary = await summarizeClinicalNote(
      scrubbed.maskedText
    );

    const finalSummary = restoreTokens(
      aiSummary,
      scrubbed.mapping
    );

    const processingTime = Date.now() - startTime;

    const requestId = `REQ-${Date.now()}`;

    logAudit({
      userId,
      requestId,
      timestamp: new Date().toISOString(),
      piiCount: scrubbed.piiCount,
      tokensCreated: Object.keys(scrubbed.mapping).length,
      processingTime,
    });

    await supabase.from("audit_logs").insert([
      {
        user_id: userId,
        request_id: requestId,
        pii_count: scrubbed.piiCount,
        tokens_created:
          Object.keys(scrubbed.mapping).length,
        processing_time: processingTime,
      },
    ]);

    res.json({
      success: true,
      originalText: note,
      maskedText: scrubbed.maskedText,
      mapping: scrubbed.mapping,
      piiCount: scrubbed.piiCount,
      aiSummary,
      finalSummary,
    });
  } catch (error) {
    console.error(error);

    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
});

module.exports = router;