# Real-time Crypto Monitoring with Lambda Architecture

![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)
![Python](https://img.shields.io/badge/Python-3.9-yellow?logo=python)
![Architecture](https://img.shields.io/badge/Architecture-Lambda-orange)

Ένα ολοκληρωμένο σύστημα παρακολούθησης κρυπτονομισμάτων (BTC, ETH) σε πραγματικό χρόνο, βασισμένο στη **Λάμδα Αρχιτεκτονική (Lambda Architecture)**. Το σύστημα χρησιμοποιεί Docker containers για την κατάποση δεδομένων (ingestion), την αποθήκευση, την επεξεργασία ροών και την οπτικοποίηση ειδοποιήσεων.

---

## Πίνακας Περιεχομένων
- [Εισαγωγή](#εισαγωγή)
- [Αρχιτεκτονική](#αρχιτεκτονική)
- [Τεχνολογίες](#τεχνολογίες)
- [Δομή Φακέλων](#δομή-φακέλων)
- [Εγκατάσταση & Εκτέλεση](#εγκατάσταση--εκτέλεση)
- [API Documentation](#api-documentation)
- [Συντελεστές](#συντελεστές)

---

## Εισαγωγή
Το έργο αναπτύχθηκε στο πλαίσιο του ΠΜΣ "Πληροφοριακά Συστήματα & Υπηρεσίες" του Πανεπιστημίου Πειραιώς. Σκοπός είναι η συλλογή δεδομένων από το Binance μέσω WebSockets, η αποθήκευσή τους για ιστορική ανάλυση και η ταυτόχρονη ανίχνευση ανωμαλιών (Anomaly Detection) σε πραγματικό χρόνο.

**Βασικές Λειτουργίες:**
* **Ingestion:** Real-time λήψη δεδομένων (kline 1m) για BTC/USDT & ETH/USDT.
* **Batch Layer:** Αποθήκευση πρωτογενών δεδομένων (Raw Data) στο MinIO.
* **Speed Layer:** In-memory Rule Engine για ανίχνευση Volume Spikes (>3x avg) και παραβίαση ορίων τιμής.
* **Alerting:** Άμεση αποστολή ειδοποιήσεων μέσω RabbitMQ & Node-RED.
* **Visualization:** Ζωντανή απεικόνιση στο Thingsboard.

---

## ⚙️ Οδηγίες Εγκατάστασης & Εκτέλεσης

Ακολουθήστε τα παρακάτω βήματα για να εγκαταστήσετε και να εκτελέσετε την εφαρμογή τοπικά στον υπολογιστή σας. Ο οδηγός αυτός είναι σχεδιασμένος ώστε να είναι κατανοητός από οποιονδήποτε χρήστη, ανεξαρτήτως εμπειρίας.

### 1. Προαπαιτούμενα (Prerequisites)

Πριν ξεκινήσετε, βεβαιωθείτε ότι έχετε εγκατεστημένα τα εξής εργαλεία:

* **Docker Desktop** (για Windows/Mac) ή **Docker Engine** (για Linux).
    * [Λήψη Docker](https://www.docker.com/products/docker-desktop/)
* **Git** (για την κλωνοποίηση του κώδικα).
    * [Λήψη Git](https://git-scm.com/downloads)

> **Σημείωση:** Δεν χρειάζεται να έχετε εγκαταστήσει Python, Node.js ή βάσεις δεδομένων στον υπολογιστή σας. Όλα τα απαραίτητα εργαλεία θα εγκατασταθούν αυτόματα μέσα σε απομονωμένα περιβάλλοντα (containers).

---

### 2. Λήψη Κώδικα (Cloning)

Ανοίξτε ένα τερματικό (Terminal ή Command Prompt) και εκτελέστε τις παρακάτω εντολές:

```bash
# 1. Κλωνοποίηση του αποθετηρίου
git clone [https://github.com/Tasos91/crypto-ingestion-pipeline.git](https://github.com/Tasos91/crypto-ingestion-pipeline.git)

# 2. Μετάβαση στον φάκελο του project
cd crypto-ingestion-pipeline

Ορίστε το κείμενο που ζήτησες (από το βήμα 3 έως το 7), ενωμένο σε ένα ενιαίο Markdown block, έτοιμο για Copy-Paste.


### 3. Εκκίνηση της Εφαρμογής (Build & Run)

Αφού βρίσκεστε στον φάκελο του project, θα χρησιμοποιήσουμε το `docker-compose` για να δημιουργήσουμε τις εικόνες (images) και να ξεκινήσουμε τα containers.

Εκτελέστε την παρακάτω εντολή στο τερματικό:

```bash
docker-compose up -d --build

```

**Τι κάνει αυτή η εντολή:**

* `up`: Ξεκινάει τη διαδικασία δημιουργίας και εκκίνησης των containers.
* `-d` (detached): Τρέχει τα containers στο παρασκήνιο, ελευθερώνοντας το τερματικό σας ώστε να μπορείτε να συνεχίσετε να το χρησιμοποιείτε.
* `--build`: Αναγκάζει το Docker να "χτίσει" ξανά τις εικόνες (images) για τα custom services μας (Python scripts & Node-RED), διασφαλίζοντας ότι τρέχετε την τελευταία έκδοση του κώδικα.

>  **Υπομονή:** Η πρώτη εκτέλεση ενδέχεται να διαρκέσει μερικά λεπτά, καθώς το Docker πρέπει να κατεβάσει τις απαραίτητες εικόνες (MinIO, RabbitMQ, Thingsboard κ.λπ.) και να εγκαταστήσει τις βιβλιοθήκες Python.

---

### 4. Έλεγχος Λειτουργίας (Verification)

Για να βεβαιωθείτε ότι όλα τα συστήματα ξεκίνησαν σωστά και δεν υπάρχουν σφάλματα, εκτελέστε:

```bash
docker-compose ps

```

Θα πρέπει να δείτε μια λίστα με **6 containers**. Η στήλη `State` (ή `Status`) πρέπει να είναι `Up` και (όπου εφαρμόζεται) η κατάσταση υγείας (`Health`) να είναι `healthy`.

Αν θέλετε να δείτε τα logs (καταγραφές) κάποιου συγκεκριμένου container (π.χ. του connector) για να βεβαιωθείτε ότι κατεβάζει δεδομένα:

```bash
docker logs -f binance_connector

```

*(Πατήστε `Ctrl + C` για να βγείτε από τα logs)*

---

### 5. Πρόσβαση στις Υπηρεσίες (Access)

Μόλις το σύστημα ξεκινήσει πλήρως, οι υπηρεσίες είναι διαθέσιμες μέσω Browser στις παρακάτω διευθύνσεις:

| Υπηρεσία | URL | Credentials (User / Pass) |
| --- | --- | --- |
| **Thingsboard Dashboard** | `http://localhost:8080` | `tenant@thingsboard.org` / `tenant` |
| **Node-RED Editor** | `http://localhost:1880` | *(Δεν απαιτείται login)* |
| **MinIO Console** | `http://localhost:9001` | `minio` / `minio123` |
| **RabbitMQ Management** | `http://localhost:15672` | `user` / `password` |
| **Analytics API** | `http://localhost:5001` | `tasos` / `charis` |

---

### 6. Παράδειγμα Χρήσης API

Για να δοκιμάσετε το Analytics API, μπορείτε να ανοίξετε τον browser ή να χρησιμοποιήσετε το `curl` στο τερματικό:

**Λήψη Πρόβλεψης & Στατιστικών (BTC):**

```bash
curl -u tasos:charis "http://localhost:5001/get-prediction/btcusdt?limit=20"

```

**Ενημέρωση Ορίων (Thresholds):**

```bash
curl -u tasos:charis -X POST "http://localhost:5001/set-thresholds" \
     -H "Content-Type: application/json" \
     -d '{"btcusdt": {"min": 92000, "max": 96000}}'

```

---

### 7. Τερματισμός Εφαρμογής (Stop)

Όταν ολοκληρώσετε την εργασία σας, μπορείτε να σταματήσετε το σύστημα με τις εξής επιλογές:

**Επιλογή Α: Απλός Τερματισμός (Διατήρηση Δεδομένων)**
Σταματάει τα containers αλλά κρατάει τα δεδομένα στις βάσεις (MinIO, Thingsboard).

```bash
docker-compose down

```

**Επιλογή Β: Πλήρης Καθαρισμός (Διαγραφή Δεδομένων)**
Σταματάει τα containers και διαγράφει τα volumes (τα αποθηκευμένα δεδομένα). Χρήσιμο αν θέλετε να ξεκινήσετε από το μηδέν.

```bash
docker-compose down -v

```

```

```