# Scalable Chat System Backend

This is an implementation for the excercise "CHAPTER 12: DESIGN A CHAT SYSTEM
" from the book "System Design Interview" from Alex Xu. T

The main idea of the task is to design a chat system backend that has the capacity of scale to handle millon of users. To reach that goal we use a distributed architecture from the begining of the design. The complex design is only worth in the case is used for that amount of users. 
Not only the complex design would be need in that case but also a cloud service to handle the servers and databases would be needed (AWS, Azure, GCP). Kubernetes could also be an option to manage the server instances in an aritrary amount of nodes, servers don't need to be physical can be containers. In this solution, as a first approach we just containerized the different instances with docker-compose.yml declarative style as we run in a single node, but it could be improved.

## Ideal design

The ideal design proposed was made with microservices as the following: a group of stateless coordinator servers interact with the users with HTTP. A load balancer distributes the load of users over the different servers interfaced as a service. This servers interact with other three services, a Login, a KV Store (For messages, connection and subscription information using a cache) and an Id generator (To generate messages ids with a relational database). Login, KV Store and Id Generator are decoupled from coordinator and chat servers, to ensure they could be scaled further (Althogh we didn't include it directly in this designu). Also we could also add deacoupled presence servers to handle users connection and disconnection lifecylces (We also didn't include it). Last but not least, we could add a message broker (such as redis) to handle the message queue between chat servers.

The criteria was so to divide the responsability in microservices to allow a scalable system. This complexity is only worth if the number of users is high enough otherwise the maintenance cost would be too high for the return.

![Texto alternativo](docs/assets/architecture1.svg)

## What we included in this design implementation

For this excercise we simplified the design to be able to complete it in just days of work. But it could be easily upgraded if necesary as it is built scalable. We used just one coordinator, one chat server, and the login system was mocked as a memory database without persistence. Also we didn't include persistence servers or group chats. We just made the system to be able for connected users to send DMs and subscribe to that DMs conversations. A method to ask for old conversations could be easily made to handle user syncronization with old messages.

![Texto alternativo](docs/assets/architecture2.svg)

## Implementation Details

The implementation is with python, using poetry and virtualenvs to handle the dependencies of each service deacoupled from each other. We use flask for the statless endpoints, and asyncio for councurrency (We avoid blocking while waiting for responses or database writes). 

The solution is just a backend, so we rely heavily on tests to verify the functionality. We used two kind of tests, unity tests and integration tests (Using pytest). The system could work with any front end that handle the protocol used in the integration tests. 

For ease of deployment we added containerization for KV Store and Id Generator. This modules also had dedicated python libraries, kv_store_lib and id_generator_lib and this we we separated the servers implementation from the database interface implementation. This interface separation allows us to divide the interface with the databases and the server implementation, which could be useful if we would need to implement distributed databases and service interface could diverge with the database interface. The libraries have unity tests to ensure correct functionality. The kv_store and id_generator have no tests as this is a simple example but it should have. Using libraries for spefic functionality that can be used project wide has the benefit that we can just easily downgrade the library version used in the service in case of unexpected upgrade bugs, and we also can experiment with the library without the need of upgrade it the main project right away.

The rest of the solution is a Coordinator and a Chat Server. (TODO: Add containerization for these services too). The coordinator has tests for the stateless part of its function, the Chat Server and Coordinator interaction over users usage are tested with integration tests. 

## Data Model

### Kv Store

TODO

### Id generator

TODO

## Proyect structure

We have all code in src folder. There is one folder for each service (chat_server, coordinator, id_generator, kv_store), plus, an integrated tests folder (That verify the interaction between clients and the services).
All other unity tests are in the test folder of each service/library. Each service/library has a pyproject.toml and poetry.lock with library requirements and exact library versions used. Dist folders contain the compiled library versions. When a library is compiled that file must be copied from the libs folder with the source code to the service folder that uses the library (In its dist folder).

```
/src
├── integrated_tests/
├── chat_server/
│   ├── pyproject.toml
│   ├── poetry.lock
│   ├── chat_server.py # Main file
│   └── utils/
├── coordinator/
│   ├── pyproject.toml
│   ├── poetry.lock
│   ├── coordinator.py # Main file
│   ├── tests/
│   ├── routes/
│   └── utils/
├── id_generator/
│    ├── pyproject.toml
│    ├── poetry.lock
│    ├── id_generator.py # Main file
│    ├── routes/
│    ├── dist/ # Compiled Id generator lib for the service
│    └── Dockerfile
├── kv_store/
│    ├── pyproject.toml
│    ├── poetry.lock
│    ├── kv_store.py # Main file
│    ├── routes/
│    ├── dist/ # Compiled Kv Store lib for the service
│    └── Dockerfile
├── libs/ # Project libraries used in dependencies
│    └── kv_store_lib/
│        ├── pyproject.toml
│        ├── poetry.lock
│        ├── kv_store_lib.py # Main file
│        ├── tests/
│        └── dist/
│    └── id_generator_lib/
│        ├── pyproject.toml
│        ├── poetry.lock
│        ├── id_generator_lib/ # Main lib module folder (Main file: __init__.py)
│        │   └── __init__.py
│        ├── tests/
│        └── dist/
├── docs/
└── docker-compose.yml # Docker compose for pg, redis database, kv_store and id_generator services
```

