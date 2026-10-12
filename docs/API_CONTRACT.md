# API CONTRACT

## Kontrak aktif — API v1 (2026-10-10)

Status implementasi: **LOCAL MOCK VERIFIED**. Kontrak ini adalah sumber kebenaran
untuk dashboard, test, dan adapter. Bagian Legacy Phase 1 di bawah dipertahankan
sebagai catatan kompatibilitas dan bukan kontrak utama.

Base path: **/api/v1**. OpenAPI interaktif: **GET /docs**.

### Aturan lintas endpoint

- Waktu memakai ISO 8601 dan wajib memiliki offset zona waktu; fixture demo
  memakai Asia/Makassar (+08:00).
- Kuantitas selalu membawa unit; fixture saat ini menggunakan kg.
- Semua uang memakai IDR tanpa konversi tersembunyi.
- Mode analisis adalah mock, live_ai, atau fallback.
- Semua transaksi adalah draft lokal dengan simulated_only bernilai true.
- Tidak ada endpoint yang mengembalikan credential, token, atau isi .env.
- Header x-trace-id disertakan pada setiap respons HTTP.

Error konsisten:

~~~json
{
  "error_code": "NOT_FOUND",
  "message": "Incident not found: INC-MISSING",
  "details": null,
  "trace_id": "d2f9..."
}
~~~

Status utama: 404 ID tidak ditemukan, 409 draft/state tidak valid, 422 request
tidak valid, dan 502 layanan AI opsional tidak tersedia. Kegagalan AI pada alur
analysis normal ditangani sebagai fallback, bukan menggagalkan kalkulasi.

### GET /health

~~~json
{"status": "ok", "service": "nsra-api"}
~~~

### GET /api/v1/status

Readiness aman: versi, mode, klasifikasi data, flag konfigurasi SAP (boolean
tanpa nilai), status emulasi AWS, state_store SQLite/persistent, dan
real_transactions_enabled: false.

### GET /api/v1/overview

Read model untuk executive overview: KPI portfolio, severity distribution,
approval summary, tujuh titik exposure/approval trend, priority incidents, dan
facility-material risk matrix. Titik trend terakhir selalu direkonsiliasi dengan
mutable state saat ini.

### GET /api/v1/network

Mengembalikan location nodes (port, factory, warehouse, supplier), WGS84
reference coordinates, status node, inbound shipment routes, mitigation routes,
delay/lead time, dan modeled exposure/cost. Peta frontend bersifat schematic;
route table adalah accessible source of truth.

### GET /api/v1/portfolio

Joined read model incident + shipment + inventory + deterministic exposure +
latest analysis/draft state. Endpoint ini tidak membuat audit event atau
memutasi inventory.

### GET /api/v1/integrations/health

Status komponen yang eksplisit: OPERATIONAL, READY, NOT_CONFIGURED, EMULATED,
atau DISABLED. Credential value tidak pernah dikembalikan dan status READY tidak
berarti live call sudah dilakukan.

### GET /api/v1/inventory

Setiap item memuat material/facility ID dan nama, on_hand, reserved,
unavailable, usable_quantity, hourly_demand, hours_of_cover, safety_stock, unit,
dan risk_level.

### GET /api/v1/shipments

Setiap shipment memuat ID shipment/PO, material, origin, destination, quantity
dan unit, baseline_eta, current_eta, serta status.

### GET dan POST /api/v1/incidents

GET mengembalikan insiden ternormalisasi. GET dengan path incident ID mengambil
satu insiden. POST memakai incident_id sebagai idempotency key: create pertama
menghasilkan 201 dan created: true; event duplikat menghasilkan 200 dan
created: false.

~~~json
{
  "incident_id": "INC-LOCAL-EVENT-001",
  "source": "local.nsra.event-simulator",
  "event_type": "VESSEL_DELAY",
  "severity": "HIGH",
  "title": "Synthetic vessel delay",
  "description": "Local emulation only.",
  "shipment_id": "SHP-MKS-001",
  "detected_at": "2026-10-10T09:00:00+08:00",
  "delay_hours": 12
}
~~~

Teks instruction-like yang berpotensi prompt injection dikarantina dan ditandai
dengan injection_warning.

### POST /api/v1/analysis/disruption

Request utama:

~~~json
{
  "incident_id": "INC-MKS-FOUR-DAY",
  "use_live_ai": false,
  "target_downtime_hours": 0
}
~~~

Response analysis memuat identitas dan mode, asumsi input, material/fasilitas,
stockout dan shortage timeline, baseline dan skenario terurut, allocations,
downtime/unmet demand, cost breakdown, constraints, rejection reasons, risks,
recommendation, evidence, draft action, approval flag, warnings, dan bounded
agent tool trace. Setiap simulation juga memuat inventory_by_time pada resolusi
per jam untuk chart baseline/recommended, arrival marker, threshold, dan outage.

Kompatibilitas prototype tetap didukung:

~~~json
{"material_id": "MAT-001", "facility_id": "ID-JKT-01", "delay_days": 4}
~~~

### POST /api/v1/scenarios/compare

~~~json
{"incident_id": "INC-MKS-FOUR-DAY", "target_downtime_hours": 0}
~~~

Mengembalikan baseline, skenario terurut, ID rekomendasi, dan rationale
deterministik tanpa meminta model AI.

### GET /api/v1/analyses/latest?incident_id={incident_id}

