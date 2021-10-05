#!/usr/bin/python -u

import sys
import os
import glob
import re
import subprocess
import traceback
import optparse
import logging
import time
import socket
import threading
import queue
import logging
import logger
from logging.handlers import TimedRotatingFileHandler


#
# TODO: make pushes smart and no push if pull sees no changes (check rsync output)
#

verbose=0

rsync_opts="--stats -avHSgp --exclude=.snapshot/ --exclude=.nfs --exclude=.rsync --delete-delay --numeric-ids --exclude=release/ --exclude=external-apps/ --exclude=.last_changed_build_id.external-apps --exclude=.last_changed_build_id.release"

# removing bw limits for push
#rsync_remote_opts=" --bwlimit=20000 "
rsync_remote_opts=""

syncareas=["share/sbtools"]

push_servers=["batfs-hub11-bgl"]

# increasing num workers to 2 times the sync systems because of 10Gb LS links
NUM_WORKERS=2*len(push_servers)

queue = queue.Queue()

path = "/var/log/rsync/hub/individual/"


def get_logger():

    if not os.path.exists(path):
        cmd = "mkdir -p {}".format(path)
        ret = subprocess.call(cmd.split())

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger("SBtols hub replication")
    logger.setLevel(logging.INFO)
    handler = TimedRotatingFileHandler(path + 'hub_SBtools_replication.log',
                                       when="d", interval=1, backupCount=20)
    handler.setFormatter(formatter)
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(handler)
    logger.info('***********replication Starts ********************')
    return logger


def run_cmd(cmd):
    """[Execute the shell command using subprocess]

    Args:
        cmd ([str]): [command]
    """
    subprocess.getoutput(cmd)


#########################################################################
### No longer used because this script is now running from the source filer batfs0391
def pull_area(area):

    logger = logging.getLogger("SBtols hub replication")
    logfile="/var/log/rsync/hub/individual/%s.rsync.%s" % (area,time.strftime("%Y%m%d_%H:%M:%S_%Z"))

    # trigger the mount
    pwd=os.getcwd()
    os.chdir("/mathworks/BGL/hub/%s/" % area)
    os.chdir(pwd)

    st=time.time()
    rsync_cmd = "rsync %s --log-file=%s /mathworks/BGL/hub/%s/ /vmgr/hub/hub_%s/%s/" % (rsync_opts,logfile,area,area,area)
    out = subprocess.getoutput(rsync_cmd)
    logger.info("Pull of %s elapsed time: %d" %(area, int(time.time(-st))))

    # TODO: problems where changes in links cause 0 transferred so
    #  need to be clever and check line counts or output to determine if changes occured
    #if re.search("Number of files transferred: 0",out,re.MULTILINE):
    #    return False

    return True

#########################################################################

class push_queue(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        logger = logging.getLogger("SBtols hub replication")
        while True:
            try:
                rsync_args = self.queue.get()
                if rsync_args is None:
                   break # end of queue
                st=time.time()
                run_cmd("rsync %s %s %s" % (rsync_opts,rsync_remote_opts,rsync_args))
                logger.info("RSYNC: %s %s %s" % (rsync_opts,rsync_remote_opts,rsync_args))
                logger.info("push to %s elapsed time: %d " % (rsync_args.split()[-1], int(time.time()-st)))
                self.queue.task_done()
            except:
                return


if __name__ == '__main__':

    # redirect output to log area
    # sys.stdout = open("/var/log/rsync/hub/hub-sync-share-sbtools.%s.log" % time.strftime("%Y-%m-%d"),"a+")
    # sys.stderr = sys.stdout
    logger = get_logger()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SBtols hub replication")

    start_time=time.time()
    logger.info("Push Start Time: %s" % time.ctime(start_time))


    # spawn a pool of threads to do the push work
    for i in range(NUM_WORKERS):
        push_queue(queue).start()

    for area in syncareas:

        #batchfile="/var/tmp/%s.batch.%s" % (area,time.strftime("%Y%m%d_%H:%M:%S_%Z"))
        #print "Pulling %s" % area
        #if pull_area(area):

        srcarea="/vmgr/hub/hub_%s/%s/" % (area.split("/")[0],area.split("/")[1])
        print(srcarea)
        destarea="/vmgr/hub/hub_%s/%s/" % (area.split("/")[0],area.split("/")[1])
        logger.info("Pushing %s to %s " %(area, push_servers))

        for server in push_servers:
            logfile="/var/log/rsync/hub/individual/%s.%s.push_rsync.%s" % (server,area.replace("/","-"),time.strftime("%Y%m%d_%H_%M_%S_%Z"))
            queue.put("--log-file=%s %s %s:%s" % (logfile,srcarea,server,destarea))

    #pull_end_time=time.time()
    #print "Pull Finished: %s, elapsed secs=%d" % (time.ctime(pull_end_time),int(pull_end_time-start_time))

    queue.join()
    push_end_time=time.time()
    logger.info("Push Finish TIME: %s - elapsed secs=%d" % (time.ctime(push_end_time),int(push_end_time-start_time)))

    # close out the queues
    for i in range(NUM_WORKERS):
        queue.put(None)
