import config from "@helpwave/eslint-config"

export default [
  ...config.nextExtension,
  {
    rules: {
      "semi": ["error", "never"],
      "quotes": ["error", "double", { avoidEscape: true, allowTemplateLiterals: true }],
      "@stylistic/quotes": ["error", "double", { avoidEscape: true, allowTemplateLiterals: true }],
    },
  },
  // Override for generated Next.js file
  {
    files: ["next-env.d.ts"],
    rules: {
      "@typescript-eslint/triple-slash-reference": "off",
    },
  },
]

