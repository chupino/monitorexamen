rm -rf monitor
docker rm -f $(docker ps -lq)
docker rmi -f monitor
