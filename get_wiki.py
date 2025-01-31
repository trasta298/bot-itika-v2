import httpx
from dataclasses import dataclass, field
from typing import List, Optional
import os

wiki_token = os.getenv("WIKI_TOKEN")


@dataclass
class Creator:
    lang: str
    status: int
    admin: bool
    _id: str
    createdAt: str
    name: str
    username: str
    v: int = field(metadata={"name": "__v"})
    image: str = field(default="")

    @classmethod
    def from_dict(cls, data: dict):
        data = data.copy()
        data["v"] = data.pop("__v")
        return cls(**data)


@dataclass
class Revision:
    format: str
    _id: str
    createdAt: str
    path: str
    body: str
    author: Creator
    v: int = field(metadata={"name": "__v"})

    @classmethod
    def from_dict(cls, data: dict):
        data = data.copy()
        data["v"] = data.pop("__v")
        data["author"] = Creator.from_dict(data["author"])
        return cls(**data)


@dataclass
class WikiPage:
    _id: str
    _score: float
    _source: dict
    status: str
    grant: int
    grantedUsers: List[str]
    liker: List[str]
    seenUsers: List[str]
    commentCount: int
    extended: str
    createdAt: str
    path: str
    creator: Creator
    lastUpdateUser: str
    updatedAt: str
    redirectTo: Optional[str]
    v: int = field(metadata={"name": "__v"})
    revision: Revision
    bookmarkCount: int

    @classmethod
    def from_dict(cls, data: dict):
        data = data.copy()
        data["v"] = data.pop("__v")
        data["creator"] = Creator.from_dict(data["creator"])
        data["revision"] = Revision.from_dict(data["revision"])
        return cls(**data)


@dataclass
class Meta:
    took: int
    total: int
    results: int


@dataclass
class WikiResponse:
    meta: Meta
    data: List[WikiPage]
    ok: bool

    @classmethod
    def from_dict(cls, data: dict):
        data["data"] = [WikiPage.from_dict(page) for page in data["data"]]
        return cls(**data)


def search_wiki(query: str, limit: int = 10) -> WikiResponse:
    """
    traP Wikiの検索を行う関数

    Args:
        query (str): 検索クエリ
        limit (int): 検索結果の最大件数（デフォルト: 10）

    Returns:
        dict: 検索結果のJSON
    """
    params = {"q": query, "limit": limit, "access_token": wiki_token, "user": "trasta"}

    with httpx.Client() as client:
        r = client.get("https://wiki.trap.jp/_api/search", params=params)
        return WikiResponse.from_dict(r.json())


if __name__ == "__main__":
    res = search_wiki("部室")
    print(res.data[0].revision.body)
