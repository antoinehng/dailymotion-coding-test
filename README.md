# dailymotion-coding-test
Coding test for Dailymotion

## Assignment

See [ASSIGNMENT.md](./ASSIGNMENT.md) for the untouched version of the coding test assignment.

## How to Run

### Prerequisites

To **run the project**, the only requirement is **Docker** and **Docker Compose**. No other dependencies need to be installed locally.

**Note**: To run tests locally (outside of Docker), additional dependencies are required. See the [Testing](#testing) section for details.

### Quick Start

1. **Start all services** (database, migrations, and API):
   ```bash
   docker-compose up --build
   ```

   Or using the Makefile:
   ```bash
   make compose up
   ```

2. **Verify the API is running**:
   - API Documentation (Swagger UI): http://localhost:8080/docs

The application will automatically:
- Start PostgreSQL database
- Run database migrations
- Start the FastAPI application with hot-reload enabled

### Development Commands

```bash
# Start services in detached mode
make compose up

# View application logs
make compose logs

# Stop services
make compose down

# Truncate database tables while db container is up
make compose clear-data
```

### Manual Testing

You can test all API endpoints through the **Swagger UI** at http://localhost:8080/docs. The interactive interface allows you to:

- Test all endpoints directly from your browser
- Fill in Basic Auth credentials directly in the Swagger UI (click the "Authorize" button)
- View request/response schemas and examples

For smoother testing, additional endpoints were added beyond the assignment requirements:
- `GET /v1/registration/me` - Get current user information
- `POST /v1/registration/resend-code` - Resend activation code

**Activation Codes**: As suggested in the assignment, activation codes are printed to the terminal output instead of being sent via email. To view them, run:

```bash
make compose logs
```

The activation codes will appear in the application logs when they are generated.



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

## Implementation Process

This section outlines the natural development steps taken to build this project. While working solo on an incomplete project, the focus was on iterative development with CI validation through commits and pull requests, delivering features piece by piece.

1. Repository Architecture and Python Tooling
2. User Domain: First Version and Entities
3. Registration Application Layer
4. HTTP FastAPI Application
5. Adapters Implementation: Database
6. Endpoints Implementation
7. HTTP Error Management
8. Various Improvements

Throughout development, I progressively implemented foundational elements that would be needed for production: logging infrastructure, error management.


## Database

This project uses **PostgreSQL** as the primary database. PostgreSQL offers excellent performance, advanced features (JSON support, extensions, ...), and strong ecosystem support.

### Database Adapter: AsyncPG

For this coding test, we chose **AsyncPG** as the database adapter. AsyncPG is natively built with async Python in mind, providing a simple and direct API that aligns well with FastAPI's async nature. This makes it straightforward for the use cases handled in this test.

#### Production Considerations

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


## Production Ready?

The assignment requested code quality that could go to production. **The code quality itself is production-ready**: the codebase follows solid architectural principles, includes comprehensive testing, proper error handling, type hints, and maintains clean separation of concerns.

However, there are several **non-code related aspects** that would need to be addressed for a true production deployment:

### Configuration Management

- **Centralized configuration**: Drive all configuration through environment variables with proper validation and defaults.
- **Secrets management**: Use a secrets management system instead of hardcoded credentials.

### Security Considerations

- **OpenAPI/Swagger access**: Disable or restrict OpenAPI documentation and Swagger UI in production to prevent exposing API structure.
- **Environment-based security**: Apply different security settings based on environment (development vs. production).

### Infrastructure & Deployment

- **Docker Compose**: Dockerfile is production ready but current docker-compose setup is optimized for development (hot-reload, volume mounts).
- **Database migrations**: Production requires controlled migration strategies: separate deployment steps, rollback procedures, backups, and zero-downtime strategies.


In summary, **code quality is production-ready**, but **operational and infrastructure aspects** need attention for production deployment.
