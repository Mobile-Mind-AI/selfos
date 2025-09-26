const js = require("@eslint/js");
const nextPlugin = require("@next/eslint-plugin-next");
const globals = require("globals");

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
    files: ["**/*.{js,jsx,cjs,mjs}", "next.config.js"],
    plugins: { "@next/next": nextPlugin },
    rules: {
      ...nextPlugin.configs["core-web-vitals"].rules,
    },
    languageOptions: {
      globals: globals.node,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
  },
];
