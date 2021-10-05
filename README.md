# docker-container-cron
Creating the docker container with cron enabled

# To build the docker image 

docker build --build-arg SSH_PRIVATE_KEY="$(cat ~/.ssh/id_rsa)" -t hub_share-sbtools/crontab .

# To run the docker containter

docker run -itd -v /vmgr/hub/hub_share/sbtools/:/vmgr/hub/hub_share/sbtools/ --name hub-sbtools-bgl hub_share-sbtools/crontab:latest
