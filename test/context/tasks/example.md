---
description: Generate a README file for the {SERVICE} service
context:
  - /README.md
  - /standards/doc_standards.md
repo:
  - /src/main.py
  - /examples/
environment:
  - SERVICE
outputs:
  - /README.md
guarantees:
  - Follows conventional markdown format
  - Includes service description
  - Includes usage instructions
---

Generate a README.md file for the {SERVICE} service based on the context files provided.

The README should:
- Include a clear service description
- Provide setup and installation instructions
- Include usage examples
- Follow the documentation standards specified in the context
- Reference patterns from existing code in the repo