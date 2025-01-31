import os
from dataclasses import dataclass
from typing import Final, List

import httpx

BOT_ACCESS_TOKEN: Final[str] = os.environ["BOT_ACCESS_TOKEN"]


@dataclass
class MessageStamp:
    userId: str
    stampId: str
    count: int
    createdAt: str
    updatedAt: str


@dataclass
class Message:
    id: str
    userId: str
    channelId: str
    content: str
    createdAt: str
    updatedAt: str
    pinned: bool
    stamps: List[MessageStamp]
    threadId: str | None

    @classmethod
    def from_dict(cls, data: dict):
        data = data.copy()
        data["stamps"] = [MessageStamp(**stamp) for stamp in data["stamps"]]
        return cls(**data)


@dataclass
class MessageSearchResult:
    totalHits: int
    hits: List[Message]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            totalHits=data["totalHits"],
            hits=[Message(**msg) for msg in data["hits"]],
        )


def search_messages(
    *,
    word: str | None = None,
    after: str | None = None,
    before: str | None = None,
    channel_id: str | None = None,
    to_user_id: str | None = None,
    from_user_id: str | None = None,
    citation: str | None = None,
    bot: bool | None = False,
    has_url: bool | None = None,
    has_attachments: bool | None = None,
    has_image: bool | None = None,
    has_video: bool | None = None,
    has_audio: bool | None = None,
    limit: int = 10,
    offset: int = 0,
    sort: str = "createdAt",
) -> MessageSearchResult:
    """
    traQのメッセージを検索します。

    Args:
        word (str, optional): 検索ワード
        after (str, optional): 指定日時より後のメッセージを検索 (ISO 8601形式)
        before (str, optional): 指定日時より前のメッセージを検索 (ISO 8601形式)
        channel_id (str, optional): チャンネルUUID
        to_user_id (str, optional): メンション先ユーザーUUID
        from_user_id (str, optional): 投稿者UUID
        citation (str, optional): 引用元メッセージUUID
        bot (bool, optional): Botからのメッセージかどうか
        has_url (bool, optional): URLを含むメッセージかどうか
        has_attachments (bool, optional): 添付ファイルを含むメッセージかどうか
        has_image (bool, optional): 画像を含むメッセージかどうか
        has_video (bool, optional): 動画を含むメッセージかどうか
        has_audio (bool, optional): 音声ファイルを含むメッセージかどうか
        limit (int, optional): 取得する最大件数 (1-100)
        offset (int, optional): 取得開始位置 (0-9900)
        sort (str, optional): ソート順 (-createdAt, createdAt, -updatedAt, updatedAt)

    Returns:
        MessageSearchResult: 検索結果
    """
    url = "https://q.trap.jp/api/v3/messages"

    params = {
        "word": word,
        "after": after,
        "before": before,
        "in": channel_id,
        "to": to_user_id,
        "from": from_user_id,
        "citation": citation,
        "bot": bot,
        "hasURL": has_url,
        "hasAttachments": has_attachments,
        "hasImage": has_image,
        "hasVideo": has_video,
        "hasAudio": has_audio,
        "limit": limit,
        "offset": offset,
        "sort": sort,
    }

    # Noneの値を持つパラメータを削除
    params = {k: v for k, v in params.items() if v is not None}

    headers = {
        "Authorization": f"Bearer {BOT_ACCESS_TOKEN}",
    }

    r = httpx.get(url, params=params, headers=headers)
    r.raise_for_status()

    return MessageSearchResult.from_dict(r.json())


def edit_traq_message(text: str, message_id: str) -> None:
    url: str = f"https://q.trap.jp/api/v3/messages/{message_id}"
    data: dict = {"content": text, "embed": True}
    headers: dict = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BOT_ACCESS_TOKEN}",
    }
    r = httpx.put(url, json=data, headers=headers)
    r.raise_for_status()


def post_to_traq(text: str, channel_id: str) -> Message:
    url: str = f"https://q.trap.jp/api/v3/channels/{channel_id}/messages"
    data: dict = {"content": text, "embed": True}
    headers: dict = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BOT_ACCESS_TOKEN}",
    }
    r = httpx.post(url, json=data, headers=headers)
    r.raise_for_status()
    j = r.json()
    return Message.from_dict(j)


if __name__ == "__main__":

    res = search_messages(word="一華", limit=10, sort="createdAt", before="2022-01-31T00:00:00Z")
    print(res.hits)
