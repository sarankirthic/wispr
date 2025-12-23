import asyncio
import json
from flask import Blueprint, request, jsonify, Response
from app import app, db
from flask_cors import CORS
import uuid
from deepgram import DeepgramClient
from config import Config
from app.models import Transcript


api = Blueprint('api', __name__)
CORS(api)

deepgram = DeepgramClient(api_key=Config.DEEPGRAM_API_KEY)


@api.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


@api.route('/transcripts/<session_id>', methods=['GET'])
def get_transcripts(session_id):
    user_id = request.headers.get("X-User_ID", "anonymous")
    try:
        transcripts = (
            Transcript.query.filter_by(session_id=session_id, user_id=user_id)
            .order_by(Transcript.created_at.desc())
            .limit(50)
            .all()
        )
        return jsonify([transcript.to_dict() for transcript in transcripts]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch transcript"}), 500


@api.route('/ws/transcribe')
def transcribe_audio():
    session_id = request.headers.get('X-Session_ID', str(uuid.uuid4()))
    user_id = request.headers.get('X-User_id')

    async def handle_websocket(websocket):
        recording = False
        try:
            connection = deepgram.listen.v("1").live({
                "model": "nova-2",
                "language": "en-US",
                "smart_format": True,
                "punctuate": True
            })

            def on_message(self, result, **kwargs):
                nonlocal recording
                if result.get("channel", {}).get("alternatives"):
                    transcript = result["channel"]["alternatives"][0]["transcript"]
                    if transcript and recording:
                        asyncio.create_task(websocket.send(
                            json.dump({
                                "type": "transcript",
                                "text": transcript,
                                "is_final": result.get("is_final", False),
                            })
                        ))

                        if result.get("is_final"):
                            transcript_obj = Transcript(
                                user_id=user_id,
                                session_id=session_id,
                                transcript_text=transcript,
                                extra_data={"source": "live"}
                            )
                            db.session.add(transcript_obj)
                            db.session.commit()

            def on_error(self, result, **kwargs):
                asyncio.create_task(websocket.send(json.dump({
                    "type": "error",
                    "message": str(result)
                })))

            connection.register_handler(connection.event.ON_MESSAGE, on_message)
            connection.register_handler(connection.event.ON_ERROR, on_error)

            await connection.keepalive()

            async for message in websocket:
                data = json.loads(message)

                if data["type"] == "start_recording":
                    recording = True
                    await websocket.send(json.dumps({
                        "type": "status",
                        "state": "recording",
                        "session_id": session_id
                    }))

                elif data["type"] == "stop_recording":
                    recording = False
                    await websocket.send(json.dumps({
                        "type": "status",
                        "state": "stopped"
                    }))

                elif data["type"] == "audio" and recording:
                    connection.send(data["audio"])

                elif data["type"] == "close":
                    break

        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Server error: {str(e)}"
            }))

        finally:
            await connection.finish()

    return Response(
        asyncio.run(handle_websocket),
        mimetype='text/plain'
    )


@api.route('/transcribe', methods=['POST'])
def file_transcribe():
    session_id = request.headers.get('X-Session-ID', str(uuid.uuid4()))
    user_id = request.headers.get('X-User-ID', 'anpnymous')

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file"}), 400

    try:
        audio_file = request.files['audio']
        source = {
            "buffer": audio_file.stream,
            "mimetype": "audio/wav"
        }

        options = {
            "model": "nova-2",
            "smart_format": True
        }

        response = deepgram.listen.prerecorded.v("1").transcribe_file(source, options)
        transcript_text = response["results"]["channels"][0]["alternatives"][0]["transcript"]

        transcript = Transcript(
            user_id=user_id,
            session_id=session_id,
            transcript_text=transcript_text,
            extra_data={"method": "file_upload"}
        )
        db.session.add(transcript)
        db.session.commit()

        return jsonify({
            "session_id": session_id,
            "transcript": transcript_text,
            "transcript_id": transcript.id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
