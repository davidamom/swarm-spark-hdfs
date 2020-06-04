# swarm-spark
Elastic Apache Spark and HDFS environment running on Docker Swarm Orchestrator to handle raster data


# Running Hadoop and Spark in Docker Swarm cluster
# Initial setup

## Setup a swarm cluster

First of all, you must start a Swarm cluster so that we can deploy services defined in docker-compose.

Initiate swarm cluster:

```
docker swarm init
```


## Deploy services

Deploy services with the CLI bellow (`hdfs` as the stack name, you can choose whatever name you want):
```
docker stack deploy -c ./docker-compose.yml hdfs
```
