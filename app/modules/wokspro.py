# python imports
import io
import os
import json
import time
import math
import traceback
from typing import Any, Dict
from datetime import datetime

# installed imports
import folium
import gspread
import requests
from PIL import Image
from flask import url_for
from openai import OpenAI
from dotenv import load_dotenv
from flask import after_this_request
from oauth2client.service_account import ServiceAccountCredentials

# local imports
from app import logger
from app.models import Threads
from .prompts import assistant_instructions


load_dotenv()

# Init Google Sheets client and spreadsheet
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(os.getenv("SERVICE_ACCOUNT_CERT"), strict=False), scope
)
gc = gspread.authorize(credentials)
spreadsheet = gc.open_by_key(os.getenv("SPREADSHEET_ID"))
FILES = os.getenv("FILES")
TEMP_FOLDER = os.getenv("TEMP_FOLDER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WOKSPRO_MOTTO = "Learning always gets better."

with open(os.path.join(FILES, "names.json"), "r") as names_file:
    names = json.load(names_file)


FUNCTION_DESCRIPTIONS = [
    {
        "name": "generate_image",
        "description": "Generates an image with prompt extracted from user only on explicit request.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The image prompt or description to be used to generate the image.",
                },
                "response": {
                    "type": "string",
                    "description": "User friendly response to prompt.",
                },
            },
            "required": ["prompt", "response"],
        },
    },
    {
        "name": "speech_synthesis",
        "description": "Synthesize text response of prompts to audio when user requests for an audio response.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text prompt response to be synthesized",
                },
                "speed": {
                    "type": "number",
                    "description": "How fast or slow the audio response should be. Values range from 0.25 to 4.0. The default is 1.0",
                },
            },
            "required": ["text", "speed"],
        },
    },
    {
        "name": "speech_synthesis",
        "description": "Performs text-to-speech synthesis on user request.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to be synthesized into speech.",
                },
                "speed": {
                    "type": "number",
                    "description": "How fast or slow the synthesised speech should be. Values range from 0.25 to 4.0. The default is 1.0",
                },
            },
            "required": ["text", "speed"],
        },
    },
    {
        "name": "google_search",
        "description": "Performs online searches to retrieve information only on explicit request.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to be searched online coined from user prompt.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "media_search",
        "description": "Performs media searches on the internet. Takes in a user-friendly response to the query, a boolean for if image search or not, the file type if a document was requested, and the number of results",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to be searched online coined from user prompt.",
                },
                "response": {
                    "type": "string",
                    "description": "User-friendly response to prompt for image and document search.",
                },
                "image_search": {
                    "type": "boolean",
                    "description": "Wether or not the user requested for an image in the query.",
                },
                "file_type": {
                    "type": "string",
                    "description": "The type of file requested by the user in the query.",
                },
                "num": {
                    "type": "integer",
                    "description": "Number of results to be gotten. Default is 1.",
                },
            },
            "required": ["query", "num", "response"],
        },
    },
    {
        "name": "web_scrapping",
        "description": "Scrapes the URL provided by the user with the provided instruction.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to be scrapped.",
                },
                "instruction": {
                    "type": "string",
                    "description": "Sentence instruction for formatting web scrapping results. The default is to summarize.",
                },
            },
            "required": ["url", "instruction"],
        },
    },
    {
        "name": "plot_areas",
        "description": f"Plots on a map the requested areas from this array of dumpsites in Enugu: {names['names']}",
        "parameters": {
            "type": "object",
            "properties": {
                "locations": {
                    "type": "string",
                    "description": "An array of location names to be plotted E.g [Place1, Place2, Place3]",
                },
            },
            "required": ["locations"],
        },
    },
    {
        "name": "record_user_location",
        "description": "Records user's physical location extracted from the conversation",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The user's physical location",
                },
            },
            "required": ["location"],
        },
    },
]
client = OpenAI(api_key=OPENAI_API_KEY)


