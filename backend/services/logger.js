const fs = require("fs");
const path = require("path");

const logFile =
  path.join(
    __dirname,
    "../data/auditLogs.json"
  );

function logAudit(entry) {

  let logs = [];

  if (fs.existsSync(logFile)) {
    logs = JSON.parse(
      fs.readFileSync(logFile)
    );
  }

  logs.push(entry);

  fs.writeFileSync(
    logFile,
    JSON.stringify(logs, null, 2)
  );
}

module.exports = logAudit;