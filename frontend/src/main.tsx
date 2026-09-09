import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import QRCode from "qrcode";
import { languages, translations, type Language } from "./i18n";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
type Kind = "static" | "dynamic";
type Theme = "light" | "dark";
type AuthMode = "login" | "register";
type Copy = Record<string, string>;
type Code = { id: number; type: Kind; destination_url: string; public_url: string; label: string | null; foreground: string; background: string; scan_count: number; is_active: boolean };

async function request(path: string, options: RequestInit = {}, token?: string) {
  const response = await fetch(`${API}${path}`, { ...options, headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers } });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Something went wrong");
  return response.status === 204 ? null : response.json();
}

function GlobeIcon() { return <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.3 2.5 3.5 5.5 3.5 9S14.3 18.5 12 21c-2.3-2.5-3.5-5.5-3.5-9S9.7 5.5 12 3Z"/></svg>; }
function ThemeIcon({ theme }: { theme: Theme }) { return theme === "dark" ? <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg> : <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 15.3A8.5 8.5 0 1 1 8.7 3.5a6.8 6.8 0 0 0 11.8 11.8Z"/></svg>; }
function GoogleIcon() { return <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285f4" d="M21.8 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.5a4.7 4.7 0 0 1-2 3.1v2.5h3.2c1.9-1.7 3.1-4.3 3.1-7.4Z"/><path fill="#34a853" d="M12 22c2.7 0 5-.9 6.7-2.4l-3.2-2.5c-.9.6-2 .9-3.5.9-2.7 0-5-1.8-5.9-4.3H2.8v2.6A10 10 0 0 0 12 22Z"/><path fill="#fbbc05" d="M6.1 13.7a6 6 0 0 1 0-3.4V7.7H2.8a10 10 0 0 0 0 8.6l3.3-2.6Z"/><path fill="#ea4335" d="M12 6c1.7 0 3.2.6 4.4 1.7l3.3-3.3A10 10 0 0 0 2.8 7.7l3.3 2.6C7 7.8 9.3 6 12 6Z"/></svg>; }

function App() {
  const [route, setRoute] = useState(window.location.pathname);
  const [token, setToken] = useState(localStorage.getItem("qr_token") || "");
  const [language, setLanguage] = useState<Language>((localStorage.getItem("qr_language") as Language) || "en");
  const [theme, setTheme] = useState<Theme>((localStorage.getItem("qr_theme") as Theme) || "light");
  const t = translations[language];

  useEffect(() => { const onPopState = () => setRoute(window.location.pathname); window.addEventListener("popstate", onPopState); return () => window.removeEventListener("popstate", onPopState); }, []);
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem("qr_theme", theme); }, [theme]);
  useEffect(() => { localStorage.setItem("qr_language", language); }, [language]);
  function navigate(path: string) { window.history.pushState({}, "", path); setRoute(path); window.scrollTo(0, 0); }
  function logout() { localStorage.removeItem("qr_token"); setToken(""); navigate("/"); }
  const isAuthPage = route === "/login" || route === "/signup";

  return <main>
    <Header token={token} language={language} theme={theme} t={t} authPage={isAuthPage} onNavigate={navigate} onLanguage={setLanguage} onTheme={() => setTheme(theme === "light" ? "dark" : "light")} onLogout={logout} />
    {isAuthPage ? <AuthPage mode={route === "/login" ? "login" : "register"} t={t} onAuthenticated={newToken => { localStorage.setItem("qr_token", newToken); setToken(newToken); navigate("/"); }} onNavigate={navigate} /> : <Home token={token} t={t} onNavigate={navigate} />}
  </main>;
}

function Header({ token, language, theme, t, authPage, onNavigate, onLanguage, onTheme, onLogout }: { token: string; language: Language; theme: Theme; t: Copy; authPage: boolean; onNavigate: (path: string) => void; onLanguage: (language: Language) => void; onTheme: () => void; onLogout: () => void }) {
  return <header><button className="brand" onClick={() => onNavigate("/")}>QR Studio</button><span className="tagline">{t.tagline}</span><div className="header-actions"><label className="language-picker"><GlobeIcon /><span className="sr-only">Language</span><select value={language} onChange={event => onLanguage(event.target.value as Language)}>{languages.map(item => <option value={item.code} key={item.code}>{item.label}</option>)}</select></label><button className="icon-button" onClick={onTheme} aria-label="Toggle color theme"><ThemeIcon theme={theme} /></button>{authPage ? <button className="quiet" onClick={() => onNavigate("/")}>{t.backToGenerator}</button> : token ? <><button className="quiet" onClick={() => document.getElementById("dashboard")?.scrollIntoView()}>{t.dashboard}</button><button className="text-button" onClick={onLogout}>{t.signOut}</button></> : <button className="quiet" onClick={() => onNavigate("/login")}>{t.signIn}</button>}</div></header>;
}

function Home({ token, t, onNavigate }: { token: string; t: Copy; onNavigate: (path: string) => void }) {
  const [url, setUrl] = useState(""); const [kind, setKind] = useState<Kind>("static"); const [label, setLabel] = useState(""); const [foreground, setForeground] = useState("#278BF5"); const [background, setBackground] = useState("#ffffff");
  const [preview, setPreview] = useState(""); const [created, setCreated] = useState<Code | null>(null); const [codes, setCodes] = useState<Code[]>([]); const [notice, setNotice] = useState("");
  const previewPayload = created?.public_url || url;
  useEffect(() => { if (previewPayload) QRCode.toDataURL(previewPayload, { width: 300, margin: 2, color: { dark: foreground, light: background } }).then(setPreview).catch(() => setPreview("")); else setPreview(""); }, [previewPayload, foreground, background]);
  useEffect(() => { if (token) loadCodes(); else setCodes([]); }, [token]);
  async function loadCodes() { try { setCodes(await request("/api/qr-codes", {}, token)); } catch { localStorage.removeItem("qr_token"); } }
  async function createCode(event: React.FormEvent) { event.preventDefault(); if (kind === "dynamic" && !token) { onNavigate("/signup"); return; } setNotice(""); setCreated(null); try { const code = await request("/api/qr-codes", { method: "POST", body: JSON.stringify({ destination_url: url, type: kind, label: label || null, foreground, background }) }, token); setCreated(code); setNotice(kind === "dynamic" ? t.dynamicCreated : t.staticCreated); if (token) loadCodes(); } catch (error) { setNotice(error instanceof Error ? error.message : "Could not create QR code"); } }
  async function download(format: "png" | "svg") { if (!created) return; try { const response = await fetch(`${API}/api/qr-codes/${created.id}/download?image_format=${format}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }); if (!response.ok) throw new Error("Download failed"); const blob = await response.blob(); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `qr-${created.id}.${format}`; link.click(); URL.revokeObjectURL(link.href); } catch (error) { setNotice(error instanceof Error ? error.message : "Download failed"); } }
  async function editDestination(code: Code) { const next = prompt(t.destination, code.destination_url); if (!next || next === code.destination_url) return; try { await request(`/api/qr-codes/${code.id}`, { method: "PATCH", body: JSON.stringify({ destination_url: next }) }, token); loadCodes(); } catch (error) { setNotice(error instanceof Error ? error.message : "Update failed"); } }
  async function remove(code: Code) { if (!confirm(`${t.delete} ${code.label || t.untitled}?`)) return; await request(`/api/qr-codes/${code.id}`, { method: "DELETE" }, token); loadCodes(); }
  const signInHint = useMemo(() => kind === "dynamic" && !token ? t.signInRequired : "", [kind, token, t]);

  return <><section className="hero"><div><p className="eyebrow">{t.heroEyebrow}</p><h1>{t.heroTitle}</h1><p className="lede">{t.heroDescription}</p></div></section><section className="studio"><form onSubmit={createCode} className="panel"><div className="tabs"><button type="button" className={kind === "static" ? "active" : ""} onClick={() => setKind("static")}>{t.static}</button><button type="button" className={kind === "dynamic" ? "active" : ""} onClick={() => setKind("dynamic")}>{t.dynamic} <small>{t.editable}</small></button></div><label>{t.destination}<input required type="url" placeholder="https://example.com" value={url} onChange={event => setUrl(event.target.value)} /></label><label>{t.label} <span>{t.optional}</span><input placeholder="Summer menu" value={label} onChange={event => setLabel(event.target.value)} /></label><div className="colors"><label>{t.ink}<input type="color" value={foreground} onChange={event => setForeground(event.target.value)} /></label><label>{t.paper}<input type="color" value={background} onChange={event => setBackground(event.target.value)} /></label></div>{signInHint && <p className="hint">{signInHint}</p>}<button className="primary">{t.generate}</button></form><div className="preview"><p className="eyebrow">{t.preview}</p>{preview ? <img src={preview} alt="QR code preview" /> : <div className="placeholder">{t.previewPlaceholder}</div>}{created && <><p className="code-url">{created.public_url}</p><div className="downloads"><button onClick={() => download("png")}>{t.downloadPng}</button><button onClick={() => download("svg")}>{t.downloadSvg}</button></div></>}</div></section>{notice && <p className="notice">{notice}</p>}{token && <section id="dashboard" className="dashboard-section"><div className="dash-title"><p className="eyebrow">{t.workspaceEyebrow}</p><h2>{t.savedCodes}</h2></div>{codes.length ? <div className="code-list">{codes.map(code => <article key={code.id}><div><strong>{code.label || t.untitled}</strong><p>{code.destination_url}</p></div><b>{code.scan_count} {t.scans}</b><button onClick={() => editDestination(code)}>{t.editLink}</button><button className="danger" onClick={() => remove(code)}>{t.delete}</button></article>)}</div> : <p className="empty">{t.noCodes}</p>}</section>}<footer>QR Studio · {t.footer}</footer></>;
}

function AuthPage({ mode, t, onAuthenticated, onNavigate }: { mode: AuthMode; t: Copy; onAuthenticated: (token: string) => void; onNavigate: (path: string) => void }) {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [notice, setNotice] = useState("");
  async function authenticate(event: React.FormEvent) { event.preventDefault(); setNotice(""); try { const data = await request(`/api/auth/${mode}`, { method: "POST", body: JSON.stringify({ email, password }) }); onAuthenticated(data.access_token); } catch (error) { setNotice(error instanceof Error ? error.message : "Could not sign in"); } }
  return <section className="auth-page"><form className="auth-card" onSubmit={authenticate}><p className="eyebrow">{t.authEyebrow}</p><h1>{mode === "login" ? t.welcomeBack : t.createAccount}</h1><p className="auth-description">{t.authDescription}</p><button type="button" className="google-button" onClick={() => setNotice(t.googleUnavailable)}><GoogleIcon />{t.google}</button><div className="divider"><span>{t.or}</span></div><label>{t.email}<input type="email" required autoComplete="email" placeholder="you@example.com" value={email} onChange={event => setEmail(event.target.value)} /></label><label>{t.password}<input type="password" required minLength={8} autoComplete={mode === "login" ? "current-password" : "new-password"} placeholder="••••••••" value={password} onChange={event => setPassword(event.target.value)} /></label>{notice && <p className="auth-notice">{notice}</p>}<button className="primary">{mode === "login" ? t.login : t.register}</button><button type="button" className="link" onClick={() => onNavigate(mode === "login" ? "/signup" : "/login")}>{mode === "login" ? t.needAccount : t.haveAccount}</button></form></section>;
}

createRoot(document.getElementById("root")!).render(<App />);
