# KV Store Service - API Endpoints

This document describes all the Flask endpoints provided by the KV Store (Key-Value Store) service. The KV Store is backed by Redis and provides a REST API for storing and retrieving data.

## API Endpoints

Base path: `/api`

### Set Key-Value Pair
- **Route:** `POST /set`
- **Description:** Store a key-value pair in the Redis store
- **Request Body:**
  ```json
  {
    "key": "my_key",
    "value": "my_value"
  }
  ```
- **Response (200):**
  ```json
  {
    "status": "Data written"
  }
  ```
- **Response (400):** Missing or null value

### Get Value by Key
- **Route:** `GET /get`
- **Description:** Retrieve a value from the store by its key
- **Query Parameters:**
  - `key` (required): The key to retrieve
- **Example:** `GET /api/get?key=my_key`
- **Response (200):**
  ```json
  {
    "value": "my_value"
  }
  ```

### Delete Key
- **Route:** `POST /delete`
- **Description:** Delete a key-value pair from the store
- **Request Body:**
  ```json
  {
    "key": "my_key"
  }
  ```
- **Response (200):**
  ```json
  {
    "status": "Data deleted"
  }
  ```

### Get All Keys with Prefix
- **Route:** `GET /get_all_with_prefix`
- **Description:** Retrieve all key-value pairs that start with a specific prefix
- **Query Parameters:**
  - `prefix` (required): The prefix to search for
- **Example:** `GET /api/get_all_with_prefix?prefix=user>`
- **Response (200):**
  ```json
  {
    "value": {
      "key1": "value1",
      "key2": "value2",
      ...
    }
  }
  ```

### Delete All Keys with Suffix
- **Route:** `POST /delete_all_with_suffix`
- **Description:** Delete all keys that end with a specific suffix
- **Request Body:**
  ```json
  {
    "suffix": "my_suffix"
  }
  ```
- **Response (200):**
  ```json
  {
    "status": "Data deleted"
  }
  ```
- **Response (400):** Missing suffix in request

### Delete All Keys with Prefix and Suffix
- **Route:** `POST /delete_all_with_prefix_and_suffix`
- **Description:** Delete all keys that start with a specific prefix and end with a specific suffix
- **Request Body:**
  ```json
  {
    "prefix": "my_prefix",
    "suffix": "my_suffix"
  }
  ```
- **Response (200):**
  ```json
  {
    "status": "Data deleted"
  }
  ```
- **Response (400):** Missing prefix or suffix in request

## Key Format Convention

The KV Store uses a delimiter-based key naming convention with `>` as the separator:
- `userver>user_id>session_token` - Maps users to their assigned chat server
- `usubscription>message_group>server_id>user_id>session_token` - Stores user subscriptions to message groups
- `dm<min_user_id<max_user_id` - Direct message group identifiers
