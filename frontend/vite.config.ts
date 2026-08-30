/** Vite build/dev-server configuration. React transforms JSX/TSX files, while
 * the Tailwind plugin processes the Tailwind import in src/styles.css. */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({ plugins: [react(), tailwindcss()] });
