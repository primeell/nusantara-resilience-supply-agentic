# Demo data

`demo_seed.json` contains synthetic, realistic data for a reproducible NSRA demo.
It is not SAP production data and must not be presented as an actual company record.

Units are explicit (`kg`), money is IDR, and timestamps use timezone-aware ISO 8601.
The five incidents cover a normal shipment, a four-day delay, insufficient origin
stock, an unavailable supplier, and a case where every mitigation is infeasible.

The fixture also includes WGS84 reference locations for ports, factories,
warehouses, and modeled suppliers, plus seven historical portfolio snapshots for
the exposure and approval trend. The latest snapshot is reconciled with current
local state at read time; the earlier points remain synthetic reference history.
