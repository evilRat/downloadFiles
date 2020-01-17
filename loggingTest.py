import logging
logging.basicConfig(level=logging.DEBUG,format ='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler("test.log")
handler.setFormatter(logFormatter)
console = logging.StreamHandler()
console.setFormatter(logFormatter)
logger.addHandler(handler)
logger.addHandler(console)



logger.info("fuck info")
logger.warning("fuck warning")
logger.debug("fuck debug")
logger.error("fuck error")