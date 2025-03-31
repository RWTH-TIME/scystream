import config from "@helpwave/eslint-config"

export default [
  ...config.nextExtension,
  {
    rules: {
      ...config.nextExtension.rules,
      "semi": ["error", "never"],
      "quotes": ["error", "double", { avoidEscape: true, allowTemplateLiterals: true }],  // Override quotes rule
      "@stylistic/quotes": ["error", "double", { avoidEscape: true, allowTemplateLiterals: true }]  // Override the @stylistic/quotes plugin rule as wellls: true }], // Override or add the quotes rule
    }
  }
]
