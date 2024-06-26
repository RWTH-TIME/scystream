The scystream project is an open-source data-science pipeline toolkit containing all necessary tools to create and carry our data-science workflows.
With an easy to use frontend, you can schedule and deploy custom workflows containing different data processing tasks.

## Architecture

![.assets/arch.png](.assets/arch.png)

## quickstart

Its recommended to use [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/)

### Docker

To setup all services just run the following command in the root directory

```sh
docker compose up -d
```

This will setup these containers:

| container         | port |
|-------------------|------|
| frontend          | 8000 |
| core              | 4000 |
| core-postgres     | 5433 |
| spark-worker      |      |
| spark-master      | 8080 |
| airflow-webserver | 3333 |
| airflow-cli       |      |
| airflow-triggerer |      |
| airflow-worker    |      |
| airflow-scheduler |      |
| postgres-airflow  |      |
| redis-airflow     |      |

## Development

You can find the development READMEs in the according directories

