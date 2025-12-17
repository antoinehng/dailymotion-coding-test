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

**Contracts** ([`.importlinter`](.importlinter)):
- **Layers**: Enforces `http` → `infrastructure` → `application` → `domain` dependency direction
- **Independance**: Domain entities and application ports should be independent from each other

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

## Testing

This project uses pytest for testing with comprehensive coverage requirements. Tests are organized by layer (domain, application, infrastructure, http) and include unit tests and integration tests.

```bash
# Run all tests with coverage report
make test

# Run tests without coverage
uv run pytest
```

### Unit

Unit tests focus on testing individual components in isolation with all dependencies mocked. This approach ensures fast execution, no external dependencies, and focused testing of component-specific logic.

**Domain layer**: Tests domain entities, value objects, and business rules without any external dependencies.

**Application layer**: Tests use cases with mocked ports (repositories, services), verifying business logic orchestration and error handling.

**HTTP layer**: Endpoint tests mock use cases using FastAPI's dependency override mechanism, focusing on HTTP-specific concerns:
- Request/response handling and status codes
- Error formatting and exception handling
- Authentication and authorization
- Dependency injection wiring


### Integration

Integration tests verify that components work together correctly. Currently, integration tests focus on database adapters using a real PostgreSQL database with transaction-based isolation.

Each test runs in its own transaction that is automatically rolled back after completion, ensuring complete test isolation without any manual cleanup. This approach provides fast, reliable testing against actual PostgreSQL, catching real SQL errors, data type issues, and constraint violations that mocks would miss.

These tests only run if `TEST_DATABASE_URL` (or `DATABASE_URL`) is set to a database URL; otherwise they are automatically skipped, allowing the test suite to run in environments without database access. A PostgreSQL service is configured in the GitHub Actions CI workflow, so these integration tests run automatically on every push and pull request. Fixtures in `tests/infrastructure/conftest.py` provide database connections, repositories, and handle migrations automatically.

```bash
# Start the database
docker-compose up -d postgres

# Set the database URL and run integration tests
export TEST_DATABASE_URL="postgresql://identity_user:identity_password@localhost:5432/identity_db"
make test
```

### End-to-End

End-to-end tests were not implemented in this coding test. Instead, we stopped at unit tests that mock use cases in API endpoint testing. This approach aligns with the current simplicity of the project—with straightforward use cases and a single domain, the added complexity of full-stack E2E tests doesn't provide sufficient value at this stage.

End-to-end tests that exercise the entire stack (HTTP → Application → Infrastructure → Database) are valuable for validating complete user flows and catching integration issues across layers. However, they are typically slower, more complex to maintain, and better suited for pre-deployment validation in more complex systems. For true end-to-end testing, consider running such tests in a remote environment that closely matches production (e.g., staging or a dedicated E2E testing environment) to validate behavior in conditions similar to production, including network latency, resource constraints, and real external service interactions.


