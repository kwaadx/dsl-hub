# DSL Hub

A modern platform for domain-specific language development and execution.

## Overview

DSL Hub is a comprehensive platform that allows users to create, manage, and execute domain-specific languages. It consists of a Vue.js frontend and a FastAPI backend, providing a seamless experience for DSL development.

## Features

- Interactive DSL editor with syntax highlighting
- Real-time DSL execution and visualization
- Version control for DSL definitions
- User management and access control
- API integration for external systems

## Architecture

The project is structured as a monorepo with the following components:

- `apps/web`: Vue.js frontend application
- `apps/agent`: FastAPI backend service
- `packages`: Shared libraries and utilities
- `schemas`: JSON Schema definitions for DSL validation

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.10+ (for local development)

## Getting Started

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/dsl-hub.git
   cd dsl-hub
   ```

2. Create a `.env.local` file with your local configuration:
   ```bash
   MODE=dev
   ```

3. Start the services:
   ```bash
   docker-compose up
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:5000

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/dsl-hub.git
   cd dsl-hub
   ```

2. Set up the frontend:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

3. Set up the backend:
   ```bash
   cd apps/agent
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload --port 5000
   ```

## Environment Variables

The application can be configured using environment variables. Create a `.env.local` file in the root directory to override the default settings.

See the `.env` file for available configuration options.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
