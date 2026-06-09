"""
Blueprint studenta – ANS System Praktyk.
"""
from flask import Blueprint

# 1. Najpierw tworzymy Blueprint
student_bp = Blueprint("student", __name__, template_folder='templates')

# 2. Potem definiujemy STUDENT_PAGE
STUDENT_PAGE = '''<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Panel studenta – System Praktyk ANS</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --navy:        #1a2744;
      --accent:      #3b5bdb;
      --accent-hover:#2f4ac0;
      --teal:        #0d9488;
      --red:         #dc2626;
      --red-light:   #fef2f2;
      --amber:       #d97706;
      --amber-light: #fffbeb;
      --green:       #16a34a;
      --green-light: #f0fdf4;
      --bg:          #f0f2f7;
      --surface:     #ffffff;
      --surface-2:   #f8f9fc;
      --border:      #dde1ef;
      --border-light:#eaecf5;
      --text:        #111827;
      --text-mid:    #374151;
      --text-muted:  #6b7280;
      --text-light:  #9ca3af;
      --shadow-sm:   0 1px 3px rgba(26,39,68,.08);
      --shadow-lg:   0 8px 32px rgba(26,39,68,.13);
      --radius:      10px;
      --radius-sm:   6px;
    }

    body {
      font-family: 'IBM Plex Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* ── NAVBAR ── */
    nav.ans-navbar {
      background: var(--navy);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      height: 68px;
      box-shadow: 0 2px 12px rgba(0,0,0,.18);
      flex-shrink: 0;
    }
    nav.ans-navbar a.brand {
      display: flex; align-items: center; gap: 14px; text-decoration: none;
    }
    nav.ans-navbar a.brand img {
      height: 44px; background: #fff; padding: 4px; border-radius: 4px;
    }
    nav.ans-navbar .brand-text { color: #fff; line-height: 1.2; }
    nav.ans-navbar .brand-text > *:first-child {
      font-size: 15px; font-weight: 700; display: block; color: #fff;
    }
    nav.ans-navbar .brand-text span {
      font-size: 12px; font-weight: 300; color: rgba(255,255,255,.65);
    }
    nav.ans-navbar > nav { display: flex; align-items: center; gap: 4px; }
    nav.ans-navbar > nav a {
      color: rgba(255,255,255,.75); text-decoration: none;
      padding: 7px 14px; border-radius: 6px;
      font-size: 13.5px; font-weight: 500;
      transition: all .15s; background: transparent;
    }
    nav.ans-navbar > nav a:hover { color: #fff; background: rgba(255,255,255,.1); }
    nav.ans-navbar > nav a.btn-logout {
      background: rgba(255,255,255,.1);
      border: 1px solid rgba(255,255,255,.2);
      color: #fff;
    }
    .ans-header-strip {
      height: 4px;
      background: linear-gradient(90deg, #3b5bdb 0%, #0d9488 100%);
      flex-shrink: 0;
    }

    /* ── FOOTER ── */
    .ans-footer {
      background: var(--navy);
      color: rgba(255,255,255,.45);
      text-align: center;
      padding: 14px 24px;
      font-size: 12px;
      margin-top: auto;
    }

    /* ── PAGE HEADER ── */
    .page-header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 22px 0;
    }
    .page-header-inner {
      max-width: 1180px; margin: 0 auto; padding: 0 24px;
      display: flex; align-items: center;
      justify-content: space-between; gap: 16px; flex-wrap: wrap;
    }
    .page-title-group h1 {
      font-size: 22px; font-weight: 700;
      color: var(--navy); letter-spacing: -.3px;
    }
    .breadcrumb {
      display: flex; align-items: center; gap: 6px;
      font-size: 12.5px; color: var(--text-muted); margin-top: 4px;
    }
    .breadcrumb a { color: var(--accent); text-decoration: none; }
    .breadcrumb a:hover { text-decoration: underline; }

    /* ── CONTAINER ── */
    .student-container {
      max-width: 1180px; margin: 0 auto; padding: 0 24px 40px; flex: 1;
    }

    /* ── CARDS ── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      overflow: hidden;
      margin-bottom: 24px;
    }
    .card-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border-light);
      display: flex; align-items: center;
      justify-content: space-between; gap: 12px;
    }
    .card-header h2 {
      font-size: 15px; font-weight: 700;
      color: var(--navy); letter-spacing: -.2px;
    }
    .card-body { padding: 24px; }

    /* ── STATS ── */
    .stats-row {
      display: grid;
      grid-template-columns: repeat(4,1fr);
      gap: 16px; padding: 24px 0 0;
    }
    .stat-card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 18px 20px;
      box-shadow: var(--shadow-sm); display: flex; align-items: center; gap: 14px;
    }
    .stat-icon {
      width: 44px; height: 44px; border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; font-size: 20px;
    }
    .stat-icon.blue  { background: #eff3ff; }
    .stat-icon.green { background: var(--green-light); }
    .stat-icon.amber { background: var(--amber-light); }
    .stat-icon.teal  { background: #f0fdfa; }
    .stat-val  { font-size: 26px; font-weight: 700; color: var(--navy); letter-spacing: -.5px; line-height: 1; }
    .stat-label{ font-size: 12px; color: var(--text-muted); margin-top: 2px; font-weight: 500; }

    /* ── ATTACHMENTS GRID ── */
    .attachments-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 16px;
      padding-top: 20px;
    }
    .attachment-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      padding: 20px;
      display: flex; flex-direction: column; gap: 12px;
      transition: box-shadow .15s, border-color .15s;
    }
    .attachment-card:hover {
      box-shadow: var(--shadow-lg);
      border-color: var(--accent);
    }
    .attachment-num {
      display: inline-flex; align-items: center; justify-content: center;
      width: 36px; height: 36px; border-radius: 8px;
      background: #eff3ff; color: var(--accent);
      font-size: 13px; font-weight: 700; flex-shrink: 0;
    }
    .attachment-title {
      font-size: 14px; font-weight: 600; color: var(--navy);
    }
    .attachment-desc {
      font-size: 12.5px; color: var(--text-muted); line-height: 1.5;
    }
    .attachment-footer {
      display: flex; align-items: center;
      justify-content: space-between; gap: 8px;
      margin-top: auto; padding-top: 4px;
    }

    /* ── BADGES ── */
    .adm-badge {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 3px 9px; border-radius: 20px;
      font-size: 11.5px; font-weight: 600; white-space: nowrap;
    }
    .adm-badge-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
    .badge-draft    { background: #f1f5f9; color: #64748b; }
    .badge-draft .adm-badge-dot    { background: #64748b; }
    .badge-submitted { background: var(--amber-light); color: var(--amber); }
    .badge-submitted .adm-badge-dot{ background: var(--amber); }
    .badge-approved  { background: var(--green-light); color: var(--green); }
    .badge-approved .adm-badge-dot { background: var(--green); }
    .badge-rejected  { background: var(--red-light); color: var(--red); }
    .badge-rejected .adm-badge-dot { background: var(--red); }
    .badge-pending   { background: #eff3ff; color: var(--accent); }
    .badge-pending .adm-badge-dot  { background: var(--accent); }

    /* ── BUTTONS ── */
    .btn {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 8px 16px; border-radius: var(--radius-sm);
      font-size: 13.5px; font-weight: 600; font-family: inherit;
      cursor: pointer; border: none; text-decoration: none;
      transition: all .15s; white-space: nowrap;
    }
    .btn-primary { background: var(--accent); color: #fff !important; }
    .btn-primary:hover { background: var(--accent-hover); }
    .btn-ghost { background: transparent; color: var(--text-mid) !important; border: 1px solid var(--border); }
    .btn-ghost:hover { background: var(--surface-2); }
    .btn-teal   { background: var(--teal); color: #fff !important; }
    .btn-teal:hover { background: #0b7a70; }
    .btn-sm { padding: 5px 11px !important; font-size: 12.5px !important; }
    .btn-danger { background: var(--red); color: #fff !important; }
    .btn-danger:hover { background: #b91c1c; }

    /* ── FORM ── */
    .form-section { margin-bottom: 28px; }
    .form-section-title {
      font-size: 13px; font-weight: 700; text-transform: uppercase;
      letter-spacing: .6px; color: var(--text-muted);
      margin-bottom: 14px; padding-bottom: 8px;
      border-bottom: 1px solid var(--border-light);
    }
    .form-grid   { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .form-grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
    .form-group  { display: flex; flex-direction: column; gap: 5px; }
    .form-group.span-2 { grid-column: span 2; }
    .form-group.span-3 { grid-column: span 3; }
    label {
      font-size: 12.5px; font-weight: 600; color: var(--text-mid);
    }
    label .required { color: var(--red); margin-left: 2px; }
    input[type=text], input[type=date], input[type=email],
    input[type=number], select, textarea {
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 9px 12px;
      font-size: 13.5px; font-family: inherit; color: var(--text);
      background: var(--surface);
      transition: border .15s, box-shadow .15s;
      outline: none; width: 100%;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(59,91,219,.12);
    }
    input[readonly], input[disabled] {
      background: var(--surface-2); color: var(--text-muted); cursor: default;
    }
    textarea { resize: vertical; min-height: 80px; }
    .form-hint { font-size: 11.5px; color: var(--text-muted); margin-top: 2px; }
    .form-error { font-size: 11.5px; color: var(--red); margin-top: 2px; }

    /* ── ALERTS ── */
    .alert {
      padding: 12px 16px; border-radius: var(--radius-sm);
      font-size: 13px; margin-bottom: 16px;
      border-left: 4px solid transparent;
      display: flex; align-items: flex-start; gap: 8px;
    }
    .alert-success { background: var(--green-light); border-color: var(--green); color: #14532d; }
    .alert-error   { background: var(--red-light);   border-color: var(--red);   color: #7f1d1d; }
    .alert-info    { background: #eff3ff; border-color: var(--accent); color: #1e3a8a; }
    .alert-warning { background: var(--amber-light); border-color: var(--amber); color: #78350f; }

    /* ── TABLE ── */
    .table-card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); box-shadow: var(--shadow-sm);
      overflow: hidden; margin-bottom: 24px;
    }
    .adm-table { width: 100%; border-collapse: collapse; }
    .adm-table thead th {
      background: var(--surface-2); padding: 11px 16px; text-align: left;
      font-size: 11.5px; font-weight: 600; text-transform: uppercase;
      letter-spacing: .6px; color: var(--text-muted);
      border-bottom: 1px solid var(--border); white-space: nowrap;
    }
    .adm-table tbody tr { border-bottom: 1px solid var(--border-light); transition: background .1s; }
    .adm-table tbody tr:last-child { border-bottom: none; }
    .adm-table tbody tr:hover { background: var(--surface-2); }
    .adm-table tbody td { padding: 13px 16px; font-size: 13.5px; vertical-align: middle; }

    /* ── DIVIDER ── */
    .divider { border: none; border-top: 1px solid var(--border-light); margin: 20px 0; }

    /* ── RESPONSIVE ── */
    @media (max-width: 900px) {
      .stats-row { grid-template-columns: 1fr 1fr; }
      .form-grid, .form-grid-3 { grid-template-columns: 1fr; }
      .form-group.span-2, .form-group.span-3 { grid-column: span 1; }
    }
    @media (max-width: 600px) {
      .stats-row { grid-template-columns: 1fr; }
      nav.ans-navbar { padding: 0 14px; }
      .student-container { padding: 0 12px 32px; }
    }
  </style>
</head>
<body>

<nav class="ans-navbar">
  <a class="brand" href="/auth/dashboard">
    <img src="/static/img/logo.png" alt="ANS Logo" onerror="this.style.display=\'none\'">
    <div class="brand-text">
      <b>Akademia Nauk Stosowanych</b>
      <span>w Elblagu – System Praktyk</span>
    </div>
  </a>
  <nav>
    <a href="/auth/dashboard">Dashboard</a>
    <a href="/student/">Panel studenta</a>
    <a href="/auth/regulamin">Regulamin PZ</a>
    <a href="/auth/logout" class="btn-logout">Wyloguj</a>
  </nav>
</nav>
<div class="ans-header-strip"></div>

{{ content|safe }}

<footer class="ans-footer">&copy; 2026 Akademia Nauk Stosowanych w Elblagu</footer>
</body>
</html>'''

# 3. Importy routes NA SAMYM DOLE – po zdefiniowaniu student_bp i STUDENT_PAGE
from app.student import routes        # noqa: E402, F401
from app.student import diary_routes  # noqa: E402, F401