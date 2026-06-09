from flask import Blueprint, redirect, request, session, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.auth.microsoft import get_auth_url, get_token_from_code, get_user_info
from flask import current_app
from flask import abort
import uuid

# In-memory store for MSAL auth flows to avoid serializing complex objects into session cookie
FLOWS = {}
auth_bp = Blueprint("auth", __name__)

def _assign_role(email: str) -> str:
    if email == "21279@student.ans-elblag.pl":
        return "administrator"
    domain = email.split("@")[-1].lower()
    student_domain = current_app.config["STUDENT_DOMAIN"].lower()
    staff_domain   = current_app.config["STAFF_DOMAIN"].lower()
    if domain == student_domain:
        return "student"
    elif domain == staff_domain:
        return "pending"
    else:
        return "no_access"

def _role_badge(role: str) -> str:
    labels = {
        'administrator': 'Administrator', 'admin': 'Administrator',
        'student': 'Student', 'opiekun': 'Opiekun',
        'dziekanat': 'Dziekanat', 'sekretariat': 'Sekretariat',
        'dyrekcja': 'Dyrekcja', 'pending': 'Oczekujący',
    }
    label = labels.get(role, role)
    return f'<span class="adm-badge role-{role}"><span class="adm-badge-dot"></span>{label}</span>'

def _avatar_letters(full_name: str) -> str:
    parts = (full_name or "").strip().split()
    if len(parts) >= 2:
        return parts[0][0].upper() + parts[-1][0].upper()
    return (full_name or "??")[:2].upper()


