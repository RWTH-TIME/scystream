module.exports = {
  extends: [
    "@helpwave/eslint-config",
    "plugin:@next/next/recommended"
  ],
  rules: {
    // we want to allow double quotes
    quotes: ["error", "double", { avoidEscape: true, allowTemplateLiterals: true }],
  }
}
