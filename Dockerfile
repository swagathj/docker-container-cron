# Pulling ubuntu image with a specific tag from the docker hub.
FROM ubuntu:18.04

# Adding maintainer name (Optional).
MAINTAINER sjonnala@mathworks.com

# Updating the packages and installing cron and vim editor if you later want to edit your script from inside your container.
RUN apt-get update \
&& apt-get install cron -y && apt-get install vim -y && apt-get install iputils-ping -y && apt-get install python3-pip -y \
&& apt-get install rsync -y && apt-get install openssh-client -y

# Install logger module
RUN pip3 install logger

# Create the SSH Key
#RUN ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa

# Create directory under opt
RUN mkdir -p /opt/sync/bin/

# Copy the sbtools 10min script
COPY ./hub-sync-no-pull-SHARE_SBTOOLS.py /opt/sync/bin/

# Crontab file copied to cron.d directory.
COPY ./sbtools /etc/cron.d/

# Add ssh private key into container
ARG SSH_PRIVATE_KEY
RUN mkdir ~/.ssh/
RUN echo "${SSH_PRIVATE_KEY}" > ~/.ssh/id_rsa
RUN chmod 600 ~/.ssh/id_rsa
RUN ssh-keyscan batfs-hub11-bgl >> ~/.ssh/known_hosts

# Apply cron job
RUN crontab /etc/cron.d/sbtools

#Create a log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container setup
CMD cron && tail -f /var/log/cron.log

# Running commands for the startup of a container.
#CMD chmod 644 /etc/cron.d/sbtools && cron && tail -f /var/log/cron.log
