# braintext

ChatGPT WhatsApp chatbot
A Python-based chatbot that connects ChatGPT to WhatsApp, enabling intelligent, conversational AI interactions directly within your WhatsApp chats. Braintext is designed for easy setup, secure API integration, and persistent chat history, making it ideal for personal productivity, customer support, or group conversations.

## Features

- Seamless integration with WhatsApp
- Powered by OpenAI's ChatGPT
- Persistent chat history
- Easy deployment and configuration

## Requirements

- Python 3.8+
- [OpenAI API key](https://platform.openai.com/account/api-keys)
- [WhatsApp Business API](https://www.twilio.com/whatsapp) or [yowsup](https://github.com/tgalal/yowsup)
- `pip` for installing dependencies

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/braintext.git
   cd braintext
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   WHATSAPP_API_KEY=your_whatsapp_api_key
   ```
   Replace the values with your actual API keys.

## Usage

1. **Start the bot:**

   ```bash
   python main.py
   ```

2. **Interact via WhatsApp:**
   - Send a message to your WhatsApp bot number.
   - The bot will respond using ChatGPT.

## Configuration

- Edit `config.yaml` to customize bot behavior, prompt templates, and logging.
- For advanced settings, refer to the comments in the configuration files.

## Troubleshooting

- Ensure all API keys in your `.env` file are valid and active.
- Check logs in the `logs/` directory for errors.
- For WhatsApp API issues, consult your provider's documentation.

## Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.

## License

This project is licensed under the MIT License.
