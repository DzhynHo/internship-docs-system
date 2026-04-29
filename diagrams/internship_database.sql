
-- System ePraktyki ? schemat bazy danych

CREATE TABLE role (
    rola_id INT PRIMARY KEY,
    nazwa VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE uzytkownicy (
    uzytkownik_id INT PRIMARY KEY,
    imie VARCHAR(100) NOT NULL,
    nazwisko VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    haslo VARCHAR(255) NOT NULL,
    rola_id INT NOT NULL,

    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2,

    FOREIGN KEY (rola_id) REFERENCES role(rola_id)
);

CREATE TABLE praktyki (
    praktyka_id INT PRIMARY KEY,
    student_id INT NOT NULL,
    instytucja_id INT NOT NULL,
    opiekun_id INT NOT NULL,
    typ VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    data_rozpoczecia DATE NOT NULL,
    data_zakonczenia DATE,
    created_at DATETIME2 DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES uzytkownicy(uzytkownik_id),
    FOREIGN KEY (instytucja_id) REFERENCES uzytkownicy(uzytkownik_id),
    FOREIGN KEY (opiekun_id) REFERENCES uzytkownicy(uzytkownik_id)
);


CREATE TABLE dokumenty (
    dokument_id INT PRIMARY KEY,
    praktyka_id INT NOT NULL,
    typ VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL,
    data_utworzenia DATETIME2 DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (praktyka_id) REFERENCES praktyki(praktyka_id)
);

CREATE TABLE dziennik (
    wpis_id INT PRIMARY KEY,
    praktyka_id INT NOT NULL,
    data DATE NOT NULL,
    opis TEXT NOT NULL,
    liczba_godzin INT NOT NULL,
    created_at DATETIME2 DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (praktyka_id) REFERENCES praktyki(praktyka_id)
);


CREATE TABLE sprawozdania (
    sprawozdanie_id INT PRIMARY KEY,
    praktyka_id INT NOT NULL UNIQUE,
    tresc TEXT NOT NULL,
    created_at DATETIME2 DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (praktyka_id) REFERENCES praktyki(praktyka_id)
);


CREATE TABLE oceny (
    ocena_id INT PRIMARY KEY,
    praktyka_id INT NOT NULL UNIQUE,
    opiekun_id INT NOT NULL,
    ocena VARCHAR(10),
    komentarz TEXT,
    created_at DATETIME2 DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (praktyka_id) REFERENCES praktyki(praktyka_id),
    FOREIGN KEY (opiekun_id) REFERENCES uzytkownicy(uzytkownik_id)
);


CREATE TABLE uwagi (
    uwaga_id INT PRIMARY KEY,
    dokument_id INT NOT NULL,
    autor_id INT NOT NULL,
    tresc TEXT NOT NULL,
    data_utworzenia DATETIME2 DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (dokument_id) REFERENCES dokumenty(dokument_id),
    FOREIGN KEY (autor_id) REFERENCES uzytkownicy(uzytkownik_id)
);

CREATE TABLE nadzor (
    id INT PRIMARY KEY,
    student_id INT NOT NULL,
    opiekun_id INT NOT NULL,

    FOREIGN KEY (student_id) REFERENCES uzytkownicy(uzytkownik_id),
    FOREIGN KEY (opiekun_id) REFERENCES uzytkownicy(uzytkownik_id)
);

-- Słownik 13 efektów kształcenia
CREATE TABLE efekty_ksztalcenia (
    efekt_id INT PRIMARY KEY,
    kod VARCHAR(10) NOT NULL UNIQUE, -- np. EK_01, EK_02
    opis TEXT NOT NULL
);

-- Tabela łącząca efekty z konkretnym formularzem (Zadanie: formularz ma 13 efektów)
CREATE TABLE efekty_formularza (
    formularz_id INT NOT NULL,
    efekt_id INT NOT NULL,
    PRIMARY KEY (formularz_id, efekt_id),
    FOREIGN KEY (formularz_id) REFERENCES praktyki(praktyka_id),
    FOREIGN KEY (efekt_id) REFERENCES efekty_ksztalcenia(efekt_id)
);

-- Szczegółowy harmonogram (Zadanie: suma dni = 120)
CREATE TABLE harmonogram_praktyki (
    harmonogram_id INT PRIMARY KEY,
    praktyka_id INT NOT NULL,
    data_rozpoczecia DATE NOT NULL,
    data_zakonczenia DATE NOT NULL,
    liczba_dni_roboczych INT NOT NULL, -- Tu suma musi wynieść 120
    zadania TEXT NOT NULL,
    FOREIGN KEY (praktyka_id) REFERENCES praktyki(praktyka_id)
);
