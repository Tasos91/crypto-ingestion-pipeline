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

## Αρχιτεκτονική

Η ροή των δεδομένων ακολουθεί αυστηρά τη Λάμδα Αρχιτεκτονική:

```mermaid
flowchart TD
    %% Ορισμός Στυλ
    classDef container fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef storage fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;

    %% Services
    Binance((Binance API)) 
    Connector[Python Ingestion Script]:::container
    NodeRED[Node-RED Service]:::container
    API[Analytics API]:::container
    TB[Thingsboard]:::container

    %% Storage
    MinIO_Raw[(MinIO: Raw Data)]:::storage
    RabbitMQ(RabbitMQ):::storage
    MinIO_Alerts[(MinIO: Alerts)]:::storage

    %% Flow
    Binance ==> Connector
    Connector -- "1. Batch Save" --> MinIO_Raw
    Connector -- "2. Alerts" --> RabbitMQ
    RabbitMQ --> NodeRED
    NodeRED -- "Archive" --> MinIO_Alerts
    NodeRED -- "Visualize" --> TB
    MinIO_Raw -.-> API
