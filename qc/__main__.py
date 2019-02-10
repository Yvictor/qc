import os
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import datetime as dt
import ujson
import redis
import pytz
from pysolace import solclient
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DBN = int(os.environ.get('REDIS_DBN', 0))
ARDB_HOST = os.environ.get('ARDB_HOST', 'localhost')
ARDB_PORT = int(os.environ.get('ARDB_PORT', 16379))
ARDB_DBN = int(os.environ.get('ARDB_DBN', 0))
SOL_HOST = os.environ.get('SOL_HOST', 'localhost')
SOL_VPN = os.environ.get('SOL_VPN', '')
SOL_USER = os.environ.get('SOL_USER', '')
SOL_PWD = os.environ.get('SOL_PWD', '')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.environ.get('LOG_FILE', 'qc.log')

allow_log_level = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
assert LOG_LEVEL in allow_log_level, "LOG_LEVEL not allow, choice {}".format(
    (', ').join(allow_log_level))
LOGGING_LEVEL = getattr(logging, LOG_LEVEL)
log = logging.getLogger('qc')
log.setLevel(LOGGING_LEVEL)
console_handler = TimedRotatingFileHandler(LOG_FILE, when='D', interval=1, backupCount=10)
console_handler.setLevel(LOGGING_LEVEL)
log_formatter = logging.Formatter(
    '[%(levelname)1.1s %(asctime)s %(pathname)s:%(lineno)4d:%(funcName)s] %(message)s'
)
console_handler.setFormatter(log_formatter)
log.addHandler(console_handler)


redis_cache = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DBN)
ardb = redis.Redis(ARDB_HOST, ARDB_PORT, ARDB_DBN)

def called_by_c(topic, json_string):
    recv_t = str(dt.datetime.now())
    parsed = ujson.loads(json_string)
    parsed['t'] = str(dt.datetime.now())#time.time()
    parsed['recv_t'] = recv_t
    redis_cache.rpush(topic, ujson.dumps(parsed))
    return 0

solclient.set_callback(called_by_c)
sol = solclient.connect(SOL_HOST, SOL_VPN, SOL_USER, SOL_PWD)
solclient.subscribe(sol, "MKT/*/*/*")
solclient.subscribe(sol, "QUT/*/*/*")

solclient.subscribe(sol, "L/*/*")
solclient.subscribe(sol, "Q/*/*") 


def redis2ardb():
    rs_keys = redis_cache.keys()
    key_n = len(rs_keys)
    init_time = time.time()
    for i, k in enumerate(rs_keys):
        log.info('KEY: {}, {}/{} [{:.2f}]%'.format(k, i+1, key_n, ((i+1)/key_n)*100))
        start_time = time.time()
        l_content = redis_cache.lrange(k, 0, -1)
        log.info('KEY: {}, LENG: {}'.format(k, len(l_content)))
        old_ardb_len = ardb.llen(k)
        ardb.rpush(k, *l_content)
        log.info('KEY: {}, LENG: {}, ARDB PUSH DONE.'.format(k, ardb.llen(k)-old_ardb_len))
        redis_cache.ltrim(k, len(l_content), -1)
        log.info('KEY: {}, LENG: {}, REDIS TRIMED.'.format(k, redis_cache.llen(k)))
        if not redis_cache.lrange(k, 0, -1):
            redis_cache.delete(k)
            log.info('KEY: {}, EMPTY DELETED'.format(k))
        end_time = time.time()
        log.info('KEY: {}, SPEND: {:.6f}s'.format(k, end_time-start_time))
        log.info('TOTAL SPEND: {}'.format(dt.datetime.fromtimestamp(end_time)-dt.datetime.fromtimestamp(init_time)))

jobstores = {
    'default': MemoryJobStore()
}
executors = {
    'default': ThreadPoolExecutor(4),
    'processpool': ProcessPoolExecutor(2)
}
scheduler = BlockingScheduler(jobstores=jobstores, executors=executors, timezone=pytz.timezone('Asia/Taipei'))

scheduler.add_job(redis2ardb, trigger='cron', hour='5', minute='2', id='redis2ardb')
scheduler.start()