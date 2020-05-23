# 1 输出loss曲线
# 2 将记忆里的轨迹重新学习
from matplotlib import pyplot as plt 
import torch
import numpy as np
import hfo
import math
import logging, random
import datetime
from pathlib import Path

class MyFormatter(logging.Formatter):
    converter=datetime.datetime.fromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s

def set_log_files(savePath):
    print("set logger")
    logging.getLogger().handlers = []

    logging.getLogger().setLevel(logging.INFO)

    #logging.addLevelName(15, 'verbose')

    #logging.getLogger().setLevel(logging.DEBUG)

    #logging.basicConfig(level=getattr(logging, 'DEBUG')) #FLAGS.loglevel.upper()))

    debug_fh = logging.FileHandler(savePath + ('_ddpg.DEBUG'))
    info_fh = logging.FileHandler( savePath + ('_ddpg.INFO'))
    warning_fh = logging.FileHandler(savePath + ('_ddpg.WARNING'))
    error_fh = logging.FileHandler(savePath + ('_ddpg.ERROR'))
    critical_fh = logging.FileHandler(savePath + ('_ddpg.CRITICAL'))

    console = logging.StreamHandler()
    # info_ch = logging.StreamHandler()
    # warning_ch = logging.StreamHandler()
    # error_ch = logging.StreamHandler()
    # fatal_ch = logging.StreamHandler()

    #logging.getLogger().setLevel(level=getattr(logging, FLAGS.loglevel.upper())) # logging.DEBUG)
    console.setLevel(getattr(logging, "INFO"))

    debug_fh.setLevel(logging.DEBUG)
    info_fh.setLevel(logging.INFO)
    warning_fh.setLevel(logging.WARNING)
    error_fh.setLevel(logging.ERROR)
    critical_fh.setLevel(logging.CRITICAL)


    #console.setLevel(level=getattr(logging, FLAGS.loglevel.upper())) # logging.DEBUG)
    # info_ch.setLevel(logging.INFO)
    # warning_ch.setLevel(logging.WARNING)
    # error_ch.setLevel(logging.ERROR)
    # fatal_ch.setLevel(logging.FATAL)

    formatter = MyFormatter('%(asctime)s: %(levelname).1s %(module)s:%(lineno)d] %(message)s', '%Y-%m-%d %H:%M:%S.%f')

    console.setFormatter(formatter)
    debug_fh.setFormatter(formatter)
    info_fh.setFormatter(formatter)
    warning_fh.setFormatter(formatter)
    error_fh.setFormatter(formatter)
    critical_fh.setFormatter(formatter)

    # if FLAGS.alsologtostderr:
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

    logging.getLogger().addHandler(debug_fh)
    logging.getLogger().addHandler(info_fh)
    logging.getLogger().addHandler(warning_fh)
    logging.getLogger().addHandler(error_fh)
    logging.getLogger().addHandler(critical_fh)

