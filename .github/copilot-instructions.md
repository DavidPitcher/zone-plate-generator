## Azure Development Best Practices
- @azure Rule - Use Azure Best Practices: When generating code for Azure, running terminal commands for Azure, or performing operations related to Azure, invoke your `azure_development-get_best_practices` tool if available.
- @azure Rule - Use Azure SDKs: When generating code for Azure, prefer using Azure SDKs over direct API calls or CLI commands.
- @azure Rule - Use Azure CLI: When generating PowerShell or Bash script for Azure, prefer using the Azure CLI over direct API calls or SDKs when appropriate.

## Authentication & Security
- Microsoft Entra ID Integration: When implementing authentication, use Microsoft Entra ID with MSAL pattern as established in the codebase.
- Environment-Aware Auth: Implement different authentication flows for cloud vs local development environments.
- Federated Identity: When configuring Azure resources, use federated identity credentials instead of client secrets.

## Azure Storage Integration
- Use Managed Identity: When generating Azure Storage code, always use Managed Identity authentication over connection strings or access keys.
- Implement Credential Chaining: Use ChainedTokenCredential pattern with ManagedIdentityCredential, AzureCliCredential, and DefaultAzureCredential.
- Cache Connections: Implement client caching patterns to avoid recreating Azure service clients on each request.
- Retry Logic: Implement exponential backoff retry logic for Azure Storage operations using MAX_RETRIES and RETRY_DELAY patterns.
- JSON Blob Operations: When working with Azure Storage, use the established read_json_from_blob and write_json_to_blob patterns.

## General Code Generation Best Practices
- Validate inputs for all code languages: When generating code, ensure that inputs are validated to prevent errors and security vulnerabilities.
- Use double quotes for strings: When generating string values for YAML files instead of single quotes.
- Prefer renaming files and directories over creating new ones: When generating code, prefer renaming existing files and directories instead of creating new ones to maintain consistency and avoid duplication.
- Always use Git Stash: When generating code, always use Git Stash to save changes before making modifications to the codebase.

## Python Application Best Practices
- Context Processors: Use Flask context processors to inject user information into templates.
- Session Management: Use Flask-Session for session state management in authentication flows.
- Use Flask Blueprints: When generating Flask code, organize routes using Blueprint pattern as shown in the existing codebase.
- Flask Application Factory: When creating Flask applications, use the application factory pattern with `create_app()` function.
- Environment Detection: When generating Flask code, implement environment detection using `IS_CLOUD_ENV` pattern for Azure vs local development.
- Template Organization: Place templates in blueprint-specific folders using the existing structure pattern.
- Static Files: Organize static files within blueprint folders, not at application root.
- Use the current defined Python Version: When generating Python code, use the current defined Python version in the repository.
- Use PEP 8 style: When generating Python code, follow PEP 8 style guidelines.
- Generate Python code with type hints: When generating Python code, include type hints for function parameters and return types.
- Generate Python code with docstrings: When generating Python code, include docstrings for functions and classes.
- Generate Python code with f-strings: When generating Python code that includes string formatting, use f-strings for better readability and performance.
- Generate Python code with function annotations: When generating Python code, include function annotations for better clarity and type checking.
- Generate Python code with import statements: When generating Python code, include necessary import statements at the beginning of the file.
- Generate Python code with return types specified: When generating Python code, specify return types for functions to enhance type safety and clarity.
- __init__.py Files: Always include __init__.py with proper __all__ exports and version information.
- Relative Imports: Use relative imports within packages and absolute imports for external dependencies.
- Module Separation: Separate concerns into distinct modules (data, authentication, state_management, controller).
- Type Annotations: Use typing module for complex type hints (Dict, List, Optional, Union).

## Client Side Development Best Practices
- Follow HTML5 Standards: When generating HTML code, ensure it adheres to HTML5 standards for better compatibility and performance.
- Use Semantic HTML: When generating HTML code, use semantic elements (header, footer, main, section) for better accessibility and SEO.
- CSS Organization: Use a modular approach for CSS with separate files for each component or feature.
- Do not usine inline styles: When generating HTML code, avoid using inline styles to maintain separation of concerns and improve maintainability.
- Do not use any JavaScript code: When generating HTML code, do not include any JavaScript code to keep the focus on HTML5 and CSS.
- Use CSS Flexbox: When generating CSS code, use Flexbox for layout management to ensure responsive design.