# ──────────────────────────────────────────────
# DESIGN SYSTEM — identyczny jak users.html
# ──────────────────────────────────────────────
_CSS = """
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --navy:         #1a2744;
    --accent:       #3b5bdb;
    --accent-hover: #2f4ac0;
    --teal:         #0d9488;
    --red:          #dc2626;
    --red-light:    #fef2f2;
    --amber:        #d97706;
    --amber-light:  #fffbeb;
    --green:        #16a34a;
    --green-light:  #f0fdf4;
    --bg:           #f0f2f7;
    --surface:      #ffffff;
    --surface-2:    #f8f9fc;
    --border:       #dde1ef;
    --border-light: #eaecf5;
    --text:         #111827;
    --text-mid:     #374151;
    --text-muted:   #6b7280;
    --text-light:   #9ca3af;
    --shadow-sm:    0 1px 3px rgba(26,39,68,.08);
    --shadow-lg:    0 8px 32px rgba(26,39,68,.13);
    --radius:       10px;
    --radius-sm:    6px;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'IBM Plex Sans', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; }

  /* ── Navbar (identyczny jak users.html) ── */
  nav.ans-navbar {
    background: var(--navy);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 28px; height: 68px;
    box-shadow: 0 2px 12px rgba(0,0,0,.18);
    flex-shrink: 0;
  }
  nav.ans-navbar a.brand { display: flex; align-items: center; gap: 14px; text-decoration: none; }
  nav.ans-navbar a.brand img { height: 44px; background: white; padding: 4px; border-radius: 4px; }
  nav.ans-navbar .brand-text { color: #fff; line-height: 1.2; }
  nav.ans-navbar .brand-text > strong { font-size: 15px; font-weight: 700; display: block; color: #fff; }
  nav.ans-navbar .brand-text span { font-size: 12px; font-weight: 300; color: rgba(255,255,255,.65); }
  nav.ans-navbar > nav { display: flex; align-items: center; gap: 4px; }
  nav.ans-navbar > nav a { color: rgba(255,255,255,.75); text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 13.5px; font-weight: 500; transition: all .15s; }
  nav.ans-navbar > nav a:hover { color: #fff; background: rgba(255,255,255,.1); }
  nav.ans-navbar > nav a.btn-logout { background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.2); color: #fff; }

  /* ── Header strip ── */
  .ans-header-strip { height: 4px; background: linear-gradient(90deg, #3b5bdb 0%, #0d9488 100%); flex-shrink: 0; }

  /* ── Footer ── */
  .ans-footer { padding: 18px; text-align: center; color: var(--text-muted); font-size: 12px; border-top: 1px solid var(--border); background: var(--surface); margin-top: auto; }

  /* ── Page header ── */
  .page-header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 22px 0; }
  .page-header-inner { max-width: 1180px; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
  .page-title-group h1 { font-size: 22px; font-weight: 700; color: var(--navy); letter-spacing: -.3px; }
  .breadcrumb { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--text-muted); margin-top: 4px; }
  .breadcrumb a { color: var(--accent); text-decoration: none; }
  .breadcrumb a:hover { text-decoration: underline; }

  /* ── Container ── */
  .ans-container { max-width: 1180px; margin: 0 auto; padding: 0 24px 40px; flex: 1; }

  /* ── Welcome banner ── */
  .welcome-banner { display: flex; align-items: center; gap: 16px; background: var(--navy); padding: 22px 24px; border-radius: var(--radius); margin-top: 28px; box-shadow: var(--shadow-sm); }
  .welcome-avatar { background: rgba(255,255,255,.15); color: #fff; width: 56px; height: 56px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; }
  .welcome-text h2 { font-size: 19px; font-weight: 700; color: #fff; }
  .welcome-text p  { font-size: 13px; color: rgba(255,255,255,.65); margin-top: 3px; }

  /* ── Stats row ── */
  .stats-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; padding: 24px 0 0; }
  .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px 20px; box-shadow: var(--shadow-sm); display: flex; align-items: center; gap: 14px; }
  .stat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 20px; }
  .stat-icon.blue  { background: #eff3ff; }
  .stat-icon.green { background: var(--green-light); }
  .stat-icon.amber { background: var(--amber-light); }
  .stat-icon.red   { background: var(--red-light); }
  .stat-val   { font-size: 26px; font-weight: 700; color: var(--navy); letter-spacing: -.5px; line-height: 1; }
  .stat-label { font-size: 12px; color: var(--text-muted); margin-top: 2px; font-weight: 500; }

  /* ── Info cards grid ── */
  .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap: 16px; padding: 24px 0 0; }
  .info-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px 20px; box-shadow: var(--shadow-sm); }
  .card-label { font-size: 11.5px; font-weight: 600; text-transform: uppercase; letter-spacing: .6px; color: var(--text-muted); margin-bottom: 6px; }
  .card-value { font-size: 15px; font-weight: 600; color: var(--navy); }

  /* ── Action panel ── */
  .action-panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 22px 24px; box-shadow: var(--shadow-sm); margin-top: 24px; }
  .action-panel h3 { font-size: 16px; font-weight: 700; color: var(--navy); margin-bottom: 4px; }
  .action-panel > p { font-size: 13px; color: var(--text-muted); margin-bottom: 16px; }
  .action-links { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: 12px; }
  .action-link { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border-radius: var(--radius-sm); text-decoration: none; border: 1px solid var(--border); background: var(--surface); transition: all .15s; }
  .action-link:hover { border-color: var(--accent); background: #f5f7ff; }
  .action-link.primary { border-color: var(--accent); background: #eff3ff; }
  .action-link-icon { font-size: 22px; flex-shrink: 0; }
  .action-link-text strong { display: block; font-size: 14px; font-weight: 700; color: var(--navy); }
  .action-link-text span   { font-size: 12px; color: var(--text-muted); }

  /* ── Badges (identyczne jak users.html) ── */
  .adm-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: 20px; font-size: 11.5px; font-weight: 600; white-space: nowrap; }
  .adm-badge-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
  .role-administrator, .role-admin { background: #eff3ff; color: #3b5bdb; }
  .role-administrator .adm-badge-dot, .role-admin .adm-badge-dot { background: #3b5bdb; }
  .role-student    { background: var(--green-light); color: var(--green); }
  .role-student    .adm-badge-dot { background: var(--green); }
  .role-dziekanat  { background: var(--amber-light); color: var(--amber); }
  .role-dziekanat  .adm-badge-dot { background: var(--amber); }
  .role-sekretariat{ background: #f0fdf4; color: #15803d; }
  .role-sekretariat .adm-badge-dot { background: #15803d; }
  .role-dyrekcja   { background: #fdf4ff; color: #9333ea; }
  .role-dyrekcja   .adm-badge-dot { background: #9333ea; }
  .role-opiekun    { background: #f0fdfa; color: #0d9488; }
  .role-opiekun    .adm-badge-dot { background: #0d9488; }
  .role-pending    { background: var(--amber-light); color: var(--amber); }
  .role-pending    .adm-badge-dot { background: var(--amber); }

  /* ── Buttons ── */
  .btn-adm { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: var(--radius-sm); font-size: 13.5px; font-weight: 600; font-family: inherit; cursor: pointer; border: none; text-decoration: none; transition: all .15s; white-space: nowrap; }
  .btn-adm-primary { background: var(--accent); color: #fff !important; }
  .btn-adm-primary:hover { background: var(--accent-hover); }
  .btn-adm-ghost { background: transparent; color: var(--text-mid) !important; border: 1px solid var(--border); }
  .btn-adm-ghost:hover { background: var(--surface-2); }

  /* ── Login ── */
  .login-wrap { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 20px; }
  .login-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; box-shadow: var(--shadow-lg); padding: 40px 44px; text-align: center; width: 100%; max-width: 420px; }
  .login-logo { height: 72px; margin-bottom: 20px; }
  .login-card h1 { font-size: 20px; font-weight: 700; color: var(--navy); }
  .login-card p  { font-size: 13.5px; color: var(--text-muted); margin: 8px 0 28px; line-height: 1.6; }
  .btn-microsoft { display: inline-flex; align-items: center; justify-content: center; gap: 10px; width: 100%; padding: 12px 20px; background: var(--navy); color: #fff !important; border-radius: var(--radius-sm); font-size: 14px; font-weight: 600; text-decoration: none; transition: background .15s; }
  .btn-microsoft:hover { background: #253460; }
  .btn-microsoft svg { width: 20px; height: 20px; }

  /* ── Local login form ── */
  .login-divider { display: flex; align-items: center; gap: 12px; margin: 22px 0 18px; color: var(--text-light); font-size: 12px; }
  .login-divider::before, .login-divider::after { content: ''; flex: 1; height: 1px; background: var(--border); }
  .login-form { text-align: left; }
  .login-field { display: flex; flex-direction: column; gap: 5px; margin-bottom: 14px; }
  .login-field label { font-size: 12px; font-weight: 600; color: var(--text-mid); text-transform: uppercase; letter-spacing: .4px; }
  .login-field input { border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 9px 12px; font-size: 14px; font-family: inherit; color: var(--text); background: var(--surface); outline: none; transition: border .15s, box-shadow .15s; width: 100%; }
  .login-field input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(59,91,219,.12); }
  .btn-local-login { width: 100%; padding: 11px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-sm); font-size: 14px; font-weight: 600; font-family: inherit; cursor: pointer; transition: background .15s; margin-top: 4px; }
  .btn-local-login:hover { background: var(--accent-hover); }
  .login-error { background: var(--red-light); border: 1px solid #fca5a5; border-radius: var(--radius-sm); padding: 10px 14px; font-size: 13px; color: #991b1b; margin-bottom: 14px; text-align: left; }
  /* ── Dev quick-login buttons ── */
  .dev-roles { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .dev-role-btn { display: block; padding: 8px 10px; border-radius: var(--radius-sm); font-size: 12.5px; font-weight: 600; text-decoration: none; text-align: center; transition: opacity .15s; border: 1px solid transparent; }
  .dev-role-btn:hover { opacity: .85; }
  .dev-role-btn.role-student   { background: var(--green-light);  color: var(--green);  border-color: #bbf7d0; }
  .dev-role-btn.role-opiekun   { background: #eff3ff;             color: var(--accent); border-color: #c7d2fe; }
  .dev-role-btn.role-dziekanat { background: var(--amber-light);  color: var(--amber);  border-color: #fde68a; }
  .dev-role-btn.role-admin     { background: var(--red-light);    color: var(--red);    border-color: #fecaca; }

  /* ── Error page ── */
  .error-wrap { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 20px; }
  .error-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow-sm); padding: 48px 40px; text-align: center; max-width: 520px; width: 100%; }
  .error-code { font-size: 72px; font-weight: 700; color: var(--border); line-height: 1; font-family: 'IBM Plex Mono', monospace; }
  .error-card h2 { font-size: 22px; font-weight: 700; color: var(--navy); margin: 12px 0 8px; }
  .error-card p  { font-size: 14px; color: var(--text-muted); margin-bottom: 24px; }

  /* ── Alert ── */
  .ans-alert { background: var(--amber-light); border: 1px solid #fcd34d; border-radius: var(--radius-sm); padding: 14px 16px; font-size: 13px; color: #78350f; text-align: left; margin-bottom: 20px; }
  .ans-alert ul { padding-left: 18px; margin: 6px 0 0; }
  .ans-alert a { color: var(--navy); }

  @media (max-width: 900px) { .stats-row { grid-template-columns: 1fr 1fr; } }
  @media (max-width: 600px) { .stats-row { grid-template-columns: 1fr; } .login-card { padding: 28px 24px; } }
</style>
"""

def _base(title, navbar_html, content_html):
    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} – System Praktyk ANS</title>
  {_CSS}
</head>
<body>
{navbar_html}
<div class="ans-header-strip"></div>
{content_html}
<footer class="ans-footer">
  &copy; 2026 <strong>Akademia Nauk Stosowanych w Elblągu</strong> – System Obsługi Praktyk
