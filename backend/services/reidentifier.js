function restoreTokens(text, mapping) {
  let restoredText = text;

  Object.entries(mapping).forEach(([token, originalValue]) => {
    restoredText = restoredText.replaceAll(
      token,
      originalValue
    );
  });

  return restoredText;
}

module.exports = restoreTokens;