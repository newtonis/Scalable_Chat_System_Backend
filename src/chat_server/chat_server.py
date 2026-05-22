import asyncio
import websockets
import json
from utils.jwt_helper import get_user_data_from_path
from urllib.parse import urlparse
import argparse
from utils import constants
import httpx
import logging


class Client:
    def __init__(self, client_id, token, websocket, message_queue, client_addr):
        self.client_id = client_id
        self.token = token
        self.websocket = websocket
        self.message_queue = message_queue
        self.client_addr = client_addr


# Set of connected clients
clients = {}
sessions_by_client_id = {}


async def MessageConsumer(token, queue, client):
    logging.info(f"Consumer started for {token}")
    while True:
        item = await queue.get()
        
        if item:
            logging.info(f"Processing message: {item}")
            await client.websocket.send(json.dumps({
                "command": "new_message",
                "message": item
            }))
            
            logging.info(f"Message processed")
        else:
            logging.info(f"Last item")

        # We send the queue a message the task is completed
        queue.task_done()


# handler is called for each new connection
async def handler(websocket, server_id):
    logging.info(f"[+] Connected client: {websocket.remote_address} — Total: {len(clients)}")
        
    path = websocket.request.path

    status, payload = get_user_data_from_path(path)
    if status == 0:
        # Invalid token, abort connection
        logging.info(f"[e] Token: {payload['error']}")
        return 0

    user_id = payload["user_id"]
    session_token = payload["token"]
    
    logging.info(f"[+] Client authenticated")

    # Register user connection as connected in the corresponding selected server
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{constants.KV_STORE_URL}/api/set", 
            json=
            {
                "key": f"userver>{user_id}>{session_token}",
                "value": server_id
            }
        )

    message_queue = asyncio.Queue()
    # Token is valid, continue connection, wait for messages
    clients[session_token] = Client(
        user_id, 
        session_token,
        websocket, 
        message_queue,
        websocket.remote_address
    ) 
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
                message_value = data.get("message") # Get the message content
                message_type = data.get("type") # If the message is from a group chat or individual conversation
                message_recv_id = data.get("user_id") # Get the target user for the message
                
                if message_type == "dm":
                    # Handle direct message
                    logging.info("Sending direct message ...")
                    message_group_name = "dm" + "<" + str(min(user_id, message_recv_id)) + "<" + str(max(user_id, message_recv_id))

                    # Generate message id
                    async with httpx.AsyncClient() as client:
                        res = await client.post(
                            f"{constants.ID_GENERATOR_URL}/api/generate_id", 
                            json=
                            {
                                "group_name": message_group_name
                            }
                        )
                    ## TODO: handle transaction failure (retries or respond error message in case of failure)

                    message_number = res.json()["generated_id"]["result"]
                    message_group = f"dm_message>{message_group_name}>{message_number}"
                    msg_value = {
                        "key": message_group,
                        "value": message_value
                    }
                    # Persist message in KV Store
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{constants.KV_STORE_URL}/api/set", 
                            json=msg_value
                        )

                    # Subsription format {message_group}>{server_id}>{user_id}>{session_token}

                    # Check group subscription users in this server
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{constants.KV_STORE_URL}/api/get_all_with_prefix?prefix=usubscription>server_{message_group_name}>{server_id}"
                        )
                    data = response.json()

                    for key in data["value"]:
                        _, _, _, user_id, user_token = key.split(">")
                        data = response.json()
                        if user_token not in clients:
                            logging.info(f"Subscribed client is not connected to server (Client disconnected without unsubscription or client subscribed and did not connect)")
                        else:
                            await clients[user_token].message_queue.put({
                                "from": user_id
                                ,"message": msg_value # Message value
                                ,"number": message_number
                                ,"group": message_group
                            })

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
        # Wait for the connection event queue to end
        await message_queue.put(None)
        await message_queue.join()
        await task_consumer
        
        clients.pop(session_token)
        sessions_by_client_id[user_id].remove(session_token)
        if len(sessions_by_client_id[user_id]) == 0:
            sessions_by_client_id.pop(user_id)
        logging.info(f"    Clientes restantes: {len(clients)}")


async def main(server_id):
    server_url = constants.CHAT_SERVERS_URL[server_id]

    host = urlparse(server_url).hostname
    port = urlparse(server_url).port

    logging.info(f"WebSocket running on ws://{host}:{port}")
    logging.info(f"Waiting for connections conexiones... (Ctrl+C to stop)\n")

    # Handler with server id variable embeeded
    async def handler_with_server_id(websocket):
        await handler(websocket, server_id)

    async with websockets.serve(handler_with_server_id, host, port):
        await asyncio.Future() # Run indefinitely


def start_chat_server():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"  # Clean disign for console
    )
    
    parser = argparse.ArgumentParser(description="Chat Server")
    parser.add_argument("server_id", type=int, help="Port to Run Server")

    args = parser.parse_args()
    
    asyncio.run(main(args.server_id))

start_chat_server()