</footer>
</body>
</html>"""

def _navbar_logged(role: str = ''):
    role_links = {
        'student':       '<a href="/student/">Panel studenta</a>',
        'opiekun':       '<a href="/opiekun/dashboard">Panel opiekuna</a>',
        'dziekanat':     '<a href="/dziekanat/">Panel dziekanatu</a>',
        'sekretariat':   '<a href="/dziekanat/">Panel sekretariatu</a>',
        'dyrekcja':      '<a href="/dziekanat/">Panel dyrekcji</a>',
        'admin':         '<a href="/admin/">Panel admina</a>',
        'administrator': '<a href="/admin/">Panel admina</a>',
    }
    extra = role_links.get(role, '')
    return f"""
<nav class="ans-navbar">
  <a class="brand" href="/auth/dashboard">
    <img src="/static/img/logo.png" alt="ANS Logo" onerror="this.style.display='none'">
    <div class="brand-text">
      <strong>Akademia Nauk Stosowanych</strong>
      <span>w Elblągu – System Praktyk</span>
    </div>
  </a>
  <nav>
    <a href="/auth/dashboard">Dashboard</a>
    {extra}
    <a href="/auth/regulamin">Regulamin PZ</a>
    <a href="/auth/logout" class="btn-logout">Wyloguj</a>
  </nav>
</nav>"""

def _navbar_guest():
    return """
<nav class="ans-navbar">
  <a class="brand" href="/auth/login">
    <img src="/static/img/logo.png" alt="ANS Logo" onerror="this.style.display='none'">
    <div class="brand-text">
      <strong>Akademia Nauk Stosowanych</strong>
      <span>w Elblągu – System Praktyk</span>
    </div>
  </a>
</nav>"""


# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    login_error = None

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not email or not password:
            login_error = "Podaj email i hasło."
        else:
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                login_error = "Nieprawidłowy email lub hasło."
            elif not user.is_active:
                login_error = "Konto jest nieaktywne. Skontaktuj się z administratorem."
            else:
                login_user(user)
                return redirect(url_for('auth.dashboard'))

    auth_url, flow = get_auth_url()
    flow_id = uuid.uuid4().hex
    FLOWS[flow_id] = flow
    session["flow_id"] = flow_id
    session.modified = True
    print("[auth.login] stored flow in session; keys=", getattr(flow, 'keys', lambda: 'n/a')())

    error_html = f'<div class="login-error">{login_error}</div>' if login_error else ''
    prefill_email = request.form.get('email', '') if login_error else ''

    content = f"""
<div class="login-wrap">
  <div class="login-card">
    <img src="/static/img/logo.png" alt="ANS Logo" class="login-logo"
         onerror="this.style.display='none'">
    <h1>System Obsługi Praktyk</h1>
    <p>Akademia Nauk Stosowanych w Elblągu</p>

    <!-- Microsoft -->
    <a href="{auth_url}" class="btn-microsoft">
      <svg viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="1"  y="1"  width="9" height="9" fill="#f25022"/>
        <rect x="11" y="1"  width="9" height="9" fill="#7fba00"/>
        <rect x="1"  y="11" width="9" height="9" fill="#00a4ef"/>
        <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
      </svg>
      Zaloguj przez Microsoft
    </a>

    <!-- Divider -->
    <div class="login-divider"><span>lub zaloguj się lokalnie</span></div>

    <!-- Local login form -->
    {error_html}
    <form method="POST" action="/auth/login" class="login-form">
      <div class="login-field">
        <label for="email">Email</label>
        <input type="email" id="email" name="email"
               value="{prefill_email}"
               placeholder="twoj@email.pl" required autocomplete="username">
      </div>
      <div class="login-field">
        <label for="password">Hasło</label>
        <input type="password" id="password" name="password"
               placeholder="••••••••" required autocomplete="current-password">
      </div>
      <button type="submit" class="btn-local-login">Zaloguj się</button>
    </form>

    <!-- Dev quick-login buttons -->
    <div class="login-divider"><span>szybki dostęp testowy</span></div>
    <div class="dev-roles">
      <a href="/auth/dev-login?role=student"    class="dev-role-btn role-student">Student</a>
      <a href="/auth/dev-login?role=opiekun"    class="dev-role-btn role-opiekun">Opiekun</a>
      <a href="/auth/dev-login?role=dziekanat"  class="dev-role-btn role-dziekanat">Dziekanat</a>
      <a href="/auth/dev-login?role=admin"      class="dev-role-btn role-admin">Admin</a>
    </div>
  </div>
</div>"""
    return _base("Logowanie", _navbar_guest(), content)


@auth_bp.route("/callback")
def callback():
    try:
        print("[auth.callback] session keys:", list(session.keys()))
        print("[auth.callback] session (raw):", {k: type(v).__name__ for k, v in session.items()})
        print("[auth.callback] request.method:", request.method)
        print("[auth.callback] request.values keys:", list(request.values.keys()))
        print("[auth.callback] request.cookies:", request.cookies)
        print("[auth.callback] request headers Cookie:", request.headers.get('Cookie'))
    except Exception as _e:
        print("[auth.callback] debug print failed:", _e)

    flow_id = session.pop("flow_id", None)
    print("[auth.callback] popped flow_id:", flow_id)
    flow = FLOWS.pop(flow_id, None) if flow_id else None
    print("[auth.callback] flow found:", bool(flow))

    if not flow:
        content = """
<div class="error-wrap">
  <div class="error-card">
    <div class="error-code">400</div>
    <h2>Brak sesji autoryzacyjnej</h2>
    <p>Wywołanie callbacku OAuth nie zawiera zapisanej sesji.</p>
    <div class="ans-alert">
      <strong>Co sprawdzić:</strong>
      <ul>
        <li>Nie restartujesz serwera między /auth/login i /auth/callback (dev reloader wyłączony).</li>
        <li>Przeglądarka akceptuje cookie sesji (Application → Cookies).</li>
        <li>Jeśli testujesz lokalnie, użyj <a href="/auth/dev-login">/auth/dev-login</a>.</li>
      </ul>
    </div>
    <a href="/auth/login" class="btn-adm btn-adm-primary">Wróć do logowania</a>
  </div>
</div>"""
        return _base("Brak sesji autoryzacyjnej", _navbar_guest(), content), 400

    result = get_token_from_code(request.values, flow)
    if "error" in result:
        return f"Błąd: {result.get('error_description')}", 400

    token = result["access_token"]
    info  = get_user_info(token)
    return _process_login(info["email"], info)


def _process_login(email: str, info: dict):
    user = User.query.filter_by(email=email).first()
    if not user:
        role = _assign_role(email)
        if role == "no_access":
            content = """
<div class="error-wrap">
  <div class="error-card">
    <div class="error-code">403</div>
    <h2>Brak dostępu</h2>
    <p>Twoja domena email nie jest uprawniona do korzystania z systemu.</p>
    <a href="/auth/login" class="btn-adm btn-adm-primary">Wróć do logowania</a>
  </div>
