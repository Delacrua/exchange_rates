# Exchange_rates

This project is a aiohttp web service for fetching and converting exchange rates between different currencies. 
It supports retrieving exchange rates from various cryptocurrency exchanges and caching the results 
for improved performance.
Currently supports Binance and KuCoin as available exchanges.

## Prerequisites

- Docker
- Docker Compose

Before building the project, ensure that you have the latest version (V2) of the Docker Compose plugin installed. 
You can check this by running:
```bash
docker compose build --help
```

If the output of the command includes the --ssh option, then the correct version of the plugin is installed.
```text
--ssh string     Set SSH authentications used when building service images. 
                           (use 'default' for using your default SSH Agent)

```
If the --ssh option is not present, you need to update the plugin. 
If the --ssh option did not appear after installing Compose along with Docker Desktop, 
manual installation may help (https://docs.docker.com/compose/install/linux/#install-the-plugin-manually).

## Setup

1. Clone the repository
2. Build the Docker image:
```bash
make build
```

## Usage

To run the project, use the following command:
```bash
make run-project
```
This command will start the application using Docker Compose, including any necessary dependencies.

Swagger documentation for implemented API is available at
```
http://127.0.0.1:8888/docs
```

## Development

### Running Checks
To use checks you need to install dependencies from dev-requirements.txt file by using:
```bash
pip install -r dev-requirements.txt
```

Before committing changes, you can run code checks and formatting using the following command:
```bash
make run-checks
```
This command will perform the following actions:
- Sort imports using `isort`
- Format code using `black` with a line length of 120 characters
- Check type annotations using `mypy`