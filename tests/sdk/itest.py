import os
import time

from notification_service.embedded_notification_client import EmbeddedNotificationClient
from notification_service.event_storage import DbEventStorage
from notification_service.server import NotificationServer
from notification_service.service import NotificationService
from notification_service.util import db

from ai_flow.rpc.server.server import AIFlowServer


if __name__ == '__main__':

    def wait_for_ns_started(server_uri):
        last_exception = None
        for i in range(60):
            try:
                return EmbeddedNotificationClient(server_uri=server_uri, namespace='default', sender='sender')
            except Exception as e:
                time.sleep(2)
                last_exception = e
        raise Exception("The server %s is unavailable." % server_uri) from last_exception

    if os.path.exists('/Users/alibaba/notification_service/notification_service.db'):
        os.remove('/Users/alibaba/notification_service/notification_service.db')

    db.create_all_tables('sqlite:////Users/alibaba/notification_service/notification_service.db')
    db_conn = "sqlite:////Users/alibaba/notification_service/notification_service.db"
    storage = DbEventStorage(db_conn)
    master = NotificationServer(NotificationService(storage), port='50052')
    master.run()
    wait_for_ns_started("localhost:50052")

    server = AIFlowServer()
    server.run(is_block=True)
