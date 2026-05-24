# ID Generator Service - API Endpoints

This document describes all the Flask endpoints provided by the ID Generator service. The ID Generator is backed by PostgreSQL and provides a REST API for generating unique IDs organized by groups.

## API Endpoints

Base path: `/api`

### Generate ID
- **Route:** `POST /generate_id`
- **Description:** Generate a new unique ID for a specific group. IDs are auto-incremented within each group and persisted in PostgreSQL.
- **Request Body:**
  ```json
  {
    "group_name": "messages"
  }
  ```
- **Response (200):**
  ```json
  {
    "generated_id": <id_value>
  }
  ```
- **Response (400):** Missing `group_name` in request body
- **Example Request:**
  ```json
  {
    "group_name": "chat_messages"
  }
  ```
- **Example Response:**
  ```json
  {
    "generated_id": 1
  }
  ```

## ID Generation Details

- IDs are generated using a PostgreSQL-backed sequence mechanism
- Each `group_name` maintains its own independent ID sequence
- IDs are auto-incremented integers starting from 1
- The service initializes the database automatically on first use
- IDs are guaranteed to be unique within their group
