# sign-gesture-lstm

Skrypty dla trenowania modelu do rozpoznawania gestów dłoni oraz ich wykrywanie w czasie rzeczywistym z użyciem kamery internetowej.
Model oparty jest na sieci neuronowej LSTM i wykorzystuje punkty kluczowe dłoni (hand landmarks).

---

## Wymagania

- Python **3.10.11**
- Kamera internetowa
- System Windows (instrukcje poniżej dla Windows)

---

## Instalacja i uruchomienie

### 1️⃣ Jeśli tworzysz środowisko od zera

Utwórz wirtualne środowisko:

```bash
python -m venv venv
```

Aktywuj środowisko:

```bash
venv\Scripts\activate
```

Zainstaluj wymagane biblioteki:

```bash
pip install -r requirements.txt
```

### 2️⃣ Jeśli środowisko już istnieje

Aktywuj je:

```bash
venv\Scripts\activate
```

---

## Proces trenowania modelu

### 🔹 1. Zbieranie danych

Uruchom:

```bash
python collect_data.py
```

Skrypt zapisuje sekwencje punktów dłoni do folderu `data/`.

![Interfejs okna przygotowania do nagrywania](photo_trening.png)

### 🔹 2. Trenowanie modelu

```bash
python train_model.py
```

Po zakończeniu treningu zostanie wygenerowany plik modelu (np. `model.h5`).

### 🔹 3. Rozpoznawanie gestów w czasie rzeczywistym

```bash
python detect_live.py
```

Program uruchamia kamerę i wyświetla przewidywaną literę alfabetu PJM.

### 🔹 4. Ewaluacja modelu (średnia skuteczność)

Aby sprawdzić dokładność modelu:

```bash
python evaluate_model.py
```

Skrypt wyświetli:

- dokładność (accuracy)
- macierz pomyłek (confusion matrix)
- inne metryki klasyfikacji

---

## Struktura

```
├── data/                # Zebrane dane (sekwencje punktów dłoni)
├── model.h5             # Wytrenowany model
├── collect_data.py      # Zbieranie danych
├── train_model.py       # Trenowanie modelu
├── detect_live.py       # Rozpoznawanie w czasie rzeczywistym
├── evaluate_model.py    # Ewaluacja modelu
├── requirements.txt     # Lista zależności
└── README.md
```

---

## Informacje dodatkowe

- Model wykorzystuje sekwencje punktów kluczowych dłoni (21 landmarków).
- Sieć LSTM analizuje zależności czasowe w ruchu dłoni.
- Skuteczność modelu zależy od jakości i liczby zebranych danych.