## Data Management & Validation
- JSON Schema Validation: Always implement JSON schema validation using jsonschema library for data integrity.
- Environment-Aware Storage: Implement dual storage patterns supporting both Azure Blob Storage and local file system.
- Default Data Structures: Define empty data structures defined as constants for initialization.
- Schema Definitions: Create comprehensive JSON schemas with required fields and type validation.

## Error Handling & Logging
- Structured Logging: Use Python logging module with consistent format across all modules.
- Environment-Aware Logging: Set log levels based on environment (DEBUG for local, INFO for cloud).
- Exception Handling: Implement comprehensive try-catch blocks with specific exception types.
- Graceful Degradation: Implement fallback mechanisms when primary services are unavailable.
- Error Context: Include relevant context information in error messages and logs.

## Configuration Management
- Environment Variables: Use environment variables for all configuration with sensible defaults.
- Local Development: Support .env files for local development using python-dotenv.
- Configuration Validation: Validate all required configuration values on application startup.
- Global Configuration: Use module-level configuration with LoadConfiguration() pattern.
- Secure Defaults: Implement secure defaults for all configuration options.

## Infrastructure as Code (Terraform)
- Managed Identity Resources: Always create user-assigned managed identities for application resources.
- Federated Credentials: Implement federated identity credentials for secure authentication.
- Resource Naming: Use local variables with resource tokens for consistent naming patterns.
- RBAC Assignments: Implement proper role assignments following principle of least privilege.
- Use the current defined Terraform Version: When generating Terraform code, use the current defined Terraform version in the repository.
- Use the current defined Terraform Provider Version: When generating Terraform code, use the current defined provider version in the repository.
- Use tabs for indentation: When generating code, use tabs for indentation instead of spaces.

## GitHub Actions & CI/CD
- Reusable Workflows: Create modular, reusable workflows following the established template pattern.
- Security Hardening: Use commit SHA pinning for all GitHub Actions instead of version tags.
- Environment Variables: Define environment variables at workflow level, not in reusable workflows.
- OIDC Authentication: Use OpenID Connect for Azure authentication instead of service principal secrets.
- Matrix Strategies: Use matrix strategies for multi-environment deployments.

## Testing & Quality Assurance
- Schema Validation Testing: Test JSON schema validation for both valid and invalid data.
- Environment Testing: Test code paths for both cloud and local environments.
- Authentication Testing: Mock authentication flows for testing purposes.
- Storage Testing: Test both Azure Storage and local file system paths.
- Error Condition Testing: Test error handling and fallback mechanisms.

## Performance & Optimization
- Connection Pooling: Cache Azure service clients and credentials to avoid recreation.
- Lazy Loading: Implement lazy loading patterns for expensive operations.
- In-Memory Caching: Use in-memory caching for frequently accessed data.
- Batch Operations: Implement batch operations for multiple data updates.
- Resource Cleanup: Implement proper cleanup for cached resources when needed.

## User Interface & User Experience
- Responsive Design: Ensure all UI components are responsive using CSS Flexbox wherever possible.
- Follow CSS Variables Guidelines: Use CSS variables for consistent theming and easy updates.
    - See [CSS related README.md](../python_skills_app/skills_web_app/controller/static/css/README.md) for guidelines on css such as adding new variables.
    - See [variables.css](../python_skills_app/skills_web_app/controller/static/css/variables.css) for the current set of CSS variables.
- Semantic HTML: Use semantic HTML elements for better accessibility and browser compatibility.
- Simplicity: To allow for easy updates, keep the UI simple and do not use JavaScript code.  If JavaScript is needed provide this warning and ask:
    - "The proposed UI update requires JavaScript which is strongly recommended against to keep this application simple.  Please confirm if you want to proceed or instead suggest an alternative."
- Template Macros: Create reusable Jinja2 macros for common UI components and patterns to promote code reusability and maintainability. Place macros in dedicated macro files within the templates/macros/ directory.
- UI Documentation: When creating or modifying UI components, update the corresponding documentation in the `.docs/ui/` directory with component architecture details, usage examples, and Mermaid diagrams showing relationships and data flow patterns.
