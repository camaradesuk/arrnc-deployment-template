# Audio Streaming Web App - Deployment Template

**Purpose:** This is a template repository that demonstrates how to set up a CI/CD pipeline for deploying web applications to `arrnc-api.ccbs.ed.ac.uk` using Docker, GitHub Actions, and a self-hosted runner. Use this as a starting point for new projects or as a reference for adding deployment capabilities to existing repositories.

This repository contains a basic web application for streaming audio files, containerized with Docker, and deployed using GitHub Actions to `arrnc-api.ccbs.ed.ac.uk`.

## Quick Start

**Using this template:**

1. **Fork or use as a template** for your project
2. **Customize the application code** in the `app/` directory
3. **Update the Dockerfile** if your application has different requirements
4. **Configure the workflow** in `.github/workflows/deploy.yml` to match your project
5. **Contact the server administrator** to get deployment access

**Using as a reference for existing projects:**

1. **Copy the workflow** from `.github/workflows/deploy.yml` to your existing repository
2. **Adapt the Dockerfile** patterns for your application
3. **Review the deployment parameters** below
4. **Contact the server administrator** to get deployment access

## Critical Requirements

⚠️ **Container names must be either `production-api` or `dev-api` only.** The server-managed deployment script will refuse any other container names. This restriction exists because:

- `production-api` containers are served at the production URL
- `dev-api` containers are served at the development URL

⚠️ **Contact the server administrator** to:

- Get your project whitelisted for deployment on `arrnc-api.ccbs.ed.ac.uk`
- Register a self-hosted runner for your repository


⚠️ **Repository maintainers must:**

- Give the GitHub account `arrnc-bot` **read access** to your repository so it can pull the built container images from GitHub Container Registry

## How the Deployment Pipeline Works

```mermaid
graph LR
    A[Developer Push] --> B[GitHub Actions]
    B --> C[Build & Push Image]
    C --> D[Deploy via Self-Hosted Runner]
    D --> E[Secure Deployment Script]
    E --> F[Running Container]
```

**The pipeline flow:**

1. **Push to GitHub**: When you push to a configured branch (e.g., `main` or `dev`), the GitHub Actions workflow is triggered
2. **Build and Push**: The `build-and-push` job builds a Docker image and pushes it to GitHub Container Registry (ghcr.io)
3. **Deploy**: The `deploy` job runs on the self-hosted runner at `arrnc-api.ccbs.ed.ac.uk`
   - For security, the runner doesn't have direct Docker access
   - Instead, it calls the `container-web-deploy` script (maintained by the server administrator)
   - The script acts as a secure gatekeeper, validating inputs and executing Docker commands

## Understanding the GitHub Actions Workflow

The `.github/workflows/deploy.yml` file contains two distinct jobs that run sequentially:

### Workflow Triggers (Customizable)

The example workflow triggers on pushes to `main` and `dev` branches, but this can be adapted to your needs:

- **Different branches**: `push: branches: [production, staging, feature/*]`
- **Manual triggers**: `workflow_dispatch:` for on-demand deployments
- **Tag-based releases**: `push: tags: ['v*']` for version-based deployments  
- **Pull request builds**: `pull_request:` for testing before merge
- **Scheduled deployments**: `schedule:` with cron expressions
- **Multiple triggers**: Combine any of the above

*See the [GitHub Actions documentation](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows) for all trigger options.*

### Job 1: `build-and-push`

**Purpose**: Builds your Docker image and pushes it to GitHub Container Registry (ghcr.io)

**Key Steps**:

- Checks out your code
- Sets up Docker Buildx for advanced building features  
- Logs into GitHub Container Registry using `GITHUB_TOKEN`
- Builds the Docker image using your `Dockerfile`
- Tags the image with the branch name (e.g., `main`, `dev`)
- Pushes the image to `ghcr.io/your-username/your-repo:branch-name`

**Customization Options**:

- Add additional build arguments to the Docker build step
- Include security scanning steps
- Add image optimization or multi-platform builds
- Customize image tags or add additional tags

### Job 2: `deploy`

**Purpose**: Deploys your container to `arrnc-api.ccbs.ed.ac.uk`

**Key Steps**:

- Runs on the self-hosted runner (physically located on the deployment server)
- Determines container name based on the branch (`main` → `production-api`, `dev` → `dev-api`)
- Calls the server-managed `container-web-deploy` script
- Passes the container name and image URL to the deployment script

**Branch to Container Mapping** *(Customizable with server administrator approval)*:

- `main` branch → `production-api` container
- `dev` branch → `dev-api` container
- Other branches → No deployment (workflow will skip the deploy job)

*Note: This mapping can be customized to use different branch names or trigger patterns, but requires coordination with the server administrator to ensure proper URL routing.*

## Customizing the Workflow

The GitHub Actions workflow is highly adaptable to your project's needs:

### Workflow Trigger Examples

```yaml
# Manual deployment trigger
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'dev'
        type: choice
        options:
        - dev
        - production

# Tag-based releases
on:
  push:
    tags:
      - 'v*'

# Multiple triggers
on:
  push:
    branches: [main, dev]
  workflow_dispatch:
  schedule:
    - cron: '0 2 * * 1'  # Weekly Monday 2 AM deployment
```

