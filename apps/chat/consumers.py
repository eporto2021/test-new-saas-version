import json
import logging
import textwrap
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.ai.agents import AgentTypes
from apps.chat.models import ChatTypes, MessageTypes
from apps.chat.sessions import AgentSession, ChatSession, ChatSessionBase
from apps.users.models import CustomUser

logger = logging.getLogger("pegasus.ai")


class ChatConsumerBase(AsyncWebsocketConsumer):
    session: ChatSessionBase
    chat_type: ChatTypes

    async def connect(self):
        self.user = self.scope["user"]
        chat_id = self.scope["url_route"]["kwargs"].get("chat_id", None)

        query_string = self.scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        self.is_embedded = query_params.get("embedded", ["false"])[0] == "true"

        self.session = await self.create_session(self.user, self.chat_type, chat_id)

        if self.user.is_authenticated:
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json["message"]

        # do nothing with empty messages
        if not message_text.strip():
            return

        message, chat_created = await self.session.add_message(message_text)
        if chat_created and not self.is_embedded:
            # Send a message to tell the front end to update its url if not in embedded mode.
            await self.send(text_data=json.dumps({"pushURL": reverse("chat:single_chat", args=[self.session.chat.id])}))

        # show user's message immediately before calling OpenAI API
        user_message_html = render_to_string(
            "chat/websocket_components/user_message.html",
            {
                "message_text": message_text,
            },
        )
        await self.send(text_data=user_message_html)

        # render an empty system message where we'll stream our response
        contents_div_id = f"message-response-{message.id}"
        system_message_html = render_to_string(
            "chat/websocket_components/system_message.html",
            {
                "contents_div_id": contents_div_id,
            },
        )
        await self.send(text_data=system_message_html)

        try:
            response_stream = self.session.get_response_streaming()
            response = ""
            async for chunk in response_stream:
                if chunk:
                    if self.session.cumulative_streaming:
                        # cumulative streaming swaps the entire content of the div
                        chunk_html = textwrap.dedent(
                            f'''<div id="{contents_div_id}" class="pg-message-contents" hx-swap-oob="true">
                                  {_format_token(chunk)}
                                </div>'''
                        )
                        response = chunk
                    else:
                        # incremental streaming appends to the div using beforeend
                        chunk_html = f'<div hx-swap-oob="beforeend:#{contents_div_id}">{_format_token(chunk)}</div>'
                        response += chunk

                    await self.send(text_data=chunk_html)
        except Exception as e:
            logger.exception(e)
            response = None
        if not response:
            # if we didn't get a response we should show the user an error.
            error_html = render_to_string(
                "chat/websocket_components/final_system_message.html",
                {
                    "contents_div_id": contents_div_id,
                    "message": _("Sorry, there was an error with your message. Please try again."),
                },
            )
            await self.send(text_data=error_html)

        else:
            # once we've streamed the whole response, save it to the database
            system_message = await self.session.save_message(response, MessageTypes.AI)

            # replace final input with fully rendered version, so we can render markdown, etc.
            final_message_html = render_to_string(
                "chat/websocket_components/final_system_message.html",
                {
                    "contents_div_id": contents_div_id,
                    "message": system_message.content,
                },
            )
            await self.send(text_data=final_message_html)

    async def create_session(self, user: CustomUser, chat_type: ChatTypes, chat_id: int | None) -> ChatSessionBase:
        raise NotImplementedError("create_session must be implemented by subclasses")


class ChatConsumer(ChatConsumerBase):
    chat_type = ChatTypes.CHAT

    async def create_session(self, user: CustomUser, chat_type: ChatTypes, chat_id: int | None) -> ChatSessionBase:
        return ChatSession(user, chat_type, chat_id)


class AgentChatConsumerBase(ChatConsumerBase):
    chat_type = ChatTypes.AGENT
    agent_type: AgentTypes

    async def create_session(self, user: CustomUser, chat_type: ChatTypes, chat_id: int | None) -> ChatSessionBase:
        return AgentSession(user, chat_type, chat_id, self.agent_type)


class WeatherAgentChatConsumer(AgentChatConsumerBase):
    agent_type = AgentTypes.WEATHER


class AdminAgentChatConsumer(AgentChatConsumerBase):
    agent_type = AgentTypes.ADMIN


class EmployeesAgentChatConsumer(AgentChatConsumerBase):
    agent_type = AgentTypes.EMPLOYEES


def _format_token(token: str) -> str:
    # apply very basic formatting while we're rendering tokens in real-time
    token = token.replace("\n", "<br>")
    return token
