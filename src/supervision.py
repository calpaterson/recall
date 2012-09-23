import signal

def as_subprocess(logger):
    def stop(signal, unused_frame):
        logger.info("Got {signal}, stopping".format(signal=signal))
        exit(0)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