## GitHub Environments and Secrets

This template uses GitHub Environments to scope secrets and apply protections per environment. In `/.github/workflows/deploy.yml` the deploy stage is split into two jobs that target different environments:

```yaml
jobs:
  deploy-production:
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    runs-on: self-hosted
    environment: production
    steps:
      - name: Deploy Production
        run: |
          sudo container-web-deploy production-api ghcr.io/${{ github.repository }}:main \
            -e APP_MODE=production \
            -e API_TOKEN=${{ secrets.API_TOKEN }}

  deploy-development:
    needs: build-and-push
    if: github.ref == 'refs/heads/dev'
    runs-on: self-hosted
    environment: development
    steps:
      - name: Deploy Development
        run: |
          sudo container-web-deploy dev-api ghcr.io/${{ github.repository }}:dev \
            -e APP_MODE=development \
            -e API_TOKEN=${{ secrets.API_TOKEN }}
```

### What this does

- Binds jobs to environments (`production` and `development`) so each job can access that environment’s secrets via `${{ secrets.<NAME> }}`.
- Restricts which branch can deploy to each environment using job-level `if:` guards:
  - `main` → `production`
  - `dev` → `development`
- Passes two example environment variables to the container:
  - A hardcoded value (`APP_MODE`) suitable for non-sensitive config.
  - A secret (`API_TOKEN`) sourced from the environment’s secrets.

### How to create environments and add secrets

1. In your repository, go to Settings → Environments.
2. Click “New environment” and create:
   - `production`
   - `dev`
3. For each environment, open it and add secrets:
   - Click “Add secret”.
   - Name: `API_TOKEN` (or your preferred name; keep it consistent with the workflow).
   - Value: the token/string your app needs.

Official docs:

- Using environments for deployment: <https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment>
- Creating encrypted secrets for an environment: <https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-an-environment>
- Workflow syntax for environments (job-level `environment`): <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idenvironment>
- Secrets context reference: <https://docs.github.com/en/actions/learn-github-actions/contexts#secrets-context>

### Limiting which branches can deploy to each environment

This template enforces branch-to-environment mapping within the workflow using `if: github.ref == 'refs/heads/<branch>'` on each deploy job. You can add defense in depth by restricting allowable branches directly on the environment:

1. Settings → Environments → choose the environment (e.g., `production`).
2. Under “Deployment branches and tags”, restrict to the branch that’s allowed to deploy (e.g., `main` for `production`, `dev` for `dev`).

Docs: Deployment branches and tags

- <https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#deployment-branches-and-tags>

Additional reference (same concept, legacy docs path):

- <https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments#deployment-branches-and-tags>

You can also set optional protection rules like required reviewers or wait timers to gate deployments:

- <https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#environment-protection-rules>

These protection settings are configured per environment under your repository’s Settings → Environments. They let you enforce branch restrictions and other controls (required reviewers, wait timers, required secrets) independently from the workflow logic.

### Tips and troubleshooting

- If your editor warns that `secrets.API_TOKEN` is undefined, ensure you created it as an environment secret for both `production` and `dev`.
- Secret names are case-sensitive. The workflow expects `API_TOKEN` by default; change either the workflow or the secret name so they match.
- If you add more environment-specific secrets, reference them the same way: `${{ secrets.MY_SECRET }}`.

### Deployment Step Customization

**Pre-deployment steps:**

- Add database migrations
- Run health checks
- Validate configurations

**Post-deployment steps:**

- Verify deployment success
- Run integration tests
- Send notifications (Slack, email, etc.)

**Example customizations:**

```yaml
# Add a database migration step before deployment
- name: Run Database Migrations
  run: |
    # Your migration commands here
    echo "Running database migrations..."

# Add post-deployment health check
- name: Health Check
  run: |
    # Wait for container to be ready and test endpoints
    sleep 30
    curl -f http://localhost:8070/health || exit 1
```

### Build Step Customization

**Additional options for the `build-and-push` job:**

- Add security scanning steps
- Include image optimization
- Add multi-platform builds
- Customise repository tags
- Customise image tags
- Include build arguments

## Deployment Script Reference

The `container-web-deploy` script is maintained by the server administrator (not by developers using this template). As a developer, you call it from your workflow; the server admin keeps it installed and up to date.

### Script Parameters (updated)

The script now supports both positional arguments and named flags, plus passing custom environment variables.

```bash
# Basic deployment (uses defaults: container port 5000, volume path /app/audio_data)
container-web-deploy <container-name> <image-name>

# Backward-compatible positional overrides
container-web-deploy <container-name> <image-name> [container_port] [container_volume_path]

# Named flags (recommended)
container-web-deploy <container-name> <image-name> \
  [-p|--port <container_port>] \
  [-v|--volume <container_volume_path>] \
  [-e|--env KEY=VALUE]...    # repeatable
```

Notes:

