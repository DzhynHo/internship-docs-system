# Architektura aplikacji Praktyk Zawodowych

Poniżej jest prosty diagram architektury aplikacji oraz opis głównych komponentów.

```mermaid
flowchart LR
    User[Użytkownik]
    subgraph Web
      FLASK[Flask App]
      TEMPL[TEMPLATES]
      STATIC[static (docs, css, img)]
    end
    subgraph DB
      SQL[(SQL - SQLAlchemy)]
    end
    User -->|HTTP| FLASK
    FLASK --> SQL
    FLASK --> TEMPL
    FLASK --> STATIC

    %% Role mapping
    subgraph Roles
      Student((Student))
      Opiekun((Opiekun))
      Dziekanat((Dziekanat/Sekretariat/Dyrekcja))
    end
    User --> Roles
    FLASK -->|RBAC| Roles

    classDef infra fill:#f9f,stroke:#333,stroke-width:1px;
    class DB infra
```

Opis:
- Flask z blueprintami `auth`, `student`, `admin`
- SQLAlchemy jako ORM, modele w `app/models`
- `app/static/docs` przechowuje oryginalne formularze (docx/pdf) — w repo są placeholdery, podmień pliki oryginalne
- Role: `student` (może wypełniać formularze i składać dokumenty), `opiekun` (może przeglądać, komentować, zatwierdzać), `dziekanat/sekretariat/dyrekcja` (zarządzanie protokołami i finalne zatwierdzenia)

Diagramy sekwencji i przepływów można dodać w kolejnych commitach.
