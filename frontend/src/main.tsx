/**
 * The complete QR Studio browser application.
 *
 * App manages form/authentication/dashboard state, renders a client-side QR
 * preview, and calls the FastAPI API for saved QR codes. The backend remains
 * the source of truth for database records, downloads, redirects, and scans.
 */

import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import QRCode from "qrcode";
import "./styles.css";

// Vite exposes only environment variables prefixed with VITE_ to browser code.
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
type Kind = "static" | "dynamic";
type Code = { id: number; type: Kind; destination_url: string; public_url: string; label: string | null; foreground: string; background: string; scan_count: number; is_active: boolean };

async function request(path: string, options: RequestInit = {}, token?: string) {
  // One small wrapper gives every API call a shared base URL, JSON header, and
  // optional bearer token. It also turns API error responses into Error values
  // that individual UI actions can display.
  const response = await fetch(`${API}${path}`, { ...options, headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers } });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Something went wrong");
  return response.status === 204 ? null : response.json();
}

function App() {
  // localStorage survives a browser refresh, allowing the dashboard to reload
  // an existing access token without an immediate login prompt.
  const [token, setToken] = useState(localStorage.getItem("qr_token") || "");
  const [url, setUrl] = useState(""); const [kind, setKind] = useState<Kind>("static");
  const [label, setLabel] = useState(""); const [foreground, setForeground] = useState("#111827"); const [background, setBackground] = useState("#ffffff");
  const [preview, setPreview] = useState(""); const [created, setCreated] = useState<Code | null>(null); const [codes, setCodes] = useState<Code[]>([]); const [notice, setNotice] = useState("");
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [authMode, setAuthMode] = useState<"login" | "register">("register");

  const previewPayload = created?.public_url || url;
  // Effects synchronize React state with external work. Here the QR library
  // asynchronously converts the current URL/style into a data-URL preview.
  useEffect(() => { if (previewPayload) QRCode.toDataURL(previewPayload, { width: 300, margin: 2, color: { dark: foreground, light: background } }).then(setPreview).catch(() => setPreview("")); else setPreview(""); }, [previewPayload, foreground, background]);
  // Once authentication state changes, fetch the codes owned by that user.
  useEffect(() => { if (token) loadCodes(); }, [token]);
  async function loadCodes() { try { setCodes(await request("/api/qr-codes", {}, token)); } catch { logout(); } }
  function logout() { localStorage.removeItem("qr_token"); setToken(""); setCodes([]); }
  // preventDefault keeps the browser from navigating away when the HTML form
  // submits; React instead sends the JSON request and updates state in place.
  async function createCode(e: React.FormEvent) { e.preventDefault(); setNotice(""); setCreated(null); try { const code = await request("/api/qr-codes", { method: "POST", body: JSON.stringify({ destination_url: url, type: kind, label: label || null, foreground, background }) }, token); setCreated(code); setNotice(kind === "dynamic" ? "Dynamic QR code created — its destination can be changed anytime." : "Static QR code created. Download it below."); if (token) loadCodes(); } catch (err) { setNotice(err instanceof Error ? err.message : "Could not create QR code"); } }
  // authMode selects either /register or /login while both endpoints accept the
  // same email/password JSON shape and return an access token.
  async function authenticate(e: React.FormEvent) { e.preventDefault(); try { const data = await request(`/api/auth/${authMode}`, { method: "POST", body: JSON.stringify({ email, password }) }); localStorage.setItem("qr_token", data.access_token); setToken(data.access_token); setNotice("You’re signed in."); } catch (err) { setNotice(err instanceof Error ? err.message : "Could not sign in"); } }
  // Fetching a Blob allows authenticated image downloads because a normal link
  // navigation cannot attach the in-memory Authorization header.
  async function download(format: "png" | "svg") { if (!created) return; try { const response = await fetch(`${API}/api/qr-codes/${created.id}/download?image_format=${format}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }); if (!response.ok) throw new Error("Download failed"); const blob = await response.blob(); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `qr-${created.id}.${format}`; link.click(); URL.revokeObjectURL(link.href); } catch (err) { setNotice(err instanceof Error ? err.message : "Download failed"); } }
  async function editDestination(code: Code) { const next = prompt("New destination URL", code.destination_url); if (!next || next === code.destination_url) return; try { await request(`/api/qr-codes/${code.id}`, { method: "PATCH", body: JSON.stringify({ destination_url: next }) }, token); loadCodes(); } catch (err) { setNotice(err instanceof Error ? err.message : "Update failed"); } }
  async function remove(code: Code) { if (!confirm(`Delete ${code.label || "this QR code"}?`)) return; await request(`/api/qr-codes/${code.id}`, { method: "DELETE" }, token); loadCodes(); }
  // useMemo avoids recomputing derived UI text unless its two inputs change.
  const callToAction = useMemo(() => kind === "dynamic" && !token ? "Sign in is required to create a dynamic code." : "", [kind, token]);

  return <main>
    <header><a className="brand" href="/">QR Studio</a><span>URL QR codes that stay useful.</span><button className="quiet" onClick={() => document.getElementById("account")?.scrollIntoView()}>{token ? "Dashboard" : "Sign in"}</button></header>
    <section className="hero"><div><p className="eyebrow">SIMPLE. EDITABLE. SCANNABLE.</p><h1>Make every scan <em>count.</em></h1><p className="lede">Create beautiful QR codes for any link. Choose static for one-off sharing, or dynamic to edit the destination and track scans later.</p></div></section>
    <section className="studio"><form onSubmit={createCode} className="panel"><div className="tabs"><button type="button" className={kind === "static" ? "active" : ""} onClick={() => setKind("static")}>Static QR</button><button type="button" className={kind === "dynamic" ? "active" : ""} onClick={() => setKind("dynamic")}>Dynamic QR <small>editable</small></button></div><label>Destination URL<input required type="url" placeholder="https://example.com" value={url} onChange={e => setUrl(e.target.value)} /></label><label>Label <span>optional</span><input placeholder="Summer menu" value={label} onChange={e => setLabel(e.target.value)} /></label><div className="colors"><label>Ink<input type="color" value={foreground} onChange={e => setForeground(e.target.value)} /></label><label>Paper<input type="color" value={background} onChange={e => setBackground(e.target.value)} /></label></div>{callToAction && <p className="hint">{callToAction}</p>}<button className="primary" disabled={kind === "dynamic" && !token}>Generate QR code</button></form>
      <div className="preview"><p className="eyebrow">LIVE PREVIEW</p>{preview ? <img src={preview} alt="QR code preview" /> : <div className="placeholder">Your QR code will appear here</div>}{created && <><p className="code-url">{created.public_url}</p><div className="downloads"><button onClick={() => download("png")}>Download PNG</button><button onClick={() => download("svg")}>Download SVG</button></div></>}</div></section>
    {notice && <p className="notice">{notice}</p>}
    <section id="account" className="account">{!token ? <form className="auth" onSubmit={authenticate}><p className="eyebrow">SAVE YOUR DYNAMIC CODES</p><h2>{authMode === "register" ? "Create an account" : "Welcome back"}</h2><input type="email" required placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} /><input type="password" required minLength={8} placeholder="Password (8+ characters)" value={password} onChange={e => setPassword(e.target.value)} /><button className="primary">{authMode === "register" ? "Create account" : "Sign in"}</button><button type="button" className="link" onClick={() => setAuthMode(authMode === "register" ? "login" : "register")}>{authMode === "register" ? "Already have an account? Sign in" : "Need an account? Register"}</button></form> : <div className="dashboard"><div className="dash-title"><div><p className="eyebrow">YOUR WORKSPACE</p><h2>Dynamic QR codes</h2></div><button className="quiet" onClick={logout}>Sign out</button></div>{codes.length ? <div className="code-list">{codes.map(code => <article key={code.id}><div><strong>{code.label || "Untitled QR code"}</strong><p>{code.destination_url}</p></div><b>{code.scan_count} scans</b><button onClick={() => editDestination(code)}>Edit link</button><button className="danger" onClick={() => remove(code)}>Delete</button></article>)}</div> : <p className="empty">No saved QR codes yet. Create a dynamic code above to see it here.</p>}</div>}</section>
    <footer>QR Studio · Build links that last.</footer>
  </main>;
}
createRoot(document.getElementById("root")!).render(<App />);