# Create or load assistant
def create_assistant():
    # Init OpenAI Client
    client = OpenAI(api_key=OPENAI_API_KEY)
    assistant_file_path = "assistant.json"

    # If there is an assistant.json file already, then load that assistant
    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, "r") as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data["assistant_id"]
            logger.info("Loaded existing assistant ID.")
    else:
        # If no assistant.json is present, create a new assistant using the below specifications
        # Pass knowledge documents
        file_ids = []
        for root, dirs, files in os.walk("wokspro_files"):
            for doc in files:
                doc_path = os.path.join(root, doc)
                with open(doc_path, "rb") as knowledge_file:
                    knowledge_doc = io.BytesIO(knowledge_file.read())
                    knowledge_doc.name = doc
                    logger.info(doc)
                    uploaded_file = client.files.create(
                        file=knowledge_doc,
                        purpose="assistants",
                    )
                    file_ids.append(uploaded_file.id)

        assistant = client.beta.assistants.create(
            instructions=assistant_instructions,
            model="gpt-4-0125-preview",
            tools=[
                {"type": "retrieval"},  # This adds the knowledge base as a tool
                *[
                    {"type": "function", "function": function}
                    for function in FUNCTION_DESCRIPTIONS
                ],
            ],
            file_ids=file_ids,
        )

        # Create a new assistant.json file to load on future runs
        with open(assistant_file_path, "w") as file:
            json.dump({"assistant_id": assistant.id}, file)
            logger.info("Created a new assistant and saved the ID.")

        assistant_id = assistant.id

    return assistant_id


def record_wokspro_message(thread: Threads, message: Any, role: str = "user"):
    if thread.last_run:
        last_run = client.beta.threads.runs.retrieve(
            thread_id=thread.thread_id, run_id=thread.last_run
        )
        if last_run.status != "completed":
            # delete thread and create new one
            client.beta.threads.delete(thread.thread_id)
            new_thread_id = client.beta.threads.create().id
            logger.info(f"New thread created with ID: {new_thread_id}")
            new_thread = Threads(thread_id=new_thread_id, phone_no=thread.phone_no)
            thread.delete()
            thread = new_thread

    client.beta.threads.messages.create(
        thread_id=thread.thread_id, role=role, content=message
    )
    return thread


def get_coordinates(location):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK":
        lat = data["results"][0]["geometry"]["location"]["lat"]
        lng = data["results"][0]["geometry"]["location"]["lng"]
        return lat, lng
    else:
        logger.info("Geocoding failed:", data["status"])
        return None, None


def haversine(coord1, coord2):
    # Radius of the Earth in kilometers
    R = 6371.0
    # Convert latitude and longitude from degrees to radians
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


def closest_coordinates(num, input_coord):
    with open(os.path.join(FILES, "coordinates.json"), "r") as file:
        coordinate_data = json.load(file)["coordinates"]
        all_coords = [
            (location["Latitude"], location["Longitude"], location["Name"])
            for location in coordinate_data
        ]
    # Calculate distances from input coordinate to all coordinates
    distances = [(coord, haversine(input_coord, coord)) for coord in all_coords]
    # Sort the distances by distance (closest first)
    sorted_distances = sorted(distances, key=lambda x: x[1])
    # Get the x closest coordinates
    closest_coords = [coord for coord, _ in sorted_distances[:num]]
    return closest_coords