</div>"""
            return _base("Brak dostępu", _navbar_guest(), content), 403

        user = User(
            email         = info["email"],
            full_name     = info["full_name"],
            external_id   = info["external_id"],
            auth_provider = "microsoft",
            role          = role,
        )
        db.session.add(user)
        db.session.commit()

    if not user.is_active:
        content = """
<div class="error-wrap">
  <div class="error-card">
    <div class="error-code">403</div>
    <h2>Konto nieaktywne</h2>
    <p>Twoje konto zostało dezaktywowane. Skontaktuj się z administratorem.</p>
    <a href="/auth/login" class="btn-adm btn-adm-primary">Wróć do logowania</a>
  </div>
</div>"""
        return _base("Konto nieaktywne", _navbar_guest(), content), 403

    login_user(user)
    return redirect(url_for("auth.dashboard"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    avatar = _avatar_letters(current_user.full_name or current_user.email)
    badge  = _role_badge(current_user.role)
    role   = current_user.role

    # Stats
    stats = f"""
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-icon blue">👤</div>
    <div>
      <div class="stat-val" style="font-size:15px;font-family:'IBM Plex Mono',monospace;">{current_user.email.split('@')[0]}</div>
      <div class="stat-label">Login</div>
    </div>
  </div>
  <div class="stat-card">
    <div class="stat-icon green">🏛️</div>
    <div>
      <div class="stat-val" style="font-size:13px;">{current_user.email.split('@')[1] if '@' in (current_user.email or '') else '—'}</div>
      <div class="stat-label">Domena</div>
    </div>
  </div>
  <div class="stat-card">
    <div class="stat-icon amber">🔑</div>
    <div>
      <div class="stat-val">{badge}</div>
      <div class="stat-label">Rola</div>
    </div>
  </div>
  <div class="stat-card">
    <div class="stat-icon {'green' if current_user.is_active else 'red'}">{'✅' if current_user.is_active else '🚫'}</div>
    <div>
      <div class="stat-val" style="font-size:14px;">{'Aktywne' if current_user.is_active else 'Nieaktywne'}</div>
      <div class="stat-label">Status konta</div>
    </div>
  </div>
</div>"""

    # Info cards
    cards = f"""
<div class="cards-grid">
  <div class="info-card">
    <div class="card-label">Imię i nazwisko</div>
    <div class="card-value">{current_user.full_name or '—'}</div>
  </div>
  <div class="info-card">
    <div class="card-label">Email</div>
    <div class="card-value" style="font-size:13px;font-family:'IBM Plex Mono',monospace;">{current_user.email}</div>
  </div>
  <div class="info-card">
    <div class="card-label">Rola w systemie</div>
    <div class="card-value">{badge}</div>
  </div>
  <div class="info-card">
    <div class="card-label">Dostawca logowania</div>
    <div class="card-value">{current_user.auth_provider}</div>
  </div>
</div>"""

    # Action panel — role-based
    if role in ('administrator', 'admin'):
        action_links = """
    <a href="/admin/users" class="action-link primary">
      <span class="action-link-icon">👥</span>
      <div class="action-link-text">
        <strong>Zarządzaj użytkownikami</strong>
        <span>Lista, role, eksport plików</span>
      </div>
    </a>
    <a href="/student/export-files" class="action-link">
      <span class="action-link-icon">📦</span>
      <div class="action-link-text">
        <strong>Eksportuj moje pliki</strong>
        <span>Pobierz dokumenty jako ZIP</span>
      </div>
    </a>"""
        panel_title = "Akcje administracyjne"
    elif role == 'student':
        action_links = """
    <a href="/student/" class="action-link primary">
      <span class="action-link-icon">🎓</span>
      <div class="action-link-text">
        <strong>Moje praktyki</strong>
        <span>Dokumenty, dziennik, status</span>
      </div>
    </a>
    <a href="/student/export-files" class="action-link">
      <span class="action-link-icon">📦</span>
      <div class="action-link-text">
        <strong>Eksportuj pliki</strong>
        <span>Pobierz dokumenty jako ZIP</span>
      </div>
    </a>"""
        panel_title = "Panel studenta"
    elif role == 'opiekun':
        action_links = """
    <a href="/opiekun/dashboard" class="action-link primary">
      <span class="action-link-icon">👨‍🏫</span>
      <div class="action-link-text">
        <strong>Panel opiekuna</strong>
        <span>Dokumenty studentów, przegląd, zatwierdzanie</span>
      </div>
    </a>"""
        panel_title = "Panel opiekuna"
    elif role in ('dziekanat', 'sekretariat', 'dyrekcja'):
        role_panel_titles = {
            'dziekanat': 'Panel dziekanatu', 'sekretariat': 'Panel sekretariatu',
            'dyrekcja': 'Panel dyrekcji',
        }
        panel_title = role_panel_titles.get(role, 'Panel')
        action_links = f"""
    <a href="/dziekanat/" class="action-link primary">
      <span class="action-link-icon">🏛️</span>
      <div class="action-link-text">
        <strong>{panel_title}</strong>
        <span>Lista studentów, praktyki, protokoły egzaminów</span>
      </div>
    </a>
    <a href="/dziekanat/internships" class="action-link">
      <span class="action-link-icon">📋</span>
      <div class="action-link-text">
        <strong>Lista praktyk</strong>
        <span>Przeglądaj i zarządzaj praktykami zawodowymi</span>
      </div>
    </a>"""
    else:
        action_links = """
    <a href="/admin/" class="action-link primary">
      <span class="action-link-icon">🏛️</span>
      <div class="action-link-text">
        <strong>Panel administracyjny</strong>
        <span>Zarządzanie systemem</span>
      </div>
    </a>"""
        panel_title = "Panel pracownika"

    action_panel = f"""
<div class="action-panel">
  <h3>{panel_title}</h3>
  <p>Wybierz jedną z opcji poniżej:</p>
  <div class="action-links">
    {action_links}
    <a href="/auth/regulamin" class="action-link">
      <span class="action-link-icon">📜</span>
      <div class="action-link-text">
        <strong>Regulamin PZ</strong>
        <span>Zasady i dokumentacja praktyk zawodowych</span>
      </div>
    </a>
  </div>
</div>"""

    content = f"""
<div class="ans-container" style="padding-top:28px;">
  <div class="welcome-banner">
    <div class="welcome-avatar">{avatar}</div>
    <div class="welcome-text">
      <h2>Witaj, {current_user.full_name or current_user.email}!</h2>
      <p>Zalogowano pomyślnie &nbsp;·&nbsp; Konto Microsoft &nbsp;·&nbsp; {current_user.email}</p>
    </div>
  </div>
  {stats}
  {cards}
  {action_panel}
