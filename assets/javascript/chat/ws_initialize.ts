// Chat streaming event handlers
// Include this asset only on pages that have chat components

document.addEventListener('DOMContentLoaded', () => {
  initializeChatHandlers();
});

// Also initialize on HTMX swaps in case the chat is loaded dynamically
document.body.addEventListener('htmx:afterSwap', () => {
  initializeChatHandlers();
});

function initializeChatHandlers() {
  // Find chat components and attach handlers
  const chatWrappers = document.querySelectorAll('.pg-chat-wrapper');

  chatWrappers.forEach(wrapper => {
    // Skip if already initialized
    if (wrapper.hasAttribute('data-chat-initialized')) {
      return;
    }

    // Mark as initialized
    wrapper.setAttribute('data-chat-initialized', 'true');

    // Listen for websocket messages
    wrapper.addEventListener('htmx:wsAfterMessage', (evt: any) => {
      // Auto-scroll to bottom
      const messageList = wrapper.querySelector('#message-list');
      if (messageList) {
        messageList.scrollTop = messageList.scrollHeight;
      }

      // Handle URL updates
      try {
        const message = JSON.parse(evt.detail.message);
        if (message.pushURL) {
          window.history.pushState({}, '', message.pushURL);
        }
      } catch (e) {
        // Not JSON - likely a regular HTMX message, ignore
      }
    });
  });
}
