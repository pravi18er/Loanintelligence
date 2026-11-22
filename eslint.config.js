// @ts-check
import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["**/node_modules/**", "**/dist/**", "**/coverage/**", "reference/**"] },
  js.configs.recommended,
  ...tseslint.configs.strict,
  {
    rules: {
      // Money must never be held in a JavaScript float. Phase 1 adds
      // decimal.js; until then, block the obvious float helpers on money.
      "no-restricted-properties": [
        "error",
        { object: "Math", property: "round", message: "Use the engine's paisa rounding helper." },
        { object: "Number", property: "parseFloat", message: "Parse money with decimal.js." },
      ],
      "no-restricted-globals": [
        "error",
        { name: "parseFloat", message: "Parse money with decimal.js." },
      ],
    },
  },
);
