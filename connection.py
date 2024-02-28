from zk import ZK

def conectar(ip, port):
    zk = ZK(ip, port, timeout=5)
    try:
        print('Connecting to device ...')
        conn = zk.connect()
        print('Disabling device ...')
        conn.disable_device()
        conn.test_voice(index=10)
    except Exception as e:
        print(f'Process terminate : ', {e})
    finally:
        return conn