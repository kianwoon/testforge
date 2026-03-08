# Teams Bot Handler

## Overview

The `NanoClawTeamsBot` class is the core handler for Microsoft Teams bot integration. It extends `ActivityHandler` from the Microsoft Bot Framework and processes incoming Teams messages to interact with the NanoClaw test automation system.

## Architecture

```
Teams Message → NanoClawTeamsBot → Message Router → Handler
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              help command     status query     test case submission
                    ↓                 ↓                 ↓
            _handle_help()   _handle_status()  _handle_test_case()
                                      ↓
                              AgentAPIClient → Agent API
```

## Components

### Dependencies

- **ConversationManager**: Manages user conversation state and context
- **AgentAPIClient**: Communicates with the Agent API for test generation
- **TeamsMessageAdapter**: Formats messages and parses test cases

### Message Handlers

#### 1. Help Command (`help`)
Returns usage instructions and test case format guidelines.

#### 2. Status Query (`status <job-id>`)
Queries the Agent API for job status and returns formatted status message.

#### 3. Test Case Submission (default)
Parses the message as a test case, submits to Agent API, and returns job ID.

## Usage

### Initialization

```python
from bot.teams_bot import NanoClawTeamsBot
from bot.conversation_manager import ConversationManager
from bot.agent_client import AgentAPIClient

# Initialize dependencies
conversation_manager = ConversationManager()
agent_client = AgentAPIClient(base_url="http://localhost:8000")

# Create bot instance
bot = NanoClawTeamsBot(conversation_manager, agent_client)
```

### Processing Messages

```python
from botbuilder.schema import Activity

# Create activity from Teams message
activity = Activity(
    type=ActivityTypes.message,
    text="Test: Login test\nScope: Auth\nSteps:\n1. Navigate to login",
    from_property=MagicMock(id="user-123")
)

# Handle message
response = await bot.on_message_activity(activity)
# response contains formatted message to send back to user
```

## Message Flow

### Test Case Submission Flow

1. User sends test case message in Teams
2. Bot receives activity via `on_message_activity()`
3. Message router identifies it as test case (not help/status command)
4. `_handle_test_case()` is called:
   - Parse message using `TeamsMessageAdapter.parse_message()`
   - Submit test case via `AgentAPIClient.submit_test_case()`
   - Update conversation state via `ConversationManager.update_state()`
   - Return formatted response with job ID

### Status Query Flow

1. User sends "status job-123" in Teams
2. Bot parses command and extracts job ID
3. `_handle_status()` is called:
   - Query status via `AgentAPIClient.get_status()`
   - Format response using `TeamsMessageAdapter.format_status()`
   - Return formatted status message

### Help Command Flow

1. User sends "help" in Teams
2. Bot returns static help text with usage instructions

## Error Handling

All handlers include error handling:

- **Parse errors**: Returns formatted error message
- **API errors**: Returns error with details
- **Unexpected errors**: Caught at top-level, logged, and formatted error returned

## Testing

The bot handler includes comprehensive tests:

```bash
# Run tests
python -m pytest bot/tests/test_teams_bot.py -v

# Run with coverage
python -m pytest bot/tests/test_teams_bot.py --cov=bot.bot.teams_bot --cov-report=term-missing
```

### Test Coverage

- Test case submission (valid and error cases)
- Status query (found and not found)
- Help command
- API error handling
- Minimal test case handling

## Configuration

The bot handler requires:

1. **ConversationManager**: Configured with TTL for conversation state
2. **AgentAPIClient**: Configured with Agent API base URL and timeout

Example configuration:

```python
conversation_manager = ConversationManager(ttl_minutes=30)
agent_client = AgentAPIClient(
    base_url="http://localhost:8000",
    timeout=30
)
```

## Integration with Teams

This handler is designed to work with:

- **Microsoft Bot Framework**: Handles activity routing
- **Teams Adapter**: Receives messages from Teams channel
- **Webhook Server**: Receives HTTP requests from Teams

The handler returns response text, which the webhook server sends back to Teams via `TurnContext.send_activity()`.

## Future Enhancements

Potential improvements:

1. **Proactive messages**: Send notifications when jobs complete
2. **Rich cards**: Use adaptive cards for better UI
3. **Multi-turn conversations**: Interactive test case refinement
4. **Command shortcuts**: Quick commands for common operations
5. **Job management**: List, cancel, retry jobs