## Installation

You need to have poetry installed to test the modules separately in virtualenvs. It is recomended to also have pyenv so you can handle easily different instalations of python versions. You can run in Ubuntu, Windows with wsl or just powershell. It is tested with Windows with wsl.
To build the docker images and run in containers you need to install docker. The containerized version is perfect for a productive environment (as it descriptive design make easy to handle the infrastructure versioning and details), and could be further upgraded to multiple nodes using kubernetes (Which also would bring rebundance and scalability)


### Run project

To run the project in virtualenvs you need to execute this scripts in order

Important: Change .env_example files to .env before starting. There are two 'src/libs/id_generator_lib/.env_example' and '.env_example'. Also, in case you run services withot docker you need to bring up the database using the docker-compose_just_databases.yml. Rename it to 'docker-compose.yml' (Replace the full docker compose) and run 'docker compose up'.

#### Id generator
```bash
cd src/id_generator
python -m venv .venv
poetry install
start_id_generator localhost
```

#### Kv Store
```bash
python -m venv .venv
source .venv/bin/activate
poetry install
start_kv_store localhost 
```

#### Coordinator
```bash
python -m venv .venv
source .venv/bin/activate
poetry install
start_coordinator localhost
```

#### Chat Server
```bash
python -m venv .venv
source .venv/bin/activate
poetry install
start_chat_server 0
```

### Build libraries
Note: increase version number when upgrading the lib. (TODO: Handle lib versioning in a different repo).
Compiled libraries are already added to the services in the repo, this is only needed to compile a new lib version.

#### Kv Store Lib
```bash
cd src/libs/id_generator_lib
python -m venv .venv
source .venv/bin/activate
poetry build
cd ../../..
mv src/libs/id_generator_lib/dist/* src/id_generator/dist
```

#### Id generator Lib
```bash
cd src/libs/kv_store_lib
python -m venv .venv
source .venv/bin/activate
poetry build
cd ../../..
mv src/libs/kv_store_lib/dist/* src/kv_store_lib/dist
```

### Run Tests

#### Integration tests
This tests are important to verify the functionality of the whole system.  We add '-o log_cli=true --log-cli-level=INFO' to enable logging for further test debugging . The test are made incrementing the usage of the system in each one. This test driven development is perfect to design the system deacoupled from fronted (That is not included in this project).

```bash
pytest tests/test_messages.py -o log_cli=true --log-cli-level=INFO
```
Note: registration may fail is user already registered but it has no effect and do not make test to fail. TODO: Clean to make no registration if not needed, or to delete user after tests are finished.

There are three integration tests that are used:

- test_connect_and_disconnect
We test a client to connect to the coordinator, complete register and login, and then make it join the chat server with the same session. Then disconnect. 

- test_subscribe_to_conversation
We test a client to connect to the coordinator, complete register and login, make it join the chat server and then subscribe to a conversation of the same user (It would be the User-User chat). We verify subscription in the kv store database. Then we disconnect and verify unsubscription and user to be disconnected in kv store database.

- test_send_direct_message
We test a client to connect to the coordinator, complete register and login, make it join the chat server, subscribe to a conversation of the same user. We verify subscription and then send a message to the same user (User-User Chat). Then we verify the message is received (As we are subscribed to conversation) and its content

- test_send_peer_message
We test two clients to connect to coordinator, complete register and login. Then we make them join the chat server (and verify the stored kv store connection information) and subscribe to the conversation of these two users. We verify the users subscriptions in kv store database. After we wait for each user to complete the subscription (To avoid race conditions and guarantee sent messages are transmitted as both users are already subscribed) then we make them send a message to its dm channel, and verify the reception of the message of each one. We just log the message count, that should be n, n + 1. when n is the messages send before running the test. To make this test to work we had to make id generator able to handle concurrency of operations and guarantee a different id to be assigned to each message.

#### Unit Tests



```bash
pip install -r requirements.txt
```

## Ejecutar el servidor

```bash
python app.py
```

## Endpoints

### Públicos

| Método | Ruta             | Descripción         |
|--------|------------------|---------------------|
| GET    | `/`              | Health check        |
| POST   | `/auth/register` | Registrar usuario   |
| POST   | `/auth/login`    | Login → devuelve token |

### Protegidos (requieren `Authorization: Bearer <token>`)

| Método | Ruta          | Descripción              |
|--------|---------------|--------------------------|
| GET    | `/api/perfil` | Retorna datos del usuario |

## Ejemplo de uso

### Registrar usuario
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "1234"}'
```

### Login
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "1234"}'
```

### Usar ruta protegida
```bash
curl http://localhost:5000/api/perfil \
  -H "Authorization: Bearer <tu_token>"
```

## Kv Store library install

Build kv store library and copy to kv store service folder 

poetry build -P src/libs/kv_store_lib
mv src/libs/kv_store_lib/dist/* src/kv_store/dist
rm -d src/libs/kv_store_lib/dist

## Run KV Store

cd src/kv_store
python -m venv .venv
source .venv/bin/activate
poetry install
start_kv_store

## Id generator library install




## Run tests with info logs enabled
pytest tests -o log_cli=true --log-cli-level=INFO
## Logs command

pytest tests/test_messages.py::test_send_direct_message -o log_cli=true --log-cli-level=INFO