- Host port and host volume locations are fixed and managed on the server. You can only change the container-internal port and the container-internal mount path.
- Allowed container names are strictly whitelisted by the server: only `production-api` and `dev-api` are accepted.

**Parameters:**

- `container-name`: REQUIRED. Must be `production-api` or `dev-api`.
- `image-name`: REQUIRED. Full Docker image URL from GitHub Container Registry.
- `-p, --port`: OPTIONAL. Container-internal port your app listens on (default: `5000`).
- `-v, --volume`: OPTIONAL. Container-internal mount point for persistent data (default: `/app/audio_data`).
- `-e, --env KEY=VALUE`: OPTIONAL, repeatable. Extra environment variables to pass into the container.

### Example Deployment Calls

```bash
# Production deployment (basic)
container-web-deploy production-api ghcr.io/yourusername/your-repo:main

# Development deployment (basic)
container-web-deploy dev-api ghcr.io/yourusername/your-repo:dev

# Development deployment overriding container-internal port (positional)
container-web-deploy dev-api ghcr.io/yourusername/your-repo:dev 3000

# Production deployment using named flags
container-web-deploy production-api ghcr.io/yourusername/your-repo:main -p 8080 -v /app/custom_data

# Development deployment with custom environment variables
container-web-deploy dev-api ghcr.io/yourusername/your-repo:dev -e LOG_LEVEL=debug -e WORKERS=4
```

## Configuration Reference

### What You Configure (Required)

Update `.github/workflows/deploy.yml` to reflect your project:

- **Image names** to match your repository
- **Container names** (must be `production-api` or `dev-api`)
- **Workflow triggers** (optional customization)
- **Custom deployment steps** (optional)
- **Custom port or volume requirements** (optional)

### What the Server Administrator Configures

The server administrator handles:

- **Host port assignment** for your application
- **Host volume paths** for persistent data
- **MS SQL Server credentials** for database access(if needed)

### Application Requirements

Your application should be designed to:

- **Listen on a configurable port** (default: 5000)
- **Use configurable volume mount points** (default: /app/audio_data)
- **Handle standard Docker signals** for graceful shutdown



## Data and Volume Management

### Application Data Files

**Note**: The `app/audio_data/` directory is just an example for this audio streaming demo. You can configure your own data directories based on your application's needs.

For this audio streaming example:

- Audio files (e.g., `.mp3` files) are placed in the `app/audio_data/` directory locally
- These files are not checked into git (see `.gitignore`)
- On `arrnc-api.ccbs.ed.ac.uk`, files are mapped to persistent storage managed by the administrator

### Volume Mapping

Your application can use any volume path you need:

- **Example container path**: `/app/audio_data` (used by this demo)
- **Fully customizable**: Specify your own paths via deployment parameters (see Deployment Script Reference)
- **Default if not specified**: `/app/audio_data`
- **Host-side storage**: Managed by the server administrator

## Optional: Database Connectivity

**Note**: This section only applies if your application requires database access.

If your application requires MS SQL Server database access, the deployment infrastructure on `arrnc-api.ccbs.ed.ac.uk` supports automatic configuration:

- If configured by the server administrator, `MSSQL_SA_USERNAME` and `MSSQL_SA_PASSWORD` are securely sourced on the server and automatically injected into your container at deploy time by `container-web-deploy`.
- Your application should read these environment variables for database connectivity; you do not need to add them to your workflow.

**Example usage in your application:**

```python
import os
# Read from environment variables provided by the deployment script
db_username = os.getenv('MSSQL_SA_USERNAME')
db_password = os.getenv('MSSQL_SA_PASSWORD')
# Connect to your database server using these credentials
```

## Project Structure

- `app/`: Contains the Flask web application
  - `app.py`: The main application file
  - `templates/index.html`: The HTML template for the web interface
  - `audio_data/`: A directory to store your audio files
- `Dockerfile`: Defines the Docker container for the application
- `.github/workflows/deploy.yml`: The GitHub Actions workflow for building and deploying the application

## Example Applications

This template can be adapted for virtually any type of containerized application:

- **Flask/Django web apps**
- **Node.js applications**  
- **Static site generators**
- **API services**
- **File processing applications**
- **Microservices**
- **Data processing pipelines**
- **Real-time applications**

Just modify the `Dockerfile` and application code in the `app/` directory to suit your needs! The deployment infrastructure on `arrnc-api.ccbs.ed.ac.uk` supports any web application that can run in a Docker container.

## Monitoring and Logs

Container logs are available through a web-based log viewer (Dozzle):

- **Access URL**: `https://arrnc-api.ccbs.ed.ac.uk/spunlogs`
- **Credentials**: Contact the server administrator for access credentials
- **What you can see**: Real-time container logs, historical logs, search and filtering

This allows you to monitor your application's behavior and troubleshoot issues without requiring direct server access.

## Getting Help

- **For deployment access**: Contact the server administrator
- **For log viewer access**: Contact the server administrator for URL and credentials
- **For workflow customization**: Refer to the [GitHub Actions documentation](https://docs.github.com/en/actions)
- **For custom requirements**: Discuss with the server administrator
