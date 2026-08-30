# Frontend

This folder contains the browser application. Vite serves and builds the project, React renders the user interface, TypeScript checks the JavaScript code, and Tailwind is imported from the stylesheet for CSS tooling.

`src/` holds the application source. `main.tsx` currently contains the complete single-page UI, its React state, and its calls to the backend API. `index.html` is the minimal document Vite loads before React renders into its `#root` element.

The frontend reads `VITE_API_URL` from `.env` (created from `.env.example`) to know where the FastAPI backend is running. It does not communicate directly with PostgreSQL.