</div>"""

    return _base("Dashboard", _navbar_logged(current_user.role), content)


# ──────────────────────────────────────────────
# DEVELOPMENT HELPERS
# ──────────────────────────────────────────────

@auth_bp.route('/dev-login')
def dev_login():
    if not (current_app.debug or current_app.config.get('SECRET_KEY') == 'dev-secret'):
        abort(404)
    role  = request.args.get('role', 'student')
    email = f"dev+{role}@test.local"
    user  = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, first_name='Dev', last_name=role.capitalize(), role=role, is_active=True)
        try:
            user.set_password('password123')
        except Exception:
            pass
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for('auth.dashboard'))


# ── Regulamin Praktyki Zawodowej ───────────────────────────────────────────────

# Prawdziwa treść regulaminu – nie używaj REGULAMIN_SECTIONS, patrz funkcja regulamin()
_TOC_ITEMS = [
    ("sec1", "1. Postanowienia ogólne"),
    ("sec2", "2. Cele praktyki zawodowej"),
    ("sec3", "3. Organizacja praktyk zawodowych"),
    ("sec4", "4. Zasady dokumentowania i zaliczania"),
    ("sec5", "5. Obowiązki opiekunów i studentów"),
    ("sec6", "6. Postanowienia końcowe"),
    ("sec7", "Wykaz załączników"),
]

_REGULAMIN_BODY = """
<div id="sec1" style="margin-bottom:28px;">
  <h3 style="font-size:15px;font-weight:700;color:#1a2744;margin:0 0 14px;
             padding-bottom:8px;border-bottom:2px solid #3b5bdb;">
    1. Postanowienia ogólne
  </h3>

  <p style="font-weight:700;margin:0 0 6px;font-size:13.5px;color:#1a2744;">§ 1</p>
  <ol style="margin:0 0 16px 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">Regulamin praktyk zawodowych, zwany dalej „Regulaminem", określa zasady organizowania i zaliczenia praktyk zawodowych w Instytucie Informatyki Stosowanej im. Krzysztofa Brzeskiego, zwanym dalej „Instytutem".</li>
    <li>Praktyki zawodowe są organizowane zgodnie z Regulaminem Studiów Akademii Nauk Stosowanych w Elblągu.</li>
  </ol>

  <p style="font-weight:700;margin:0 0 6px;font-size:13.5px;color:#1a2744;">§ 2</p>
  <ol style="margin:0 0 16px 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">Praktyki zawodowe odbywają się w oparciu o Porozumienie w sprawie praktyk zawodowych pomiędzy ANS w Elblągu, zwaną dalej „Uczelnią" a wybranymi w kraju lub/i za granicą jednostkami organizacyjnymi, zwanymi dalej „Zakładami Pracy". Wzór Porozumienia określa załącznik nr 1 do Regulaminu. Dopuszcza się stosowanie druku Porozumienia przedkładanego przez Zakład Pracy.</li>
    <li style="margin-bottom:8px;">Wraz z porozumieniem uczelnia wysyła do zakładu pracy Regulamin praktyk zawodowych dla kierunku informatyka oraz Program praktyki (Zał. nr 2.).</li>
    <li style="margin-bottom:8px;">Praktyka zawodowa może być realizowana w oparciu o dokumentację zgodną z programem „Erasmus+".</li>
    <li>Praktyka zawodowa może być realizowana w jednostce organizacyjnej wskazanej i uzgodnionej przez Uczelnię lub w jednostce organizacyjnej zaproponowanej i uzgodnionej przez studenta – jeżeli spełnia ona warunki zawarte w § 3 ust. 2.</li>
  </ol>

  <p style="font-weight:700;margin:0 0 6px;font-size:13.5px;color:#1a2744;">§ 3</p>
  <ol style="margin:0 0 16px 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">Miejsce odbycia praktyki zawodowej musi być uzgodnione z Uczelnianym opiekunem praktyk zawodowych (UOPZ) przed rozpoczęciem praktyki.</li>
    <li style="margin-bottom:8px;">Wybór miejsca odbywania praktyki zawodowej i charakter wykonywanej przez studenta pracy musi być zgodny z kierunkiem studiów, aby umożliwić osiągnięcie zakładanych efektów uczenia się i zdobycie umiejętności zawodowych zgodnych z kierunkiem kształcenia.</li>
    <li>Opiekunem praktyk ze strony zakładu (ZOPZ) pracy powinien być doświadczony pracownik zatrudniony na stanowisku informatycznym (np. administrator sieci, administrator systemów, programista, referent ds. informatyki itp.) – wymagane wykształcenie wyższe na kierunkach informatycznych lub pokrewnych (automatyka, robotyka, elektronika, telekomunikacja, elektrotechnika, matematyka stosowana); preferowany inżynier informatyk.</li>
  </ol>

  <p style="font-weight:700;margin:0 0 6px;font-size:13.5px;color:#1a2744;">§ 4</p>
  <ol style="margin:0 0 16px 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">Student, który wykonuje bądź w okresie ostatnich 3 lat wykonywał pracę zawodową, prowadził własną działalność gospodarczą, odbywał staż, a jego zakres obowiązków zawodowych jest/był zgodny z programem praktyki zawodowej, może realizować praktykę zawodową w ramach wykonywanych obowiązków lub wystąpić z wnioskiem o zaliczenie na jej poczet wykonywanych czynności zawodowych.</li>
    <li style="margin-bottom:8px;">Student, który odbywać będzie praktykę zawodową w ramach wykonywanej pracy zawodowej bądź występujący z wnioskiem o jej zaliczenie zobligowany jest do przedłożenia odpowiednio: zaświadczenia o zatrudnieniu i zakresu obowiązków (opisu stanowiska pracy) wykonywanych w ramach zatrudnienia, prowadzonej działalności gospodarczej, stażu oraz zaświadczenia z CEIDG lub odpisu z KRS albo innych dokumentów, na podstawie których można ocenić nabycie efektów uczenia się przewidzianych dla praktyki zawodowej.</li>
    <li>Merytoryczną ocenę wniosku studenta złożonego na podstawie ustępu 2 dokonuje Komisja do zaliczania praktyk zawodowych. Wzór merytorycznej oceny wniosku studenta przez Komisję do spraw praktyk stanowi <strong>załącznik 4a</strong>. Ostateczną decyzję co do uznania efektów uczenia się podejmuje dyrektor instytutu. Wniosek studenta o uznanie efektów uczenia się zrealizowanych w ramach pracy zawodowej, stażu lub działalności gospodarczej stanowi <strong>Załącznik Nr 4b</strong>.</li>
  </ol>

  <p style="font-weight:700;margin:0 0 6px;font-size:13.5px;color:#1a2744;">§ 5</p>
  <ol style="margin:0 0 16px 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">Potwierdzenia realizacji zadań wykonywanych w ramach praktyki zawodowej:
      <ol type="a" style="margin:8px 0 0 20px;padding:0;line-height:1.75;">
        <li style="margin-bottom:6px;">realizowanej na podstawie porozumienia w sprawie praktyk zawodowych dokonuje Zakładowy opiekun praktyki zawodowej w Dzienniku Praktyk (<strong>Zał. Nr 6</strong>) i na Karcie praktyki zawodowej (<strong>Zał. Nr 3</strong>),</li>
        <li style="margin-bottom:6px;">w przypadku realizujących praktykę w ramach pracy zawodowej – bezpośredni przełożony w oparciu o dostarczone sprawozdanie (<strong>Zał. Nr 7a</strong>),</li>
        <li>w przypadku realizujących praktykę na podstawie własnej działalności gospodarczej – Uczelniany opiekun praktyk zawodowych w oparciu o dostarczone sprawozdanie (<strong>Zał. Nr 7a</strong>).</li>
      </ol>
    </li>
    <li>Do potwierdzenia efektów uczenia się przewidzianych dla praktyki zawodowej służy <strong>załącznik nr 4</strong>.</li>
  </ol>

  <p style="font-weight:700;margin:0 0 6px;font-size:13.5px;color:#1a2744;">§ 6</p>
  <ol style="margin:0 0 16px 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">Egzamin z praktyki zawodowej warunkuje zaliczenie semestru, w którym odbywają się praktyki zawodowe oraz uzyskanie rejestracji na ostatni semestr studiów i dopuszczenie studenta do egzaminu dyplomowego.</li>
    <li style="margin-bottom:8px;">W przypadku studenta, który nie realizuje praktyki zawodowej z powodu choroby w czasie łącznym dłuższym niż 40 godzin, ma on obowiązek zwrócić się z wnioskiem o przedłużenie czasu trwania praktyki zawodowej i zrealizować praktykę w wymiarze wynikającym z programu studiów.</li>
    <li>Przedłużenie czasu trwania praktyki zawodowej jest możliwe maksymalnie na okres miesiąca po zaplanowanym dniu zakończenia praktyki zawodowej.</li>
  </ol>

  <p style="font-weight:700;margin:0 0 6px;font-size:13.5px;color:#1a2744;">§ 7</p>
  <p style="margin:0 0 16px;font-size:13.5px;color:#374151;line-height:1.75;">Praktykom zawodowym przypisuje się punkty ECTS.</p>
