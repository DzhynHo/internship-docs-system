Aplikacja Praktyk Zawodowych

Cel: Centralne miejsce do gromadzenia i wypełniania dokumentów praktyk.

Jak użyć:
- Utwórz i aktywuj wirtualne środowisko
- Zainstaluj zależności: `pip install -r requirements.txt`
- Uruchom: `python run.py`

Role: student, opiekun, dziekanat (sekretariat), dyrekcja

Co dodałem w repo:
- modele `Attachment` i `DocumentSubmission` w `app/models/__init__.py`
- katalog `app/static/docs` z placeholderami wszystkich załączników
- `docs/ARCHITECTURE.md` z diagramem mermaid i opisem architektury

Następne kroki (opcjonalne):
- Dodać widoki i formularze dla każdej roli
- Dodać migracje i seed danych (wypełnić REQUIRED_ATTACHMENTS)
- Dodać walidację w formularzu sprawozdania (one-sentence)
