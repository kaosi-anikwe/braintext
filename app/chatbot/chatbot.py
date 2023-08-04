# python imports
import os
import json
import traceback
from datetime import datetime

# installed imports
from flask import Blueprint, request, url_for, jsonify, send_file
from dotenv import load_dotenv

# local imports
from .functions import *
from ..modules.functions import *
from ..models import (
    Users,
    UserSettings,
    BasicSubscription,
    StandardSubscription,
    PremiumSubscription,
)

load_dotenv()

chatbot = Blueprint("chatbot", __name__)
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")


@chatbot.get("/send-voice-note")
def send_voice_note():
    filename = request.args.get("filename")
    file_ = f"{TEMP_FOLDER}/{filename}"
    if os.path.exists(file_):
        return send_file(file_)
    else:
        return "Not found", 404


@chatbot.route("/meta-chatbot", methods=["GET", "POST"])
def webhook():
    data = request.get_json()
    try:
        if is_message(data):
            name = get_name(data)
            number = f"+{get_number(data)}"
            message_id = get_message_id(data)
            message_type = get_message_type(data)

            mark_as_read(message_id)
            # try to get user
            user = Users.query.filter(Users.phone_no == number).one_or_none()
            if user:  # user account exists
                if user.phone_verified:
                    if user.email_verified:
                        # identify user account type
                        if user.account_type == "Basic":
                            subscription = BasicSubscription.query.filter(
                                BasicSubscription.user_id == user.id
                            ).one_or_none()
                            if subscription:
                                if subscription.respond():
                                    if message_type == "image":
                                        # Image editing/variation
                                        try:
                                            image = get_image(data)
                                            image_url = get_media_url(image["id"])
                                            image_path = download_media(
                                                image_url,
                                                f"{datetime.utcnow().strftime('%M%S%f')}.jpg",
                                            )
                                            if "caption" in image:
                                                prompt = image["caption"]
                                                if "variation" in prompt.lower():
                                                    image_url = image_variation(
                                                        image_path
                                                    )
                                                else:
                                                    image_url = image_edit(
                                                        image_path, prompt
                                                    )
                                                response_caption = f"Here's {prompt}"
                                            else:
                                                # Image variation
                                                image_url = image_variation(image_path)

                                            log_response(
                                                name=name,
                                                number=number,
                                                message=message,
                                            )
                                            send_image(
                                                image_url, number, response_caption
                                            ) if "caption" in image else send_image(
                                                image_url, number
                                            )
                                        except:
                                            print(traceback.format_exc())
                                            text = "Something went wrong. Please try again later."
                                            send_text(text, number)
                                    if message_type == "text":
                                        message = get_message(data)
                                        if "dalle" in message.lower():
                                            # Image generation
                                            prompt = message.lower().replace(
                                                "dalle", ""
                                            )
                                            try:
                                                image_url = image_response(prompt)
                                                caption = f"Here's {prompt}"
                                                log_response(
                                                    name=name,
                                                    number=number,
                                                    message=prompt,
                                                )
                                                send_image(image_url, number, caption)
                                            except:
                                                print(traceback.format_exc())
                                                text = "Sorry, I cannot respond to that at the moment, please try again later."
                                                reply_to_message(
                                                    message_id, number, text
                                                )
                                        else:
                                            # Chat response
                                            meta_chat_response(
                                                data=data,
                                                user=user,
                                                subscription=subscription,
                                            )
                                    elif message_type == "audio":
                                        # Audio response
                                        try:
                                            audio_url = get_media_url(
                                                get_audio_id(data)
                                            )
                                            audio_file = download_media(
                                                audio_url,
                                                f"{datetime.utcnow().strftime('%M%S%f')}",
                                            )
                                            try:
                                                transcript = transcribe_audio(
                                                    audio_file
                                                )
                                            except:
                                                print(traceback.format_exc())
                                                text = "Error transcribing audio. Please try again later."
                                                send_text(text, number)

                                            # delete audio file
                                            if os.path.exists(audio_file):
                                                os.remove(audio_file)
                                            try:
                                                user_db_path = get_user_db(name, number)
                                                messages = load_messages(
                                                    prompt=transcript,
                                                    db_path=user_db_path,
                                                )
                                                text, tokens, role = text_response(
                                                    messages=messages, number=number
                                                )
                                            except TimeoutError:
                                                text = "Sorry your response is taking longer than usual. Please hold on."
                                                send_text(text, number)

                                            # record ChatGPT response
                                            new_message = {
                                                "role": role,
                                                "content": text,
                                            }
                                            new_message = Messages(
                                                new_message, user_db_path
                                            )
                                            new_message.insert()

                                            log_response(
                                                name=name,
                                                number=number,
                                                message=prompt,
                                                tokens=tokens,
                                            )
                                            user_settings = user.user_settings()

                                            if user_settings.voice_response:
                                                try:
                                                    audio_filename = synthesize_speech(
                                                        text=text,
                                                        voice=user_settings.ai_voice_type,
                                                    )
                                                    if audio_filename == None:
                                                        text = "AWS session expired."
                                                        send_text(text, number)
                                                    audio_path = os.path.join(
                                                        TEMP_FOLDER, audio_filename
                                                    )

                                                    # convert to ogg with ffmpeg
                                                    subprocess.Popen(
                                                        f"ffmpeg -i '{audio_path}' -c:a libopus '{audio_path.split('.')[0]}.opus'",
                                                        shell=True,
                                                        stdout=subprocess.DEVNULL,
                                                        stderr=subprocess.STDOUT,
                                                    ).wait()

                                                    # remove original audio
                                                    if os.path.exists(audio_path):
                                                        os.remove(audio_path)

                                                    media_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename={audio_filename.split('.')[0]}.opus"
                                                    print(media_url)

                                                    send_audio(media_url, number)
                                                except BotoCoreError:
                                                    print(traceback.format_exc())
                                                    text = "Sorry, I cannot respond to that at the moment, please try again later."
                                                    send_text(text, number)
                                                except ClientError:
                                                    print(traceback.format_exc())
                                                    text = "Sorry, you're response was too long. Please rephrase the question or break it into segments."
                                                    send_text(text, number)
                                            else:
                                                if len(text) < WHATSAPP_CHAR_LIMIT:
                                                    send_text(text, number)
                                                else:
                                                    meta_split_and_respond(
                                                        text,
                                                        number,
                                                        get_message_id(data),
                                                    )
                                        except:
                                            print(traceback.format_exc())
                                            text = "Sorry, I cannot respond to that at the moment, please try again later."
                                            send_text(text, number)
                                else:
                                    text = f"You have exceed your limit for the week.\nYour prompts will be renewed on {subscription.get_expire_date().strftime('%A, %d/%m/%Y')} at {subscription.get_expire_date().strftime('%I:%M %p')}.\nUpgrade your account to decrease limits.\nhttps://braintext.io/profile"
                                    reply_to_message(
                                        message_id, number, text
                                    ) if message_type == "text" else send_text(
                                        message, number
                                    )
                            else:
                                text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                                reply_to_message(
                                    message_id, number, text
                                ) if message_type == "text" else send_text(
                                    message, number
                                )
                        if user.account_type == "Standard":
                            subscription = user.get_active_sub()
                            if subscription:
                                if not subscription.expired():
                                    if message_type == "audio":
                                        # Audio response
                                        text = "You don't have access to this service. Please upgrade your account to decrease limits. \nhttps://braintext.io/profile"
                                        reply_to_message(message_id, number, text)
                                    elif message_type == "image":
                                        # Image editing/variation
                                        try:
                                            image = get_image(data)
                                            image_url = get_media_url(image["id"])
                                            image_path = download_media(
                                                image_url,
                                                f"{datetime.utcnow().strftime('%M%S%f')}.jpg",
                                            )
                                            if "caption" in image:
                                                prompt = image["caption"]
                                                if "variation" in prompt.lower():
                                                    image_url = image_variation(
                                                        image_path
                                                    )
                                                else:
                                                    image_url = image_edit(
                                                        image_path, prompt
                                                    )
                                                response_caption = f"Here's {prompt}"
                                            else:
                                                # Image variation
                                                image_url = image_variation(image_path)

                                            log_response(
                                                name=name,
                                                number=number,
                                                message=message,
                                            )
                                            send_image(
                                                image_url, number, response_caption
                                            ) if "caption" in image else send_image(
                                                image_url, number
                                            )
                                        except:
                                            print(traceback.format_exc())
                                            text = "Something went wrong. Please try again later."
                                            send_text(text, number)
                                    elif message_type == "text":
                                        message = get_message(data)
                                        if "dalle" in message.lower():
                                            # Image generation
                                            prompt = message.lower().replace(
                                                "dalle", ""
                                            )
                                            try:
                                                image_url = image_response(prompt)
                                                caption = f"Here's {prompt}"
                                                log_response(
                                                    name=name,
                                                    number=number,
                                                    message=prompt,
                                                )
                                                send_image(image_url, number, caption)
                                            except:
                                                print(traceback.format_exc())
                                                text = "Sorry, I cannot respond to that at the moment, please try again later."
                                                reply_to_message(
                                                    message_id, number, text
                                                )
                                        else:
                                            # Chat response
                                            meta_chat_response(
                                                data=data,
                                                user=user,
                                                subscription=subscription,
                                            )
                                else:
                                    text = "It seems your subscription has expired. Plese renew your subscription to continue to enjoy your services. \nhttps://braintext.io/profile"
                                    reply_to_message(
                                        message_id, number, text
                                    ) if message_type == "text" else send_text(
                                        message, number
                                    )
                            else:
                                text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                                reply_to_message(
                                    message_id, number, text
                                ) if message_type == "text" else send_text(
                                    message, number
                                )
                        if user.account_type == "Premium":
                            subscription = user.get_active_sub()
                            if subscription:
                                if not subscription.expired():
                                    if message_type == "audio":
                                        # Audio response
                                        try:
                                            audio_url = get_media_url(
                                                get_audio_id(data)
                                            )
                                            audio_file = download_media(
                                                audio_url,
                                                f"{datetime.utcnow().strftime('%M%S%f')}",
                                            )
                                            try:
                                                transcript = transcribe_audio(
                                                    audio_file
                                                )
                                            except:
                                                print(traceback.format_exc())
                                                text = "Error transcribing audio. Please try again later."
                                                send_text(text, number)

                                            # delete audio file
                                            if os.path.exists(audio_file):
                                                os.remove(audio_file)
                                            try:
                                                user_db_path = get_user_db(name, number)
                                                messages = load_messages(
                                                    prompt=transcript,
                                                    db_path=user_db_path,
                                                )
                                                text, tokens, role = text_response(
                                                    messages=messages, number=number
                                                )
                                            except TimeoutError:
                                                text = "Sorry your response is taking longer than usual. Please hold on."
                                                send_text(text, number)

                                            # record ChatGPT response
                                            new_message = {
                                                "role": role,
                                                "content": text,
                                            }
                                            new_message = Messages(
                                                new_message, user_db_path
                                            )
                                            new_message.insert()

                                            log_response(
                                                name=name,
                                                number=number,
                                                message=text,
                                                tokens=tokens,
                                            )
                                            user_settings = user.user_settings()

                                            if user_settings.voice_response:
                                                try:
                                                    audio_filename = synthesize_speech(
                                                        text=text,
                                                        voice=user_settings.ai_voice_type,
                                                    )
                                                    if audio_filename == None:
                                                        text = "AWS session expired."
                                                        send_text(text, number)
                                                    audio_path = os.path.join(
                                                        TEMP_FOLDER, audio_filename
                                                    )

                                                    # convert to ogg with ffmpeg
                                                    subprocess.Popen(
                                                        f"ffmpeg -i '{audio_path}' -c:a libopus '{audio_path.split('.')[0]}.opus'",
                                                        shell=True,
                                                        stdout=subprocess.DEVNULL,
                                                        stderr=subprocess.STDOUT,
                                                    ).wait()

                                                    # remove original audio
                                                    if os.path.exists(audio_path):
                                                        os.remove(audio_path)

                                                    media_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename={audio_filename.split('.')[0]}.opus"
                                                    print(media_url)

                                                    send_audio(media_url, number)
                                                except BotoCoreError:
                                                    print(traceback.format_exc())
                                                    text = "Sorry, I cannot respond to that at the moment, please try again later."
                                                    send_text(text, number)
                                                except ClientError:
                                                    print(traceback.format_exc())
                                                    text = "Sorry, you're response was too long. Please rephrase the question or break it into segments."
                                                    send_text(text, number)
                                            else:
                                                if len(text) < WHATSAPP_CHAR_LIMIT:
                                                    send_text(text, number)
                                                else:
                                                    meta_split_and_respond(
                                                        text,
                                                        number,
                                                        get_message_id(data),
                                                    )
                                        except:
                                            print(traceback.format_exc())
                                            text = "Sorry, I cannot respond to that at the moment, please try again later."
                                            send_text(text, number)
                                    if message_type == "image":
                                        # Image editing/variation
                                        try:
                                            image = get_image(data)
                                            image_url = get_media_url(image["id"])
                                            image_path = download_media(
                                                image_url,
                                                f"{datetime.utcnow().strftime('%M%S%f')}.jpg",
                                            )
                                            if "caption" in image:
                                                prompt = image["caption"]
                                                if "variation" in prompt.lower():
                                                    image_url = image_variation(
                                                        image_path
                                                    )
                                                else:
                                                    image_url = image_edit(
                                                        image_path, prompt
                                                    )
                                                response_caption = f"Here's {prompt}"
                                            else:
                                                # Image variation
                                                image_url = image_variation(image_path)

                                            log_response(
                                                name=name,
                                                number=number,
                                                message=message,
                                            )
                                            send_image(
                                                image_url, number, response_caption
                                            ) if "caption" in image else send_image(
                                                image_url, number
                                            )
                                        except:
                                            print(traceback.format_exc())
                                            text = "Something went wrong. Please try again later."
                                            send_text(text, number)
                                    if message_type == "text":
                                        message = get_message(data)
                                        if "dalle" in message.lower():
                                            # Image generation
                                            prompt = message.lower().replace(
                                                "dalle", ""
                                            )
                                            try:
                                                image_url = image_response(prompt)
                                                caption = f"Here's {prompt}"
                                                log_response(
                                                    name=name,
                                                    number=number,
                                                    message=prompt,
                                                )
                                                send_image(image_url, number, caption)
                                            except:
                                                print(traceback.format_exc())
                                                text = "Sorry, I cannot respond to that at the moment, please try again later."
                                                reply_to_message(
                                                    message_id, number, text
                                                )
                                        else:
                                            # Chat response
                                            meta_chat_response(
                                                data=data,
                                                user=user,
                                                subscription=subscription,
                                            )
                                else:
                                    text = "It seems your subscription has expired. Plese renew your subscription to continue to enjoy your services. \nhttps://braintext.io/profile"
                                    reply_to_message(
                                        message_id, number, text
                                    ) if message_type == "text" else send_text(
                                        message, number
                                    )
                            else:
                                text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                                reply_to_message(
                                    message_id, number, text
                                ) if message_type == "text" else send_text(
                                    message, number
                                )
                    else:
                        text = "Please verify your email to access the service. https://braintext.io/profile"
                        reply_to_message(
                            message_id, number, text
                        ) if message_type == "text" else send_text(message, number)
                else:
                    text = "Please verify your number to access the service. https://braintext.io/profile"
                    reply_to_message(
                        message_id, number, text
                    ) if message_type == "text" else send_text(message, number)
            else:  # no account found
                text = "To use BrainText, please sign up for an account at https://braintext.io"
                reply_to_message(
                    message_id, number, text
                ) if message_type == "text" else send_text(message, number)
    except:
        print(traceback.format_exc())
        text = "Sorry, I can't respond to that at the moment. Plese try again later."
        reply_to_message(
            message_id, number, text
        ) if message_type == "text" else send_text(message, number)

    response = jsonify(success=True)
    response.status_code = 200
    return response