</div>

<div id="sec2" style="margin-bottom:28px;">
  <h3 style="font-size:15px;font-weight:700;color:#1a2744;margin:0 0 14px;
             padding-bottom:8px;border-bottom:2px solid #3b5bdb;">
    2. Cele praktyki zawodowej
  </h3>
  <ol style="margin:0 0 0 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">Zapoznanie z działalnością przedsiębiorstw branży informatycznej lub działów informatycznych w przedsiębiorstwach, instytucjach, urzędach, itp.</li>
    <li style="margin-bottom:8px;">Zapoznanie z realizacją projektów informatycznych, procesami wdrażania systemów informatycznych lub procedurami związanymi z utrzymaniem urządzeń, obiektów i systemów teleinformatycznych.</li>
    <li style="margin-bottom:8px;">Wykonanie samodzielne lub poprzez współudział w zespole minimum jednej pozycji z zakresu:
      <ol type="a" style="margin:8px 0 0 20px;padding:0;line-height:1.75;">
        <li style="margin-bottom:6px;">oprogramowania (systemów, aplikacji lub komponentów programowych) lub projektów systemów oprogramowania,</li>
        <li style="margin-bottom:6px;">projektów graficznych lub multimedialnych, modelowania 3D, fotogrametrii,</li>
        <li>konfiguracji systemów lub projektów sieci zlecanych przez firmy.</li>
      </ol>
    </li>
    <li style="margin-bottom:8px;">Zdobycie doświadczenia w korzystaniu z norm i standardów stosowanych w informatyce.</li>
    <li style="margin-bottom:8px;">Zapoznanie się z zasadami bezpieczeństwa pracy i ergonomii w zawodzie informatyka.</li>
    <li>Zdobycie doświadczenia w pracy zespołowej.</li>
  </ol>
</div>

<div id="sec3" style="margin-bottom:28px;">
  <h3 style="font-size:15px;font-weight:700;color:#1a2744;margin:0 0 14px;
             padding-bottom:8px;border-bottom:2px solid #3b5bdb;">
    3. Organizacja praktyk zawodowych
  </h3>
  <ol style="margin:0 0 0 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">Praktyka zawodowa realizowana jest na 7. semestrze studiów w wymiarze <strong>6 miesięcy (120 dni roboczych) tzn. 960 godzin</strong>. Studentów obowiązuje dzienny wymiar czasu pracy stosowany w danym zakładzie pracy, jednak nie dłużej niż 8 godzin.</li>
    <li style="margin-bottom:8px;">Praktykę należy rozpocząć przed semestrem 7. tak, aby zakończyła się do połowy lutego.</li>
    <li style="margin-bottom:8px;">W szczególnie uzasadnionych przypadkach Dyrektor Instytutu Informatyki Stosowanej im. K. Brzeskiego, na pisemny wniosek studenta, może wyrazić zgodę na realizację praktyki zawodowej w innym terminie niż wskazany w programie studiów. Zmiana terminu odbywania praktyki zawodowej nie zwalnia studenta z uczestnictwa w zajęciach przewidzianych w programie studiów.</li>
    <li style="margin-bottom:8px;">W przypadku gdy osiągnięcie zakładanych efektów uczenia się nie jest możliwe na jednym stanowisku pracy, konieczne jest odbycie praktyki na kilku stanowiskach pracy bądź w różnych zakładach pracy.</li>
    <li style="margin-bottom:8px;">Przed przystąpieniem do praktyki, student wraz z Uczelnianym opiekunem praktyk zawodowych (UOPZ) i zakładowym opiekunem praktyk zawodowej (ZOPZ) uzgadniają program i harmonogram praktyki (<strong>Zał. 2a</strong>).</li>
    <li style="margin-bottom:8px;">W przypadku realizacji praktyki w kilku zakładach, konieczne jest prowadzenie odrębnej dokumentacji praktyki.</li>
    <li style="margin-bottom:8px;">W przypadku, kiedy student wyjeżdża na studia za granicę w ramach programów unijnych, praktykę zawodową zobowiązany jest zaliczyć we wcześniejszym lub późniejszym terminie. Zgoda na przesunięcie terminu praktyki jest udzielana przez Dyrektora Instytutu na pisemny wniosek studenta po zasięgnięciu opinii Opiekuna praktyk. Możliwe jest odbywanie praktyk za granicą kraju, pod warunkiem spełnienia wymagań niniejszego regulaminu.</li>
    <li style="margin-bottom:8px;">W trakcie trwania praktyki zawodowej przewiduje się minimum jedną hospitację dokonywaną przez Opiekuna praktyk zawodowych w wybranym zakładzie pracy lub przez inne osoby wskazane przez zastępcę dyrektora Instytutu ds. organizacyjnych i naukowych.</li>
    <li>Za organizację praktyk zawodowych odpowiada Opiekun praktyk zawodowych (UOPZ) wyznaczony przez Rektora Uczelni.</li>
  </ol>
