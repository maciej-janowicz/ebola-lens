# EbolaLens project charter

## Operational purpose

EbolaLens will turn official outbreak reports into lightweight, reproducible situational-awareness outputs. Its first users are analysts supporting INSP, WHO, Africa CDC, and field organizations.

The project will organize situational awareness around three areas:

- epidemic evolution;
- observation and reporting quality;
- response-system pressure.

## MVP-0 scope

MVP-0 will:

- register official reports;
- preserve data provenance;
- detect new and changed documents;
- extract basic data;
- validate totals;
- maintain an explicit revision register;
- publish lightweight static outputs.

MVP-0 will not provide clinical recommendations, official forecasts, automated operational decisions, complex spatial models, or a heavy dashboard.

The complete workflow must run on an ordinary laptop without HPC, paid cloud services, or a database server. Observed, corrected, and modeled data must remain clearly separated in storage, processing, and published outputs.
