# Coordinator Service - API Endpoints

This document describes all the Flask endpoints provided by the Coordinator service.

## Authentication Endpoints

Base path: `/auth`

### Register User
- **Route:** `POST /register`
- **Description:** Register a new user in the system
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
  }
  ```
- **Response (201):**
  ```json
  {
    "mensaje": "User registered",
    "id": <user_id>
  }
  ```
- **Response (400):** Missing required fields
- **Response (500):** User already registered or unexpected error

### Login
- **Route:** `POST /login`
- **Description:** Authenticate a user and receive a JWT token
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response (200):**
  ```json
  {
    "name": "John Doe",
    "id": <user_id>,
    "token": "<jwt_token>"
  }
  ```
- **Response (400):** Missing email or password
- **Response (401):** Invalid credentials

## Protected Endpoints

All protected endpoints require a valid JWT token in the request headers.

Base path: `/api`

### Join Server
- **Route:** `GET /join_server`
- **Protected:** Yes
- **Description:** Get the server assignment for the user to connect to (currently returns server 0)
- **Response (200):**
  ```json
  {
    "server": 0
  }
  ```

### Get Total Users
- **Route:** `GET /get_total_users`
- **Protected:** Yes
- **Description:** Get a list of all registered users in the system
- **Response (200):**
  ```json
  {
    "users": [<list_of_all_users>]
  }
  ```

### Subscribe to Direct Message Conversation
- **Route:** `POST /subscribe_dm`
- **Protected:** Yes
- **Description:** Subscribe the authenticated user to a direct message conversation with another user
- **Request Body:**
  ```json
  {
    "target_user_id": <target_user_id>
  }
  ```
- **Response (200):**
  ```json
  {
    "result": "user subscription is complete"
  }
  ```
- **Response (400):** Missing target_user_id

### Subscribe to Group Conversation
- **Route:** `POST /subscribe_group`
- **Protected:** Yes
- **Description:** Subscribe the authenticated user to a group conversation (Not implemented)
- **Response (501):** Not implemented

### Get Direct Message Messages
- **Route:** `GET /get_dm_messages`
- **Protected:** Yes
- **Description:** Get messages from a specific direct message conversation (Not implemented)
- **Response (501):** Not implemented

### Get Group Messages
- **Route:** `GET /get_group_messages`
- **Protected:** Yes
- **Description:** Get messages from a specific group conversation (Not implemented)
- **Response (501):** Not implemented

### Delete Chat
- **Route:** `POST /delete_chat`
- **Protected:** Yes
- **Description:** Delete a chat conversation (only the owner can delete) (Not implemented)
- **Response (501):** Not implemented
