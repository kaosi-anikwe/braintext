from decimal import Decimal

# price constants
PERCENTAGE = 1.1
GPT_3_5_INPUT = Decimal("0.0000005")  # per token
GPT_3_5_OUTPUT = Decimal("0.0000015")  # per token
GPT_4_VISION_INPUT = Decimal("0.00001")  # per token
GPT_4_VISION_OUTPUT = Decimal("0.00003")  # per token
WHISPER = Decimal("0.0001")  # per second
TTS = Decimal("0.000015")  # per character
DALLE_3 = {  # per image
    "standard": {
        "1024x1024": Decimal("0.04"),
        "1024x1792": Decimal("0.08"),
        "1792x1024": Decimal("0.08"),
    },
    "hd": {
        "1024x1024": Decimal("0.08"),
        "1024x1792": Decimal("0.12"),
        "1792x1024": Decimal("0.12"),
    },
}
DALLE_2 = {
    "1024x1024": Decimal("0.02"),
    "512x512": Decimal("0.018"),
    "256x256": Decimal("0.016"),
}


def gpt_3_5_cost(tokens: dict):
    input_cost = float(int(tokens["input"]) * GPT_3_5_INPUT) * PERCENTAGE
    output_cost = float(int(tokens["output"]) * GPT_3_5_OUTPUT) * PERCENTAGE
    return input_cost + output_cost


def gpt_4_vision_cost(tokens: dict):
    input_cost = float(int(tokens["input"]) * GPT_4_VISION_INPUT) * PERCENTAGE
    output_cost = float(int(tokens["output"]) * GPT_4_VISION_OUTPUT) * PERCENTAGE
    return input_cost + output_cost


def whisper_cost(seconds: int):
    return float(int(seconds) * WHISPER) * PERCENTAGE


def tts_cost(characters: int):
    return float(int(characters) * TTS) * PERCENTAGE


def dalle3_cost(confg: dict):
    price = (
        float(DALLE_3[confg.get("type", "standard")][confg.get("res", "1024x1024")])
        if confg.get("type")
        else 0
    )
    return price * PERCENTAGE


def dalle2_cost(res: str):
    price = float(DALLE_2[res]) if res else 0
    return price * PERCENTAGE
