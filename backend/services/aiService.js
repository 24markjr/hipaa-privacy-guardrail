const { GoogleGenAI } = require("@google/genai");

const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API_KEY,
});

async function summarizeClinicalNote(text) {
  const prompt = `
You are an experienced clinical AI assistant.

The following clinical note has already been de-identified for HIPAA compliance.

Your task is to:

1. Produce a concise clinical summary.
2. Mention the patient's main symptoms.
3. Mention likely diagnosis.
4. Mention treatments or medications.
5. Mention recommended follow-up.

Do NOT invent facts.
Use only the information present.

Clinical Note:

${text}
`;

  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: prompt,
  });

  return response.text;
}

module.exports = summarizeClinicalNote;