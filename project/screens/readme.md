
# System Obsługi Praktyk – ANS Elbląg

Aplikacja webowa do zarządzania praktykami zawodowymi studentów Akademii Nauk Stosowanych w Elblągu.

---

## Screenshoty

### 1. Strona logowania

![Strona logowania](screens/login.png)

Ekran powitalny systemu. Logowanie odbywa się wyłącznie przez konto uczelniane Microsoft (`@student.ans-elblag.pl`). Brak tradycyjnego formularza login/hasło – uwierzytelnianie delegowane do Microsoft Entra ID (Azure AD).

---

### 2. Dashboard użytkownika

![Dashboard](screens/dashboard.png)

Po zalogowaniu użytkownik trafia na swój dashboard. Widoczne są:

- baner powitalny z imieniem, nazwiskiem i numerem albumu,
- karty informacyjne: login, domena, rola w systemie, status konta,
- sekcja **Akcje** dopasowana do roli – administrator widzi skróty do zarządzania użytkownikami i eksportu plików.

---

### 3. Panel admina – Zarządzanie użytkownikami

![Zarządzanie użytkownikami](screens/admin_users.png)

Tabela wszystkich kont w systemie z możliwością:

- filtrowania po roli i statusie,
- wyszukiwania po nazwie / e-mailu,
- zmiany roli użytkownika,
- eksportu plików konkretnego użytkownika,
- eksportu całej listy do CSV.

Statystyki na górze strony pokazują liczbę studentów, pracowników i administratorów w czasie rzeczywistym.


© 2026 Akademia Nauk Stosowanych w Elblągu
