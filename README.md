# Satellite L1B to L1C Ortho Processing with AGA Evaluation

Projekt umożliwia:
- Przetworzenie danych satelitarnych z poziomu L1B do L1C (ortorektyfikacja)
- Wykorzystanie modelu RPC (Rational Polynomial Coefficients)
- Użycie DTM (cyfrowego modelu terenu) do korekcji geometrycznej
- Ocenę dokładności geometrycznej AGA z wykorzystaniem metryki CE90

## 📦 Struktura

.
├── Dockerfile
├── README.md
├── data/
│ 
│──rpc_model.py
│── inverse_rpc.py
│── l1b_processor_rpc.py
│── trial.ipynb

## ⚙️ Opis komponentów

### `rpc_model.py`
Klasa `RPCModel` odpowiedzialna za:
- Parsowanie pliku `.rpb`
- Projekcję współrzędnych geograficznych na pikselowe (`project()`)

### `inverse_rpc.py`
Funkcja `rpc_inverse()` służy do odwrotnego przekształcenia współrzędnych obrazowych do geograficznych (z uwzględnieniem DEM).

### `l1b_processor_rpc.py`
Klasa `L1BProcessorRPC`:
- Przetwarza obraz L1B do L1C (ortorektyfikacja)
- Zapisuje wynikowy obraz w docelowym układzie odniesienia (np. UTM)

---

## 📊 AGA – Absolute Geometric Accuracy

Ocena dokładności geolokalizacji obrazu względem punktów odniesienia.

### 🔬 CE90
> CE90 to promień okręgu, który zawiera 90% błędów pozycyjnych (odległości euklidesowej XY).

