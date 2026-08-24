# Symmio Analytics Dashboard

Angular dashboard for aggregated SYMMIO frontend and solver analytics across the configured chains.

## Requirements

- Node.js 22
- npm

## Local development

Install dependencies and start the aggregate dashboard:

```bash
npm install
npm start -- --configuration aggregate
```

Open [http://localhost:4200](http://localhost:4200). The aggregate configuration loads every chain listed in `src/environments/environment.aggregate.ts`; the default development environment is intentionally empty.

Run the unit tests:

```bash
npm test -- --watch=false --browsers=ChromeHeadless
```

Build the aggregate dashboard:

```bash
npm run build -- --configuration aggregate
```

## Data sources and entity discovery

Each chain configuration in `src/environments/environment.*.ts` provides its analytics subgraph URL, supported collaterals, decimals, and fallback entities.

At startup, the dashboard queries `symmioEntities` from every configured subgraph and uses entities with type `Affiliate` or `Solver` for chart series and filters. Entity addresses are matched case-insensitively. Configured entities remain the fallback when a subgraph does not expose `symmioEntities`, times out, or returns an error.

History rows whose address is absent from the entity response are retained as `Unknown`, except for the maintained address aliases such as Trading SDK, Echoes, and Bulla.

## Display rules

- Chain, frontend, and solver series without trade-volume data are omitted.
- Chain and frontend controls are sorted by aggregated trade volume, highest first.
- Frontends with more than zero but less than `$100K` aggregated trade volume are combined as `Others` in filters, charts, legends, and tooltips.
- Tooltip entries are sorted by value, highest first, and zero-value entries are hidden.
- Development builds show compact, human-readable trade volume beside each frontend in the dropdown.

## Headline metrics compatibility

The Deposits and Traded Volume headline cards intentionally retain the configured legacy affiliate population and the pagination behavior used by the current production `main` branch. This keeps those two totals comparable with the existing dashboard while charts and entity filters use subgraph-discovered entities and corrected pagination.