Mengembalikan analysis terbaru untuk incident agar dashboard dapat memulihkan
workflow setelah browser refresh atau backend restart. Jika belum ada analysis,
field analysis bernilai null dan endpoint tetap mengembalikan 200.

### GET /api/v1/analyses/{analysis_id}

Mengambil satu persisted analysis untuk scenario deep link. ID yang tidak ada
menghasilkan error 404 terstruktur.

### POST /api/v1/transaction-drafts

~~~json
{
  "incident_id": "INC-MKS-FOUR-DAY",
  "analysis_id": "ANL-INC-MKS-FOUR-DAY-0",
  "scenario_id": "SCN-TRANSFER-MKS+LOCAL-MKS",
  "requested_by": "demo.operator",
  "idempotency_key": "browser-session-request-001"
}
~~~

Idempotency key mencegah retry membuat draft duplikat. Draft bertransisi lokal
dari DRAFT ke PENDING_APPROVAL. Response memuat version,
source/destination allocation, kuantitas/unit, estimasi biaya, approval policy,
status, dan simulated_only: true. Baseline/wait tidak dapat membuat transaksi.
GET /api/v1/transaction-drafts menyediakan list dengan filter incident_id.

### POST /api/v1/transaction-drafts/{draft_id}/decision

~~~json
{
  "action": "APPROVE",
  "actor": "demo.manager",
  "justification": "Reviewed against deterministic scenario comparison.",
  "expected_version": 1
}
~~~

Hanya PENDING_APPROVAL ke APPROVED atau REJECTED yang valid. Keputusan kedua
menghasilkan 409. Actor approval harus berbeda dari requesting operator;
justification minimal 10 karakter; expected_version mencegah keputusan stale.
Approval hanya mengubah status simulasi dan tidak memanggil write API SAP.

### GET /api/v1/audit

Opsional filter query incident_id. Record memuat audit ID, timestamp, action,
actor, entity type/ID, incident ID, dan ringkasan aman.

### POST /api/v1/demo/reset

Memuat ulang data/demo_seed.json, menghapus analysis/draft/audit mutable, lalu
mencatat satu event DEMO_RESET. Endpoint ini hanya untuk demo lokal.

---

## Legacy Phase 1 contract (historical)

Status: superseded; retained for compatibility history.

Dokumen ini menjadi sumber kebenaran untuk vertical slice awal NSRA Phase 1.
Semua endpoint pada fase ini bersifat offline-safe, deterministic, dan berbasis mock data.

## Prinsip
- Tidak ada credential, token, atau koneksi live SAP/AWS yang diekspos.
- Semua hasil analisis harus reproducible dari fixture lokal.
- Response menyertakan label mode agar tidak disalahartikan sebagai live production data.

## Endpoints

### `GET /health`
Health check proses.

Response:
```json
{
  "status": "ok"
}
```

### `GET /api/v1/status`
Readiness non-sensitive aplikasi lokal.

### `GET /api/v1/inventory`
Mengembalikan posisi inventory mock per material/facility.

Response shape:
```json
{
  "mode": "MOCK VERIFIED",
  "items": [
    {
      "material_id": "MAT-001",
      "facility_id": "ID-JKT-01",
      "on_hand": 420,
      "daily_demand": 60,
      "lead_time_days": 8,
      "days_of_cover": 7.0,
      "risk_level": "high"
    }
  ]
}
```

### `GET /api/v1/shipments`
Mengembalikan shipment context mock yang dipakai untuk simulasi disruption.

Response shape:
```json
{
  "mode": "MOCK VERIFIED",
  "shipments": [
    {
      "shipment_id": "SHP-001",
      "material_id": "MAT-001",
      "facility_id": "ID-JKT-01",
      "origin_port": "SG-SIN",
      "destination_port": "ID-JKT",
      "scheduled_arrival_day": 8,
      "quantity": 600
    }
  ]
}
```

### `POST /api/v1/analysis/disruption`
Menjalankan deterministic time-phased disruption analysis untuk satu inventory item dan satu shipment.

Request shape:
```json
{
  "material_id": "MAT-001",
  "facility_id": "ID-JKT-01",
  "delay_days": 4
}
```

Rules:
- `material_id` dan `facility_id` harus ada di mock ERP.
- `delay_days` harus integer `>= 0`.
- Analisis menggunakan shipment inbound terdekat yang cocok dengan material/facility.
- Simulasi dilakukan per hari dengan horizon default sampai shipment delayed tiba.
- Pada `delayed_arrival_day`, inbound quantity ditambahkan lebih dulu lalu demand harian dikonsumsi pada hari yang sama.

Response shape:
```json
{
  "mode": "MOCK VERIFIED",
  "analysis": {
    "material_id": "MAT-001",
    "facility_id": "ID-JKT-01",
    "delay_days": 4,
    "baseline_arrival_day": 8,
    "delayed_arrival_day": 12,
    "projected_stockout_day": 8,
    "projected_stockout_hours": 192,
    "unmet_demand_units": 240,
    "downtime_days": 4,
    "baseline_risk": "high",
    "disrupted_risk": "high"
  }
}
```

## Error contract
- `404 Not Found`: material/facility atau shipment context tidak ditemukan.
- `422 Unprocessable Entity`: request body tidak valid.

Contoh error:
```json
{
  "detail": "Inventory item not found for material_id=MAT-999 facility_id=ID-JKT-01"
}
```
