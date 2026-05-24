import argparse
import asyncio
import json
import logging

import httpx
import websockets
from utils import constants
from utils.jwt_helper import get_user_data_from_path


class Client:
    def __init__(self, client_id, token, websocket, message_queue, client_addr):
        self.client_id = client_id
        self.token = token
        self.websocket = websocket
        self.message_queue = message_queue
        self.client_addr = client_addr


class ServerContext:
    def __init__(self, server_id, kv_store_url, id_generator_url):
        self.server_id = server_id
        self.kv_store_url = kv_store_url
        self.id_generator_url = id_generator_url


# Set of connected clients
clients = {}
sessions_by_client_id = {}


async def MessageConsumer(token, queue, client):
    logging.info(f"Consumer started for {token}")
    while True:
        item = await queue.get()

        if item:
            logging.info(f"Processing message: {item}")
            await client.websocket.send(json.dumps({"command": "new_message", "message": item}))

            logging.info("Message processed")
        else:
            logging.info("Last item")

        # We send the queue a message the task is completed
        queue.task_done()


def validate_msg_package(data):
    if "message" not in data:
        return False
    if "value" not in data["message"]:
        return False
    if "user_id" not in data["message"]:
        return False
    if "type" not in data["message"]:
        return False

    return True


# handler is called for each new connection
async def handler(websocket, server_context):
    logging.info(f"[+] Connected client: {websocket.remote_address} — Total: {len(clients)}")

    path = websocket.request.path

    status, payload = get_user_data_from_path(path)
    if status == 0:
        # Invalid token, abort connection
        logging.info(f"[e] Token: {payload['error']}")
        return 0

    user_id = int(payload["user_id"])
    session_token = payload["token"]

    logging.info("[+] Client authenticated")

    # Register user connection as connected in the corresponding selected server
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{server_context.kv_store_url}/api/set",
            json={
                "key": f"userver>{user_id}>{session_token}",
                "value": server_context.server_id,
            },
        )

    message_queue = asyncio.Queue()
    # Token is valid, continue connection, wait for messages
    clients[session_token] = Client(user_id, session_token, websocket, message_queue, websocket.remote_address)
    # Add a new token for the client connection
    if user_id in sessions_by_client_id:
        sessions_by_client_id[user_id].add(session_token)
    else:
        sessions_by_client_id[user_id] = {session_token}

    # Create a message consumer for the client
    task_consumer = asyncio.create_task(MessageConsumer(session_token, message_queue, clients[session_token]))

    try:
        async for message in websocket:
            logging.info(f"[{websocket.remote_address}] New message: {message}")

            # Parse message
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                logging.info(f"[-] Invalid Package: {message} from {websocket.remote_address}")

            command = data.get("command")

            # New message
            if data.get("command") == "dummy":
                # Respond to test dummy message
                logging.info(f"Respond dummy menssage to {websocket.remote_address}")
                await websocket.send(json.dumps({"command": "dummy", "value": "dummy answer"}))
            elif command == "new_message":
                if not validate_msg_package(data):
                    # TODO: Handle to ask for resend
                    logging.info(
                        f"Invalid msg received (no message or incomplete message information): {data}. No Action"
                    )
                else:
                    message_value = data["message"]["value"]  # Get the message content
                    message_type = data["message"][
                        "type"
                    ]  # If the message is from a group chat or individual conversation
                    message_recv_id = int(data["message"]["user_id"])  # Get the target user for the message

                    if message_type == "dm":
                        # Handle direct message
                        logging.info("Sending direct message ...")
                        message_group_name = (
                            "dm" + "<" + str(min(user_id, message_recv_id)) + "<" + str(max(user_id, message_recv_id))
                        )
                        logging.info(message_group_name)

                        # Generate message id
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            res = await client.post(
                                f"{server_context.id_generator_url}/api/generate_id",
                                json={"group_name": message_group_name},
                                headers={
                                    "Cache-Control": "no-cache, no-store, must-revalidate",
                                    "Pragma": "no-cache",
                                },
                            )
                        ## TODO: handle transaction failure (retries or respond error message in case of failure)

                        message_number = res.json()["generated_id"]["result"]
                        message_group = f"dm_message>{message_group_name}>{message_number}"
                        msg_value = {"key": message_group, "value": message_value}
                        # Persist message in KV Store
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            await client.post(f"{server_context.kv_store_url}/api/set", json=msg_value)

                        # Subsription format {message_group}>{server_id}>{user_id}>{session_token}

                        # Check group subscription users in this server
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.get(
                                f"{server_context.kv_store_url}/api/get_all_with_prefix?prefix=usubscription>{message_group_name}>{server_context.server_id}"
                            )
                        data_subscriptions = response.json()

                        for key in data_subscriptions["value"]:
                            _, _, _, to_id, user_token = key.split(">")
                            data = response.json()
                            if user_token not in clients:
                                logging.info(
                                    "Subscribed client is not connected to server (Client disconnected without unsubscription or client subscribed and did not connect)"
                                )
                            else:
                                await clients[user_token].message_queue.put(
                                    {
                                        "type": "dm",
                                        "group": message_group_name,
                                        "user_id": user_id,
                                        "value": message_value,
                                        "id": message_number,
                                    }
                                )

                    # TODO: Search if the client is connected in other servers and send to corresponding client queues in that servers. (Check subscription in other servers)

            # # Respuesta al remitente
            # respuesta = {
            #     "tipo": "respuesta",
            #     "mensaje": f"Recibido: {data.get('texto', message)}",
            #     "timestamp": datetime.now().isoformat(),
            #     "clientes_conectados": len(clients),
            # }
            # await websocket.send(json.dumps(respuesta))

            # # Broadcast a todos los demás clientes
            # broadcast = {
            #     "tipo": "broadcast",
            #     "de": str(client_addr),
            #     "mensaje": data.get("texto", message),
            #     "timestamp": datetime.now().isoformat(),
            # }
            # otros = clients - {websocket}
            # if otros:
            #     await asyncio.gather(*[c.send(json.dumps(broadcast)) for c in otros])

    except websockets.exceptions.ConnectionClosedOK:
        logging.info(f"[-] Cliente desconectado limpiamente: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        logging.info(f"[-] Cliente desconectado con error: {websocket.remote_address} — {e}")
    finally:
        # Register user disconnection in the corresponding selected server
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{server_context.kv_store_url}/api/delete",
                json={"key": f"userver>{user_id}>{session_token}"},
            )

        # Unsubscribe this user connection from all chat subscriptions (That will be of this server)
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{server_context.kv_store_url}/api/delete_all_with_prefix_and_suffix",
                json={"prefix": "usubscription>", "suffix": f">{session_token}"},
            )

        # Wait for the connection event queue to end
        await message_queue.put(None)
        await message_queue.join()
        task_consumer.cancel()

        clients.pop(session_token)
        sessions_by_client_id[user_id].remove(session_token)
        if len(sessions_by_client_id[user_id]) == 0:
            sessions_by_client_id.pop(user_id)
        logging.info(f"    Clientes restantes: {len(clients)}")


async def main(server_id, kv_store_host, id_generator_host):
    port = constants.CHAT_SERVERS_PORTS[server_id]

    logging.info(f"WebSocket running on ws://0.0.0.0:{port}")
    logging.info("Waiting for connections ... (Ctrl+C to stop)\n")

    # Handler with context variables embeeded
    async def handler_with_context(websocket):
        await handler(
            websocket,
            ServerContext(
                server_id,
                constants.KV_STORE_URL.format(host=kv_store_host),
                constants.ID_GENERATOR_URL.format(host=id_generator_host),
            ),
        )

    async with websockets.serve(handler_with_context, "0.0.0.0", port):
        await asyncio.Future()  # Run indefinitely


def start_chat_server():
    parser = argparse.ArgumentParser(description="Chat Server Api")
    parser.add_argument("server_id", type=int, help="Server id")
    parser.add_argument("kv_store_host", type=str, help="Kv store host", default="localhost")
    parser.add_argument("id_generator_host", type=str, help="Id generator host", default="localhost")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",  # Clean disign for console
    )

    asyncio.run(main(args.server_id, args.kv_store_host, args.id_generator_host))


start_chat_server()
