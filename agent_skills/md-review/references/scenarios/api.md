# API Scenario Checklist — API Document

Enabled when the scenario parameter is `api`. Checks whether the API document contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Do error codes cover all exception scenarios and troubleshooting suggestions?
2. Is the authentication method (e.g., Admin/User permissions) clear?
3. Are the Request/Response examples real and runnable?

## Key Focus
Endpoint contracts + data models + error dictionary
- Includes: **Error Code List** (all error codes and their meanings)

## Required Content (deduct if missing)

### Interface Specification
- [ ] **Interface Overview**: Are the document's purpose/service scope explained?
- [ ] **Basic Information**: Are Base URL, version, and authentication method clear?
- [ ] **Interface List**: Are all endpoints numbered (ENDPOINT-1, ENDPOINT-2...)?
- [ ] **HTTP Methods**: Is each endpoint's method (GET/POST/PUT/DELETE/PATCH) correct?

### Endpoint Definitions (for each endpoint)
- [ ] **Path**: Is the endpoint path complete and RESTful?
- [ ] **Request Parameters**: Are parameters (path/query/request body) listed: name/type/required/default/validation rules?
- [ ] **Response Format**: Is the success response structure defined (fields/type/example)?
- [ ] **Error Codes**: Are error responses defined (status code/error code/error message/fix suggestion)?
- [ ] **Examples**: Does each endpoint have request/response examples?
- [ ] **Boundary Conditions**: Is the behavior for empty parameters/invalid input/over-limit input explained?

### Consistency
- [ ] **Naming Conventions**: Are endpoint and field names consistent (camelCase/snake_case unified)?
- [ ] **Pagination**: Do list interfaces define pagination parameters (page/size/cursor)?
- [ ] **Versioning Strategy**: Is the version management strategy explained (URL versioning vs header versioning)?
- [ ] **Rate Limiting**: Are rate limits/quotas explained?
- [ ] **Idempotency**: Is idempotency explained for write operations?

### Security
- [ ] **Authentication**: Is the authentication method clear (API Key / OAuth2 / JWT)?
- [ ] **Authorization**: Are permission levels/role-based access control explained?
- [ ] **Sensitive Data**: Are masking/encryption requirements marked for sensitive fields?
- [ ] **Transport Security**: Is HTTPS/TLS enforced?

### Testing and Change Management
- [ ] **Test Cases**: Are there test cases for key interfaces (input → expected output/status code)?
- [ ] **Change Log**: Are version changes recorded (with breaking changes marked)?
- [ ] **Deprecation Strategy**: Is the handling strategy for deprecated interfaces explained?

### 5W1H Check (API context)
- [ ] **What**: What capability does this API provide?
- [ ] **Who**: Who calls this API (internal/external/third-party)?
- [ ] **When**: When is it called / what are the trigger conditions?
- [ ] **Where**: Deployment environment / call entry point?
- [ ] **Why**: Why does this interface exist (business purpose)?
- [ ] **How**: How is it called (authentication/request/response chain)?

## Completeness Issue Markers
- Endpoints without request/response examples
- Error codes not defined (callers cannot handle failures)
- Parameters missing type/required markers
- Authentication method not stated

## Scoring Guide
| Finding | Deduction |
|---|---|
| Missing interface list | -15 |
| Endpoint missing request parameter definitions | -5 per endpoint |
| Endpoint missing response format definitions | -5 per endpoint |
| Missing error code definitions | -12 |
| Missing examples | -5 per example |
| Authentication method not stated | -15 |
| Missing test cases | -10 |
| Missing change log | -8 |
| Inconsistent naming | -5 |
| Boundary conditions not explained | -3 per occurrence |
