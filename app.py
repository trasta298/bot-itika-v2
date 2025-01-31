import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Final, Optional

from chat import get_response
from traq_api import post_to_traq

BOT_ACCESS_TOKEN: Final[str] = os.environ["BOT_ACCESS_TOKEN"]


def is_token_valid(token: Optional[str]) -> bool:
    return token == os.environ.get("BOT_VERIFICATION_TOKEN")


class BotHandler(BaseHTTPRequestHandler):

    def do_POST(self) -> None:
        content_length: int = int(self.headers["Content-Length"])

        token: Optional[str] = self.headers.get("X-TRAQ-BOT-TOKEN")
        if token is None:
            print("No X-TRAQ-BOT-TOKEN")
            self.send_error(400)
            self.end_headers()
            return

        event: Optional[str] = self.headers.get("X-TRAQ-BOT-EVENT")
        if event is None:
            print("No X-TRAQ-BOT-EVENT")
            self.send_error(400)
            self.end_headers()
            return

        body: bytes = self.rfile.read(content_length)
        try:
            data: dict = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            print("JSONDecodeError")
            self.send_error(400)
            self.end_headers()
            return

        if is_token_valid(token):
            self.handle_event(data, event)
        else:
            self.send_error(401)
            self.end_headers()

    def handle_event(self, data: dict, event: str) -> None:
        if event == "PING":
            self.send_response(204)
            self.end_headers()
        elif event == "MESSAGE_CREATED":
            self.handle_message_created(data)
        else:
            self.send_response(501)
            self.end_headers()

    def handle_message_created(self, data):
        text: str = data["message"]["plainText"]
        channel_id: str = data["message"]["channelId"]

        if data["message"]["user"]["bot"]:
            print("message from bot")
            self.send_response(204)
            self.end_headers()
            return

        text = re.sub(r"^@[Bb][Oo][Tt]_[Ii][Tt][Ii][Kk][Aa]\s*", "", text)

        # チャットボットの応答を生成
        res = get_response(text)

        post_to_traq(res, channel_id)
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":

    HOST: Final[str] = "0.0.0.0"
    PORT: Final[int] = 8080

    with HTTPServer((HOST, PORT), BotHandler) as server:
        print("serving at port", PORT)
        server.serve_forever()
