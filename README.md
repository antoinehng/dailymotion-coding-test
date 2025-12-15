# dailymotion-coding-test
Coding test for Dailymotion

## Assignment

See [ASSIGNMENT.md](./ASSIGNMENT.md) for the untouched version of the coding test assignment.

## Architecture

This project combines **Hexagonal Architecture** (structure) with **Domain-Driven Design** (domain modeling) for maintainability and scalability.

### Structure

```
src/
├── domain/              # DDD: Entities, value objects, business rules
├── application/         # Hexagonal: Use cases, ports (interfaces)
│   └── registration/ports/  # Repository interfaces
├── infrastructure/      # Hexagonal: Adapters (DB, SMTP implementations)
└── http/                # Hexagonal: HTTP API powered by FastAPI (routes, schemas, Dependency Injections)
```

**Dependency flow**: `http` → `infrastructure` → `application` → `domain`

### Principles

**Hexagonal Architecture** (from Ports & Adapters):
- **Layers**: Enforce dependency direction (higher → lower)
- **Ports**: Interfaces defined in `application/ports/`
- **Adapters**: Implementations in `infrastructure/`
- **Benefit**: Swap infrastructure without changing business logic

**Domain-Driven Design** (from DDD):
- **Domain layer**: Pure business logic (entities, value objects)
- **Application layer**: Orchestrates use cases, potentially across multiple domains
- **Benefit**: Business rules localized, code reflects domain concepts

**Combined benefits**:
- Testable: Domain logic independent of infrastructure
- Scalable: Requires upfront investment in ports/interfaces and layer separation, but enables adding new domains (e.g., `domain/payment/`) or swapping infrastructure (PostgreSQL → MongoDB) without touching current business logic
- Standard: Using proven architectures patterns instead of reinventing the wheel allows focus on business features

### Import Enforcement

Python cannot enforce architectural boundaries. We use [Import Linter](https://import-linter.readthedocs.io/en/stable/) to automatically enforce rules in CI/CD.

**Contracts** (`.importlinter`):
- **Layers**: Enforces `http` → `infrastructure` → `application` → `domain` dependency direction
- **Protected**: Domain entities and application ports only accessible to allowed layers
- **Acyclic siblings**: Prevents circular dependencies within layers

```bash
make check-imports  # Validate import rules
```

## Database

This project uses **PostgreSQL** as the primary database. PostgreSQL offers excellent performance, advanced features (JSON support, extensions, ...), and strong ecosystem support.

### Database Adapter: AsyncPG

For this coding test, we chose **AsyncPG** as the database adapter. AsyncPG is natively built with async Python in mind, providing a simple and direct API that aligns well with FastAPI's async nature. This makes it straightforward for the use cases handled in this test.

### Production Considerations

In a production environment, the choice of database adapter may differ:

- **ORMs like SQLAlchemy**: Can improve syntax, provide better abstractions, and thus the advantages of asyncpg are less obvious.
- **Psycopg**: Since v3 it also has robust async Python support and may be preferable in certain scenarios
- **Real-world factors**: The choice depends on many factors beyond codebase simplicity, including:
  - Connection pooling strategies (application-level vs. database-level poolers like PgBouncer)
  - Performance characteristics under production load
  - Team familiarity and maintenance considerations
  - Integration with existing infrastructure

**Note**: In practice, AsyncPG has shown slower connection times when connecting to a PgBouncer pooler at the database level (as opposed to application-level pooling), an issue not present with Psycopg3. Production decisions should be based on real-life testing and infrastructure requirements, not just codebase preferences.


