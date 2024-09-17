# NightSky Backend API Documentation

## Overview

This document provides instructions for designing frontend functions in JavaScript to interact with the NightSky backend API. The backend is built using FastAPI and implements Server-Sent Events (SSE) for real-time updates.

## API Endpoints

### 1. Execute Graph

- Endpoint: POST `/execute/{chat_id}`
- Purpose: Starts the execution of the graph for a given chat ID.
- Request Body:
  {
    "initial_data": {
      // Your initial data object
    }
  }
- Response:
  {
    "message": "Graph execution started successfully"
  }

### 2. SSE Connection

- Endpoint: GET `/sse/{chat_id}`
- Purpose: Establishes a Server-Sent Events connection for real-time updates.

## Frontend Implementation Guidelines

### 1. Execute Graph Function

Create a function to initiate graph execution:

async function executeGraph(chatId, initialData) {
  const response = await fetch(`/execute/${chatId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ initial_data: initialData }),
  });

  if (!response.ok) {
    throw new Error('Failed to start graph execution');
  }

  const result = await response.json();
  console.log(result.message);
}

### 2. SSE Connection Function

Implement a function to establish and handle SSE connections:

function connectSSE(chatId) {
  const eventSource = new EventSource(`/sse/${chatId}`);

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleSSEUpdate(data);
  };

  eventSource.onerror = (error) => {
    console.error('SSE connection error:', error);
    eventSource.close();
  };

  return eventSource;
}

function handleSSEUpdate(data) {
  // Process the SSE update
  console.log('Received SSE update:', data);
  // Update UI or perform actions based on the received data
}

### 3. Managing Graph Execution

Create a function to manage the overall graph execution process:

async function manageGraphExecution(chatId, initialData) {
  try {
    // Start graph execution
    await executeGraph(chatId, initialData);

    // Establish SSE connection
    const eventSource = connectSSE(chatId);

    // Clean up function
    return () => {
      eventSource.close();
    };
  } catch (error) {
    console.error('Error managing graph execution:', error);
  }
}

### 4. UI Integration

Integrate these functions into your UI components:

// Example React component
function GraphExecutionComponent() {
  const [chatId, setChatId] = useState(null);

  useEffect(() => {
    if (chatId) {
      const initialData = {
        // Your initial data
      };
      const cleanup = manageGraphExecution(chatId, initialData);
      return cleanup;
    }
  }, [chatId]);

  const startExecution = () => {
    const newChatId = generateUniqueId(); // Implement this function
    setChatId(newChatId);
  };

  return (
    <div>
      <button onClick={startExecution}>Start Graph Execution</button>
      {/* Other UI elements */}
    </div>
  );
}

## Important Notes

1. Error Handling: Implement robust error handling for both API calls and SSE connections.
2. State Management: Consider using a state management solution (e.g., Redux) for complex applications.
3. Reconnection Logic: Implement reconnection logic for SSE in case of connection loss.
4. Security: Ensure proper authentication and authorization mechanisms are in place.
5. Testing: Create unit and integration tests for these functions.

## Conclusion

This documentation provides a foundation for implementing frontend functions to interact with the NightSky backend. Adapt these guidelines to fit your specific frontend framework and application requirements.
