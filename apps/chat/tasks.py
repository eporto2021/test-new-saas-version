import litellm
from celery import shared_task

from apps.chat.models import Chat
from apps.chat.prompts import get_chat_naming_prompt
from apps.chat.utils import get_llm_kwargs


@shared_task
def set_chat_name(chat_id: int, message: str):
    chat = Chat.objects.get(id=chat_id)
    if not message:
        return
    elif len(message) < 30:
        # for short messages, just use them as the chat name. the summary won't help
        chat.name = message
        chat.save()
    else:
        # set the name with openAI
        messages = [
            {"role": "developer", "content": get_chat_naming_prompt()},
            {"role": "user", "content": f"Summarize the following text: '{message}'"},
        ]
        response = litellm.completion(messages=messages, **get_llm_kwargs())
        chat.name = response.choices[0].message.content[:100].strip()
        chat.save()
