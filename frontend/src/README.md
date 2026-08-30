# Frontend source

`main.tsx` defines the React application. It manages form values, authentication state, QR preview generation, API requests, and the dashboard view. `styles.css` supplies the visual layout and responsive styling.

The React application communicates only with the FastAPI API through `fetch`. The browser-generated QR preview is immediate feedback; the backend remains the source of truth for saved QR records and download files.
