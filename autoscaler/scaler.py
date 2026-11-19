import os
import time
import docker
import psycopg2


CHECK_INTERVAL_SEC = 3
IDLE_TIMEOUT_SEC = 20
EXTRA_SERVER_IDS = ["app3", "app4"]  # Максимум 2 додаткові сервери (разом до 4)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "dbname": os.environ.get("DB_NAME", "jacobi_db"),
    "user": os.environ.get("DB_USER", "jacobi_user"),
    "password": os.environ.get("DB_PASSWORD", "jacobi_pass"),
    "port": int(os.environ.get("DB_PORT", 5432)),
}

client = docker.from_env()
idle_since = {}


def get_base_app_config():
    for c in client.containers.list():
        if "app1" in c.name:
            image = c.image.tags[0] if c.image.tags else c.image.id
            networks = list(c.attrs["NetworkSettings"]["Networks"].keys())
            network = networks[0] if networks else None
            return image, network
    return None, None


def get_db_state():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM solver_computetask WHERE status = 'queued';")
            queued_count = cur.fetchone()[0]

            cur.execute("SELECT server_id, active_tasks FROM solver_servernode;")
            nodes = {row[0]: row[1] for row in cur.fetchall()}
        return queued_count, nodes
    finally:
        conn.close()


def mark_node_offline(server_id):
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE solver_servernode SET is_online = FALSE, active_tasks = 0 WHERE server_id = %s;",
                (server_id,),
            )
        conn.commit()
    finally:
        conn.close()


def get_running_extra_containers():
    result = {}
    for sid in EXTRA_SERVER_IDS:
        name = f"jacobi_{sid}"
        try:
            c = client.containers.get(name)
            if c.status == "running":
                result[sid] = c
            else:
                c.remove(force=True)
        except docker.errors.NotFound:
            pass
    return result


def spawn_server(server_id, image, network):
    name = f"jacobi_{server_id}"
    print(f"[autoscaler] Черга заповнена — запускаю {name}...")
    client.containers.run(
        image=image,
        name=name,
        detach=True,
        network=network,
        environment={
            "SERVER_ID": server_id,
            "MAX_SLOTS": "2",
            "DB_HOST": DB_CONFIG["host"],
            "DB_NAME": DB_CONFIG["dbname"],
            "DB_USER": DB_CONFIG["user"],
            "DB_PASSWORD": DB_CONFIG["password"],
        },
    )
    idle_since.pop(server_id, None)


def main():
    print("[autoscaler] Старт моніторингу черги...")
    while True:
        try:
            image, network = get_base_app_config()
            if not image or not network:
                print("[autoscaler] Чекаю на запуск app1...")
                time.sleep(CHECK_INTERVAL_SEC)
                continue

            queued_count, nodes = get_db_state()
            running_extra = get_running_extra_containers()
            now = time.time()


            if queued_count >= 1:
                for sid in EXTRA_SERVER_IDS:
                    if sid not in running_extra:
                        spawn_server(sid, image, network)
                        break


            for sid, container in list(running_extra.items()):
                active = nodes.get(sid, 0)
                if queued_count == 0 and active == 0:
                    if sid not in idle_since:
                        idle_since[sid] = now
                    elif now - idle_since[sid] >= IDLE_TIMEOUT_SEC:
                        print(f"[autoscaler] Простій {sid} > {IDLE_TIMEOUT_SEC}с — видаляю...")
                        container.stop(timeout=5)
                        container.remove(force=True)
                        mark_node_offline(sid)
                        idle_since.pop(sid, None)
                else:
                    idle_since.pop(sid, None)

        except Exception as e:
            print(f"[autoscaler] Помилка: {e}")

        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == "__main__":
    main()