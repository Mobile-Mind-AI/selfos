const js = require("@eslint/js");
const nextPlugin = require("@next/eslint-plugin-next");

module.exports = [
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "**/*.ts",
      "**/*.tsx",
    ],
  },
  js.configs.recommended,
  {
    files: ["**/*.{js,jsx}"],
    plugins: { "@next/next": nextPlugin },
    rules: {
      ...nextPlugin.configs["core-web-vitals"].rules,
    },
    languageOptions: {
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
  },
];