</div>

<div id="sec4" style="margin-bottom:28px;">
  <h3 style="font-size:15px;font-weight:700;color:#1a2744;margin:0 0 14px;
             padding-bottom:8px;border-bottom:2px solid #3b5bdb;">
    4. Zasady dokumentowania przebiegu praktyki zawodowej oraz procedura jej zaliczania
  </h3>
  <ol style="margin:0 0 0 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">W trakcie praktyki student zobowiązany jest do prowadzenia dziennika praktyki, w którym będzie odnotowywał prace jakie wykonywał w poszczególnych dniach roboczych.</li>
    <li style="margin-bottom:8px;">W terminie do 7 dni po zakończeniu praktyki zawodowej, student składa do Opiekuna uczelnianego praktyk zawodowych sprawozdanie wraz z dokumentami określonymi w ust. 4.</li>
    <li style="margin-bottom:8px;">W wyjątkowych przypadkach, kiedy student nie ma możliwości realizacji praktyki zawodowej i jej zaliczenia z przyczyn niezależnych od studenta, decyzję o przedłużeniu terminu jej realizacji i zaliczenia podejmuje, na pisemny wniosek studenta i po zasięgnięciu opinii Opiekuna praktyk zawodowych, zastępca dyrektora Instytutu ds. organizacyjnych i naukowych.</li>
    <li style="margin-bottom:8px;">Po zakończeniu praktyki zawodowej Student zobowiązany jest do przedłożenia następujących dokumentów:
      <ol type="a" style="margin:8px 0 0 20px;padding:0;line-height:1.75;">
        <li style="margin-bottom:6px;"><strong>Dziennika praktyki zawodowej (Zał. Nr 6)</strong>, w którym będzie odnotowywał prace jakie wykonywał w poszczególnych dniach roboczych z uwzględnieniem zagadnień związanych z osiąganiem efektów uczenia się wymaganych w programie praktyki. Wykonanie poszczególnych zadań, opisanych w dzienniku praktyki, potwierdza zakładowy opiekun praktyki.</li>
        <li style="margin-bottom:6px;"><strong>Sprawozdania z przebiegu praktyki zawodowej (Zał. Nr 7)</strong>, zawierającego element samooceny w zakresie stopnia osiągnięcia założonych efektów uczenia się, podpisanego przez Zakładowego opiekuna praktyk.</li>
        <li style="margin-bottom:6px;"><strong>Zaświadczenia odbycia praktyki zawodowej i opinii z Zakładu Pracy (Zał. Nr 3)</strong>, w którym student odbywał praktykę.</li>
        <li style="margin-bottom:6px;"><strong>Potwierdzenia uzyskania efektów uczenia się (Zał. Nr 4)</strong> w ramach zatrudnienia/stażu/praktyki zawodowej.</li>
        <li><strong>Kwestionariusza ankiety (Zał. Nr 5)</strong> oceniającego przebieg praktyk zawodowych.</li>
      </ol>
    </li>
    <li style="margin-bottom:8px;">Praktyka zawodowa podlega zaliczeniu w formie egzaminu ustnego z oceną.</li>
    <li style="margin-bottom:8px;">Egzamin z praktyki zawodowej odbywa się przed Komisją egzaminacyjną powoływaną przez dyrektora Instytutu. W skład Komisji wchodzą: Przewodniczący, Opiekunowie praktyk. Przewodniczącego Komisji wyznacza dyrektor Instytutu.</li>
    <li style="margin-bottom:8px;">Termin egzaminu z praktyki zawodowej wyznacza przewodniczący Komisji egzaminacyjnych ds. praktyk zawodowych w porozumieniu z Opiekunami praktyk zawodowych.</li>
    <li style="margin-bottom:8px;">Podstawą zaliczenia praktyki zawodowej jest protokół sporządzony i podpisany przez Komisję egzaminacyjną ds. praktyk.</li>
    <li style="margin-bottom:8px;"><strong>Protokół sporządzany jest indywidualnie dla każdego studenta</strong> i dołączany do akt osobowych studenta (<strong>Zał. Nr 8</strong>).</li>
    <li>Opiekun praktyki zawodowej potwierdza zaliczenie praktyki zawodowej odpowiednim wpisem do systemu komputerowego USOS.</li>
  </ol>
</div>

<div id="sec5" style="margin-bottom:28px;">
  <h3 style="font-size:15px;font-weight:700;color:#1a2744;margin:0 0 14px;
             padding-bottom:8px;border-bottom:2px solid #3b5bdb;">
    5. Obowiązki opiekunów i studentów
  </h3>

  <p style="font-weight:700;margin:0 0 6px;font-size:13.5px;color:#1a2744;">§ 8</p>
  <ol style="margin:0 0 0 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;" type="1">
    <li style="margin-bottom:12px;">Do obowiązków Opiekuna praktyk zawodowych należy:
      <ol type="a" style="margin:8px 0 0 20px;padding:0;line-height:1.75;">
        <li style="margin-bottom:5px;">opracowanie Programu i harmonogramu praktyki zawodowej (<strong>Zał. Nr 2a</strong>),</li>
        <li style="margin-bottom:5px;">zapoznanie studenta z obowiązującym Programem praktyki zawodowej,</li>
        <li style="margin-bottom:5px;">wydawanie skierowań na praktykę zawodową – skierowanie jest częścią Karty praktyki zawodowej (<strong>Zał. Nr 3</strong>),</li>
        <li style="margin-bottom:5px;">nadzór nad przebiegiem praktyki zawodowej (hospitacje),</li>
        <li style="margin-bottom:5px;">prowadzenie dokumentacji praktyk zawodowych,</li>
        <li style="margin-bottom:5px;">ocena dokumentacji dostarczonej przez studentów z odbytych praktyk zawodowych,</li>
        <li>uznanie efektów uczenia się zakładanych dla praktyki zawodowej (<strong>Zał. Nr 4</strong>).</li>
      </ol>
    </li>
    <li style="margin-bottom:12px;">Na wniosek Zakładu Pracy student odbywający praktykę zawodową jest zobowiązany ubezpieczyć się indywidualnie od następstw nieszczęśliwych wypadków na czas jej trwania.</li>
    <li style="margin-bottom:12px;">Do obowiązków studenta odbywającego praktykę zawodową należy:
      <ol type="a" style="margin:8px 0 0 20px;padding:0;line-height:1.75;">
        <li style="margin-bottom:5px;">zapoznanie się z Regulaminem praktyk zawodowych oraz innymi dokumentami,</li>
        <li style="margin-bottom:5px;">w przypadku samodzielnego wyszukania miejsca praktyki – student jest zobowiązany dostarczyć do dziekanatu <strong>Oświadczenie instytucji (Zał. Nr 9)</strong>,</li>
        <li style="margin-bottom:5px;">aktywne uczestniczenie w praktyce zawodowej i realizacja zadań wyznaczonych przez Opiekuna praktyk,</li>
        <li style="margin-bottom:5px;">przestrzeganie dyscypliny pracy oraz obowiązujących w Zakładzie Pracy regulaminów, przepisów BHP i innych,</li>
        <li>prowadzenie określonej w Regulaminie dokumentacji praktyk.</li>
      </ol>
    </li>
    <li>Do obowiązków Komisji egzaminacyjnej ds. praktyk należy przeprowadzenie egzaminu z praktyki zawodowej.</li>
  </ol>
