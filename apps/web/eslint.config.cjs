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
  {
    files: ["next.config.js"],
    languageOptions: {
      globals: { ...globals.node, module: true, exports: true, require: true, __dirname: true, __filename: true },
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "commonjs",
      },
    },
    rules: {
      // keep defaults; this override ensures CommonJS globals
    }
  }
];
