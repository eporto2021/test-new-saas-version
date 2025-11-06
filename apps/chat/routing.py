from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path(r"ws/aichat/", consumers.ChatConsumer.as_asgi(), name="ws_ai_new_chat"),
    path(r"ws/aichat/<slug:chat_id>/", consumers.ChatConsumer.as_asgi(), name="ws_ai_continue_chat"),
    path(r"ws/weatheragent/", consumers.WeatherAgentChatConsumer.as_asgi(), name="ws_weather_agent_chat"),
    path(r"ws/adminagent/", consumers.AdminAgentChatConsumer.as_asgi(), name="ws_admin_agent_chat"),
    path(r"ws/employeesagent/", consumers.EmployeesAgentChatConsumer.as_asgi(), name="ws_employees_agent_chat"),
]