def plot_areas(thread: Threads = None, **kwargs):
    from app.chatbot.functions import send_image

    try:
        locations = kwargs.get("locations", [])
        coordinates = kwargs.get("coordinates", [])
        if not coordinates:
            logger.info(locations)
            logger.info(f"COORDINATES: {locations}")
            logger.info(f"COORDINATES LEN: {len(locations)}")

            with open(os.path.join(FILES, "coordinates.json"), "r") as file:
                coordinate_data = json.load(file)["coordinates"]

            for location in locations:
                for area in coordinate_data:
                    if area["Name"] == location:
                        coordinates.append(
                            [area["Latitude"], area["Longitude"], area["Name"]]
                        )

        logger.info(f"COORDINTES: {coordinates}")

        m = folium.Map(location=coordinates[0][:2], zoom_start=15.5)

        for coordinate in coordinates:
            # Add a marker at a specific location with a custom icon and popup message
            folium.Marker(
                location=[coordinate[0], coordinate[1]],
                icon=folium.Icon(icon="location-pin", prefix="fa", color="blue"),
            ).add_to(m)
            # show name of area
            folium.Marker(
                location=[coordinate[0], coordinate[1]],
                popup=coordinate[2],
                icon=folium.DivIcon(
                    icon_size=(150, 36),
                    html=f'<div style="font-size: 20px; color: black;">{coordinate[2]}</div>',
                ),
            ).add_to(m)

            # Add a circle around the marker with specified radius and color
            # folium.Circle(
            #     radius=1000,  # radius in meters
            #     location=[coordinate[0], coordinate[1]],
            #     color="blue",
            #     fill=True,
            #     fill_color="blue",
            #     fill_opacity=0.3,  # opacity of the shaded area
            #     weight=1,
            # ).add_to(m)

            logger.info(f"ADDED {coordinate[2]} to map")

        # make all markers visible
        m.fit_bounds([(coord[0], coord[1]) for coord in locations])

        # Create a temporary file to save the image
        logger.info("Saving to png")
        img_path = os.path.join(TEMP_FOLDER, f"{datetime.now().strftime('%f')}.png")
        img_data = m._to_png()
        img = Image.open(io.BytesIO(img_data))
        img.save(img_path)
        logger.info("Image saved successfully")
        # Send the image using the send_image function
        image_url = f"{url_for('chatbot.send_media', _external=True, _scheme='https')}?filename={os.path.basename(img_path)}"
        logger.info(
            send_image(
                image_url, thread.phone_no, phone_number_id=kwargs.get("wokspro_id")
            )
        )

        return {"coordinates": locations, "success": True}
    except:
        logger.error(traceback.format_exc())
        return {"coordinates": [], "success": False}


def record_user_location(thread: Threads = None, **kwargs):
    from app.chatbot.functions import (
        send_text,
    )

    try:
        location = kwargs.get("location")
        coordinates = get_coordinates(location)
        logger.info(f"USER COORDINATES: {coordinates}")
        if not coordinates:
            return {
                "success": False,
                "message": "Failed to record location. Please try again",
            }
        thread.location = location
        thread.latitude = coordinates[0]
        thread.longitude = coordinates[1]
        thread.update()
        return {
            "success": True,
            "message": "Location recorded successfully",
        }
    except:
        return {
            "success": False,
            "message": "Failed to record location. Please try again",
        }


def update_spreadsheet(data: dict, sheetname: str = "Users"):
    # Get worksheet
    if sheetname not in [worksheet.title for worksheet in spreadsheet.worksheets()]:
        worksheet = spreadsheet.add_worksheet(sheetname, rows=100, cols=20)
    else:
        worksheet = spreadsheet.worksheet(sheetname)
    # Write header row
    header_row = worksheet.row_values(1)
    header = list(data.keys())
    if header_row != header:
        logger.info(f"Updating header")
        print(f"Updating header")
        worksheet.update("A1", [header])

    values = list(data.values())
    return worksheet.append_row(values, value_input_option="USER_ENTERED")


