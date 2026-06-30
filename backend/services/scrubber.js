function scrubText(text) {
  let maskedText = text;

  const mapping = {};
  let piiCount = 0;

  /*
   ==========================
   EMAIL DETECTION
   ==========================
  */

  const emailRegex =
    /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;

  let emailCounter = 1;

  maskedText = maskedText.replace(emailRegex, (match) => {
    const token = `[EMAIL_${emailCounter++}]`;

    mapping[token] = match;
    piiCount++;

    return token;
  });

  /*
   ==========================
   PHONE DETECTION
   ==========================
  */

  const phoneRegex =
    /(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g;

  let phoneCounter = 1;

  maskedText = maskedText.replace(phoneRegex, (match) => {
    const token = `[PHONE_${phoneCounter++}]`;

    mapping[token] = match;
    piiCount++;

    return token;
  });

  /*
   ==========================
   DOB DETECTION
   ==========================
   Examples:
   12/05/1985
   12-05-1985
  */

  const dobRegex =
    /\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b/g;

  let dobCounter = 1;

  maskedText = maskedText.replace(dobRegex, (match) => {
    const token = `[DOB_${dobCounter++}]`;

    mapping[token] = match;
    piiCount++;

    return token;
  });

  /*
   ==========================
   SSN DETECTION
   ==========================
   Example:
   123-45-6789
  */

  const ssnRegex =
    /\b\d{3}-\d{2}-\d{4}\b/g;

  let ssnCounter = 1;

  maskedText = maskedText.replace(ssnRegex, (match) => {
    const token = `[SSN_${ssnCounter++}]`;

    mapping[token] = match;
    piiCount++;

    return token;
  });

  /*
   ==========================
   AADHAAR DETECTION
   ==========================
   Example:
   1234 5678 9012
  */

  const aadhaarRegex =
    /\b\d{4}\s\d{4}\s\d{4}\b/g;

  let aadhaarCounter = 1;

  maskedText = maskedText.replace(aadhaarRegex, (match) => {
    const token = `[AADHAAR_${aadhaarCounter++}]`;

    mapping[token] = match;
    piiCount++;

    return token;
  });

  /*
   ==========================
   MRN DETECTION
   ==========================
   Example:
   MRN12345
   MRN-12345
  */

  const mrnRegex =
    /\bMRN[-]?\d+\b/gi;

  let mrnCounter = 1;

  maskedText = maskedText.replace(mrnRegex, (match) => {
    const token = `[MRN_${mrnCounter++}]`;

    mapping[token] = match;
    piiCount++;

    return token;
  });

  /*
   ==========================
   PATIENT NAME DETECTION
   ==========================
  */

  const names = [
    "John Doe",
    "Jane Smith",
    "Michael Brown",
    "Sarah Johnson",
    "David Wilson",
    "Robert Davis",
    "Emily Clark"
  ];

  let patientCounter = 1;

  names.forEach((name) => {
    if (maskedText.includes(name)) {
      const token = `[PATIENT_${patientCounter++}]`;

      mapping[token] = name;

      maskedText = maskedText.replaceAll(name, token);

      piiCount++;
    }
  });

  return {
    maskedText,
    mapping,
    piiCount,
  };
}

module.exports = scrubText;