</div>

<div id="sec6" style="margin-bottom:28px;">
  <h3 style="font-size:15px;font-weight:700;color:#1a2744;margin:0 0 14px;
             padding-bottom:8px;border-bottom:2px solid #3b5bdb;">
    6. Postanowienia końcowe
  </h3>
  <ol style="margin:0 0 0 20px;padding:0;font-size:13.5px;color:#374151;line-height:1.75;">
    <li style="margin-bottom:8px;">W sprawach nieuregulowanych niniejszym Regulaminem decyzje podejmuje dyrektor Instytutu Informatyki Stosowanej im. K. Brzeskiego.</li>
    <li>Regulamin praktyk zawodowych obowiązuje studentów rozpoczynających praktykę zawodową od roku ak. <strong>2024/2025</strong>.</li>
  </ol>
</div>

<div id="sec7" style="margin-bottom:8px;">
  <h3 style="font-size:15px;font-weight:700;color:#1a2744;margin:0 0 14px;
             padding-bottom:8px;border-bottom:2px solid #3b5bdb;">
    Wykaz załączników
  </h3>
  <table style="width:100%;border-collapse:collapse;font-size:13.5px;color:#374151;">
    <tbody>
      <tr style="background:#f7fafc;"><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;width:120px;">Zał. nr 1</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Porozumienie – zakład pracy</td></tr>
      <tr><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 2</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Program praktyki zawodowej</td></tr>
      <tr style="background:#f7fafc;"><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 2a</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Program i harmonogram praktyki zawodowej</td></tr>
      <tr><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 3</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Karta praktyki zawodowej</td></tr>
      <tr style="background:#f7fafc;"><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 4</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Potwierdzenie efektów uczenia się</td></tr>
      <tr><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 4a</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Potwierdzenie uzyskania efektów uczenia się – merytoryczna ocena wniosku studenta</td></tr>
      <tr style="background:#f7fafc;"><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 4b</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Wniosek o zaliczenie efektów uczenia się dla praktyki zawodowej na podstawie pracy zawodowej, stażu lub prowadzenia działalności gospodarczej</td></tr>
      <tr><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 5</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Kwestionariusz ankiety</td></tr>
      <tr style="background:#f7fafc;"><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 6</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Dziennik praktyki zawodowej</td></tr>
      <tr><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 7</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Sprawozdanie z praktyki zawodowej – studia stacjonarne</td></tr>
      <tr style="background:#f7fafc;"><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 7a</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Sprawozdanie z praktyki zawodowej – studia niestacjonarne</td></tr>
      <tr><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 8</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Protokół egzaminu z praktyki zawodowej</td></tr>
      <tr style="background:#f7fafc;"><td style="padding:9px 14px;border:1px solid #e2e8f0;font-weight:700;">Zał. nr 9</td><td style="padding:9px 14px;border:1px solid #e2e8f0;">Oświadczenie instytucji w sprawie przyjęcia studenta na praktykę zawodową</td></tr>
    </tbody>
  </table>
</div>
"""

# Nowy REGULAMIN_SECTIONS = [] – zastąpiony przez _REGULAMIN_BODY powyżej
@auth_bp.route("/regulamin")
@login_required
def regulamin():
    """Regulamin Praktyki Zawodowej – widoczny dla wszystkich zalogowanych."""
    navbar = _navbar_logged(current_user.role)

    toc_html = "".join(
        f'<li style="border-bottom:1px solid #f0f0f5;">'
        f'<a href="#{anchor}" style="display:block;padding:8px 0;font-size:12.5px;'
        f'color:#3b5bdb;text-decoration:none;">{label}</a></li>'
        for anchor, label in _TOC_ITEMS
    )

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div class="page-title-group">
      <h1>Regulamin Praktyki Zawodowej</h1>
      <div class="breadcrumb">
        <a href="/auth/dashboard">Dashboard</a>
        <span>›</span>
        <span>Regulamin PZ</span>
      </div>
    </div>
    <a href="/auth/dashboard" class="btn-adm btn-adm-ghost" style="font-size:13px;">
      ← Powrót
    </a>
  </div>
</div>

<div class="ans-container">
  <div style="display:grid;grid-template-columns:1fr 280px;gap:28px;align-items:start;">

    <div style="background:#fff;border:1px solid #dde1ef;border-radius:10px;
                padding:36px 40px;box-shadow:0 1px 3px rgba(26,39,68,.08);">

      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;color:#9ca3af;margin-bottom:4px;letter-spacing:.5px;">
          AKADEMIA NAUK STOSOWANYCH W ELBLĄGU
        </div>
        <div style="font-size:11px;color:#9ca3af;margin-bottom:20px;font-style:italic;">
          Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego
        </div>
        <h2 style="font-size:17px;font-weight:700;color:#1a2744;
                   text-transform:uppercase;letter-spacing:.4px;line-height:1.45;">
          Regulamin praktyk zawodowych<br>
          <span style="font-size:14px;">dla studiów o profilu praktycznym</span><br>
          <span style="font-size:14px;">Kierunek Informatyka</span>
        </h2>
      </div>

      {_REGULAMIN_BODY}

      <div style="margin-top:32px;padding:16px 20px;background:#f7fafc;
                  border-radius:8px;border:1px solid #e2e8f0;font-size:12px;
                  color:#6b7280;text-align:center;">
        Akademia Nauk Stosowanych w Elblągu &nbsp;·&nbsp;
        Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego &nbsp;·&nbsp;
        Obowiązuje od roku ak. 2024/2025
      </div>
    </div>

    <div>
      <div style="background:#fff;border:1px solid #dde1ef;border-radius:10px;
                  padding:20px;box-shadow:0 1px 3px rgba(26,39,68,.08);
                  position:sticky;top:24px;">
        <h3 style="font-size:13px;font-weight:700;color:#1a2744;margin-bottom:14px;">
          📋 Spis treści
        </h3>
        <ul style="list-style:none;padding:0;margin:0;">
          {toc_html}
        </ul>
        <div style="margin-top:16px;padding-top:14px;border-top:1px solid #e2e8f0;">
          <a href="/auth/dashboard" class="btn-adm btn-adm-ghost"
             style="display:block;text-align:center;font-size:13px;padding:8px;">
            ← Powrót do panelu
          </a>
        </div>
      </div>
    </div>

  </div>
</div>"""

    return _base("Regulamin PZ", navbar, content)