def wokspro_response(thread: Threads, data: Dict[Any, Any]):
    from app.chatbot.functions import (
        get_number,
        get_message_id,
        get_message_type,
        get_message,
        get_media_url,
        get_audio_duration,
        get_audio_id,
        get_image,
        get_interactive_response,
        download_media,
        send_text,
        send_reaction,
        send_interactive_message,
        delete_file,
        is_reply,
        reply_to_message,
        meta_split_and_respond,
        generate_list_message,
        WHATSAPP_CHAR_LIMIT,
    )
    from app.modules.functions import (
        speech_synthesis,
        generate_image,
        google_search,
        media_search,
        web_scrapping,
        encode_image,
    )

    FUNCTIONS = {
        "generate_image": {
            "type": "non-callback",
            "function": generate_image,
        },
        "speech_synthesis": {
            "type": "non-callback",
            "function": speech_synthesis,
        },
        "google_search": {
            "type": "callback",
            "function": google_search,
        },
        "media_search": {
            "type": "non-callback",
            "function": media_search,
        },
        "web_scrapping": {
            "type": "callback",
            "function": web_scrapping,
        },
        "plot_areas": {
            "type": "non-callback",
            "function": plot_areas,
        },
        "record_user_location": {
            "type": "callback",
            "function": record_user_location,
        },
    }

    wokspro_id = os.getenv("WOKSPRO_NUMBER_ID")
    number = f"+{get_number(data)}"
    message_id = get_message_id(data)
    message_type = get_message_type(data)
    message = "`audio recording`" if message_type != "text" else get_message(data)

    if message_type == "audio":
        from app.modules.functions import (
            openai_transcribe_audio,
            contains_greeting,
            contains_thanks,
        )

        callback = True
        function_name = ""
        audio_url = get_media_url(get_audio_id(data))
        audio_file = download_media(
            audio_url,
            f"{datetime.now().strftime('%M%S%f')}",
        )
        duration = get_audio_duration(audio_file)
        logger.info(f"AUDIO DURATION: {duration}")
        try:
            transcript = openai_transcribe_audio(audio_file)
            message = transcript
            greeting = contains_greeting(transcript)
            thanks = contains_thanks(transcript)
        except:
            logger.error(traceback.format_exc())
            text = "Error transcribing audio. Please try again later."
            thread = record_wokspro_message(thread=thread, message=message)
            thread = record_wokspro_message(
                thread=thread, message=message, role="assistant"
            )
            return send_text(text, number, wokspro_id)
        finally:
            # delete audio file
            delete_file(audio_file)
        # reactions
        (
            send_reaction(chr(128075), message_id, number, wokspro_id)
            if greeting
            else None
        )  # react waving hand
        (
            send_reaction(chr(128153), message_id, number, wokspro_id)
            if thanks
            else None
        )  # react blue love emoji

        # run the assistant
        thread = record_wokspro_message(thread=thread, message=message)
        run = client.beta.threads.runs.create(
            thread_id=thread.thread_id, assistant_id=create_assistant()
        )
        # update thread last run
        thread.last_run = run.id
        thread.update()
        # wait for response
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.thread_id, run_id=run.id
            )
            logger.info(f"Run status: {run_status.status}")
            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                # handle function call
                for (
                    tool_call
                ) in run_status.required_action.submit_tool_outputs.tool_calls:
                    logger.info(tool_call.function)
                    function_name = tool_call.function.name
                    callback = (
                        False
                        if FUNCTIONS[function_name]["type"] == "non-callback"
                        else True
                    )
                    if FUNCTIONS.get(function_name):
                        # get function arguments
                        arguments = json.loads(tool_call.function.arguments)
                        arguments["data"] = data
                        arguments["message"] = message
                        arguments["tokens"] = 0
                        arguments["message_request"] = None
                        arguments["wokspro_id"] = wokspro_id
                        arguments["thread"] = thread
                        output = FUNCTIONS[function_name]["function"](**arguments)
                        logger.info(output)
                        client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread.thread_id,
                            run_id=run.id,
                            tool_outputs=[
                                {
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps(output),
                                }
                            ],
                        )
            time.sleep(1)  # wait for a second before checking again

        if function_name == "record_user_location":
            check_thread = Threads.query.filter(Threads.phone_no == number).one()
            if check_thread.latitude and check_thread.longitude:
                logger.info("Starting Survey")

                @after_this_request
                def start_survey(response):
                    logger.info("Prompting for waste composition")
                    # Prompt for waste composition
                    with open(os.path.join(FILES, "composition.json"), "r") as file:
                        waste_types = json.load(file)["wasteCompositions"]
                    # Generate interactive message
                    header = "Choose Waste Composition"
                    body = (
                        "Which of these best describes your primary waste composition?"
                    )
                    choices = [
                        {
                            "title": "Waste Compositions",
                            "rows": waste_types,
                        }
                    ]
                    message_list = generate_list_message(
                        header=header,
                        body=body,
                        button_text="Choose",
                        sections=choices,
                        footer=WOKSPRO_MOTTO,
                    )
                    thread = record_wokspro_message(check_thread, body, "assistant")
                    send_interactive_message(
                        message_list,
                        thread.phone_no,
                        interactive_type="list",
                        phone_number_id=wokspro_id,
                    )
                    return response

        if callback:
            # retrieve and return the latest message from the assistant
            messages = client.beta.threads.messages.list(thread_id=thread.thread_id)
            text = messages.data[0].content[0].text
            annotations = text.annotations

            # Iterate over the annotations and remove them
            for _, annotation in enumerate(annotations):
                text.value = text.value.replace(annotation.text, "")
            text = text.value
            return speech_synthesis(
                data=data,
                text=text,
                tokens=0,
                message=transcript,
            )

    if message_type == "image":
        callback = True
        image = get_image(data)
        image_url = get_media_url(image["id"])
        image_path = download_media(
            image_url,
            f"{datetime.now().strftime('%M%S%f')}.jpg",
        )
        # convert to png
        image_content = Image.open(image_path)
        image_content = image_content.convert(
            "RGBA"
        )  # If the image has an alpha channel (transparency)
        image_content.save(image_path, format="PNG")
        prompt = image.get("caption", "What's in this image?")
        base64_image = encode_image(image_path)

        content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
        }
        thread = record_wokspro_message(thread, prompt)
        thread = record_wokspro_message(thread, content)

        # run the assistant
        thread = record_wokspro_message(thread=thread, message=message)
        run = client.beta.threads.runs.create(
            thread_id=thread.thread_id, assistant_id=create_assistant()
        )
        # update thread last run
        thread.last_run = run.id
        thread.update()
        # wait for response
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.thread_id, run_id=run.id
            )
            logger.info(f"Run status: {run_status.status}")
            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                # handle function call
                for (
                    tool_call
                ) in run_status.required_action.submit_tool_outputs.tool_calls:
                    logger.info(tool_call.function)
                    function_name = tool_call.function.name
                    callback = (
                        False
                        if FUNCTIONS[function_name]["type"] == "non-callback"
                        else True
                    )
                    if FUNCTIONS.get(function_name):
                        # get function arguments
                        arguments = json.loads(tool_call.function.arguments)
                        arguments["data"] = data
                        arguments["message"] = message
                        arguments["tokens"] = 0
                        arguments["message_request"] = None
                        arguments["wokspro_id"] = wokspro_id
                        arguments["thread"] = thread
                        output = FUNCTIONS[function_name]["function"](**arguments)
                        logger.info(output)
                        client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread.thread_id,
                            run_id=run.id,
                            tool_outputs=[
                                {
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps(output),
                                }
                            ],
                        )
            time.sleep(1)  # wait for a second before checking again
        if callback:
            # retrieve and return the latest message from the assistant
            messages = client.beta.threads.messages.list(thread_id=thread.thread_id)
            text = messages.data[0].content[0].text
            annotations = text.annotations

            # Iterate over the annotations and remove them
            for _, annotation in enumerate(annotations):
                text.value = text.value.replace(annotation.text, "")
            text = text.value
            return send_text(message, number, wokspro_id)

    if message_type == "text":
        from app.modules.functions import contains_greeting, contains_thanks

        isreply = is_reply(data)
        greeting = contains_greeting(message)
        thanks = contains_thanks(message)
        callback = True
        function_name = ""
        # react to message
        (
            send_reaction(chr(128075), message_id, number, wokspro_id)
            if greeting
            else None
        )  # react waving hand
        (
            send_reaction(chr(128153), message_id, number, wokspro_id)
            if thanks
            else None
        )  # react blue love emoji

        # run the assistant
        thread = record_wokspro_message(thread=thread, message=message)
        run = client.beta.threads.runs.create(
            thread_id=thread.thread_id, assistant_id=create_assistant()
        )
        # update thread last run
        thread.last_run = run.id
        thread.update()
        # wait for response
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.thread_id, run_id=run.id
            )
            logger.info(f"Run status: {run_status.status}")
            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                # handle function call
                for (
                    tool_call
                ) in run_status.required_action.submit_tool_outputs.tool_calls:
                    logger.info(tool_call.function)
                    function_name = tool_call.function.name
                    callback = (
                        False
                        if FUNCTIONS[function_name]["type"] == "non-callback"
                        else True
                    )
                    if FUNCTIONS.get(function_name):
                        # get function arguments
                        arguments = json.loads(tool_call.function.arguments)
                        arguments["data"] = data
                        arguments["message"] = message
                        arguments["tokens"] = 0
                        arguments["message_request"] = None
                        arguments["wokspro_id"] = wokspro_id
                        arguments["thread"] = thread
                        output = FUNCTIONS[function_name]["function"](**arguments)
                        logger.info(output)
                        client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread.thread_id,
                            run_id=run.id,
                            tool_outputs=[
                                {
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps(output),
                                }
                            ],
                        )
            time.sleep(1)  # wait for a second before checking again

        if function_name == "record_user_location":
            check_thread = Threads.query.filter(Threads.phone_no == number).one()
            if check_thread.latitude and check_thread.longitude:
                logger.info("Starting Survey")

                @after_this_request
                def start_survey(response):
                    logger.info("Prompting for waste composition")
                    # Prompt for waste composition
                    with open(os.path.join(FILES, "composition.json"), "r") as file:
                        waste_types = json.load(file)["wasteCompositions"]
                    # Generate interactive message
                    header = "Choose Waste Composition"
                    body = (
                        "Which of these best describes your primary waste composition?"
                    )
                    choices = [
                        {
                            "title": "Waste Compositions",
                            "rows": waste_types,
                        }
                    ]
                    message_list = generate_list_message(
                        header=header,
                        body=body,
                        button_text="Choose",
                        sections=choices,
                        footer=WOKSPRO_MOTTO,
                    )
                    thread = record_wokspro_message(check_thread, body, "assistant")
                    send_interactive_message(
                        message_list,
                        thread.phone_no,
                        interactive_type="list",
                        phone_number_id=wokspro_id,
                    )
                    return response

        if callback:
            # retrieve and return the latest message from the assistant
            messages = client.beta.threads.messages.list(thread_id=thread.thread_id)
            text = messages.data[0].content[0].text
            annotations = text.annotations

            # Iterate over the annotations and remove them
            for _, annotation in enumerate(annotations):
                text.value = text.value.replace(annotation.text, "")
            text = text.value

            if text:
                if len(text) < WHATSAPP_CHAR_LIMIT:
                    return (
                        send_text(text, number, wokspro_id)
                        if not isreply
                        else reply_to_message(message_id, number, text, wokspro_id)
                    )
                return (
                    meta_split_and_respond(
                        text, number, message_id, phone_id=wokspro_id
                    )
                    if not isreply
                    else meta_split_and_respond(
                        text, number, message_id, reply=True, phone_id=wokspro_id
                    )
                )
            else:
                text = "I was unable to retrieve the requested information. Please try again later."
                thread = record_wokspro_message(thread, message, "assistant")
                return reply_to_message(message_id, number, text, wokspro_id)

    if message_type == "interactive":
        response = get_interactive_response(data)
        logger.info(response)
        type = response.get("type", "list_reply")
        message = response[type]["title"]
        reply_id = response[type]["id"]
        isreply = is_reply(data)
        thread = record_wokspro_message(thread, message)
        if type == "list_reply":
            # Waste Composition
            if "waste_" in reply_id:
                thread.waste_comp = message
                thread.update()
                # Prompt for waste management practices
                logger.info("Prompting for waste management practices")
                with open(os.path.join(FILES, "management.json"), "r") as file:
                    management_practices = json.load(file)["wasteManagementPractices"]
                # Generate interactive message
                header = "Current Waste Management Practice"
                body = "Which of these best describes the current waste management practice in your area?"
                choices = [
                    {
                        "title": "Waste Compositions",
                        "rows": management_practices,
                    }
                ]
                message_list = generate_list_message(
                    header=header,
                    body=body,
                    button_text="Choose",
                    sections=choices,
                    footer=WOKSPRO_MOTTO,
                )
                thread = record_wokspro_message(thread, body, "assistant")
                return send_interactive_message(
                    message_list,
                    thread.phone_no,
                    interactive_type="list",
                    phone_number_id=wokspro_id,
                )
            # Waste Management Practice
            if "wmp_" in reply_id:
                thread.practice = message
                thread.update()
                # Prompt for role
                logger.info("Prompting for role")
                with open(os.path.join(FILES, "roles.json"), "r") as file:
                    roles = json.load(file)["roles"]
                # Generate interactive message
                header = "Community Role"
                body = (
                    "Which of these best describes your current role in your community?"
                )
                choices = [
                    {
                        "title": "Community Roles",
                        "rows": roles,
                    }
                ]
                message_list = generate_list_message(
                    header=header,
                    body=body,
                    button_text="Choose",
                    sections=choices,
                    footer=WOKSPRO_MOTTO,
                )
                thread = record_wokspro_message(thread, body, "assistant")
                return send_interactive_message(
                    message_list,
                    thread.phone_no,
                    interactive_type="list",
                    phone_number_id=wokspro_id,
                )
            if "role_" in reply_id:
                thread.role = message
                thread.update()
                # Show closest dump sites
                logger.info("Showing closest dumpsites")
                message = "Thank you for your responses.\nI am plotting a map to show you the closest dumpsites to your location.\nAfter that, I'll suggest waste management practices based on the information you submitted.\nPlease exercise patience during this process."
                send_text(message, number, phone_number_id=wokspro_id)
                thread = record_wokspro_message(thread, message, "assistant")
                coordinates = closest_coordinates(
                    5, (thread.latitude, thread.longitude)
                )
                plot_areas(
                    thread=thread, coordinates=coordinates, wokspro_id=wokspro_id
                )
                # Suggest waste management practices
                logger.info("Suggesting waste management practices")
                message = f"""
                            Considering my location ({thread.location}), waste composition ({thread.waste_comp}), current waste management practices ({thread.practice}), 
                            and role ({thread.role}) in my community, suggest waste management practices that I can adapt.
                        """
                thread = record_wokspro_message(thread, message)
                # run the assistant
                thread = record_wokspro_message(thread=thread, message=message)
                run = client.beta.threads.runs.create(
                    thread_id=thread.thread_id,
                    assistant_id=create_assistant(),
                    instructions="Do not call any function. Give a comprehensize text response",
                )
                # update thread last run
                thread.last_run = run.id
                thread.update()
                # wait for response
                while True:
                    run_status = client.beta.threads.runs.retrieve(
                        thread_id=thread.thread_id, run_id=run.id
                    )
                    logger.info(f"Run status: {run_status.status}")
                    if run_status.status == "completed":
                        break
                    elif run_status.status == "requires_action":
                        # handle function call
                        for (
                            tool_call
                        ) in run_status.required_action.submit_tool_outputs.tool_calls:
                            logger.info(tool_call.function)
                            function_name = tool_call.function.name
                            callback = (
                                False
                                if FUNCTIONS[function_name]["type"] == "non-callback"
                                else True
                            )
                            if FUNCTIONS.get(function_name):
                                # get function arguments
                                arguments = json.loads(tool_call.function.arguments)
                                arguments["data"] = data
                                arguments["message"] = message
                                arguments["tokens"] = 0
                                arguments["message_request"] = None
                                arguments["wokspro_id"] = wokspro_id
                                arguments["thread"] = thread
                                output = FUNCTIONS[function_name]["function"](
                                    **arguments
                                )
                                logger.info(output)
                                client.beta.threads.runs.submit_tool_outputs(
                                    thread_id=thread.thread_id,
                                    run_id=run.id,
                                    tool_outputs=[
                                        {
                                            "tool_call_id": tool_call.id,
                                            "output": json.dumps(output),
                                        }
                                    ],
                                )

                    time.sleep(1)  # wait for a second before checking again

                # retrieve and return the latest message from the assistant
                messages = client.beta.threads.messages.list(thread_id=thread.thread_id)
                text = messages.data[0].content[0].text
                annotations = text.annotations

                # Iterate over the annotations and remove them
                for _, annotation in enumerate(annotations):
                    text.value = text.value.replace(annotation.text, "")
                text = text.value

                if text:

                    @after_this_request
                    def record_user(response):
                        thread.recommended = text
                        thread.update()
                        # log record to Google Sheets
                        update_spreadsheet(thread.export())
                        return response

                    if len(text) < WHATSAPP_CHAR_LIMIT:
                        return send_text(text, number, wokspro_id)
                    return (
                        meta_split_and_respond(
                            text, number, message_id, phone_id=wokspro_id
                        )
                        if not isreply
                        else meta_split_and_respond(
                            text, number, message_id, reply=True, phone_id=wokspro_id
                        )
                    )
