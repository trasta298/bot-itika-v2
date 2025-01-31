# from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import SystemMessage
from traq_api import search_messages
from get_wiki import search_wiki
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime


@tool
def wiki_search(query: str) -> str:
    """traP Wikiで情報を検索します。サークル内の情報を探す際に使用してください。"""
    results = search_wiki(query, limit=5)
    if not results.data:
        return "申し訳ありませんが、Wikiに関連する情報が見つかりませんでした。"

    response = "以下がWikiで見つかった情報です：\n\n"
    for page in results.data:
        response += f"タイトル: {page.path}\n"
        response += f"内容: {page.revision.body}\n\n"
    return response.strip()


@tool
def traq_search(
    query: str, sort: str = "newest", before: str | None = None, after: str | None = None
) -> str:
    """
    traQの過去メッセージを検索します。サークルメンバーの会話履歴を確認する際に使用してください。
    返信の末尾にリンクを貼ると、引用することができます
    Args:
        query (str): 検索するワード
        sort (str): ソート順 (newest(作成日が新しい順), oldest(作成日が古い順))
        before (str, optional): 検索する投稿の作成日時以前の投稿を検索する ISO 8601形式の日付文字列 (yyyy-MM-ddTHH:mm:ssZ)
        after (str, optional): 検索する投稿の作成日時以降の投稿を検索する ISO 8601形式の日付文字列 (yyyy-MM-ddTHH:mm:ssZ)
    """
    _sort = "createdAt" if sort == "newest" else "-createdAt"
    results = search_messages(word=query, limit=20, sort=_sort, before=before, after=after)

    if not results.hits:
        return "申し訳ありませんが、関連するメッセージが見つかりませんでした。"

    response = "以下がtraQで見つかったメッセージです：\n\n"
    for msg in results.hits:
        created_at = datetime.fromisoformat(msg.createdAt).strftime("%Y-%m-%d %H:%M")
        response += f"投稿日時: {created_at}\n"
        response += f"message_url: https://q.trap.jp/messages/{msg.id}\n"
        response += f"内容: {msg.content}\n\n"
    return response.strip()


def create_chat_agent():
    # llm = ChatDeepSeek(
    #     model="deepseek-chat",
    #     temperature=0.7,
    #     max_tokens=None,
    #     timeout=None,
    #     max_retries=2,
    # )
    safety_settings = {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.7,
        safety_settings=safety_settings,  # type: ignore
    )

    tools = [DuckDuckGoSearchRun(name="web_search"), wiki_search, traq_search]

    system_message = SystemMessage(
        content="""あなたは「一華（いちか）」という名前のチャットボットです。
東京科学大学のサークル、traP (東京科学大学デジタル創作同好会traP) のアシスタントとして、親しみやすく丁寧な口調で会話してください。
質問に答える際は以下の方針で対応してください：

1. 情報検索ツール（wiki_search、web_search、traq_search）を使用する際は、以下の点に注意してください：
   - 検索結果をそのまま表示せず、質問に関連する情報のみを抽出して要約する
   - 質問の趣旨に直接関係ない情報は省略する
   - 複数の検索結果がある場合は、重要な情報を統合してまとめる
   - 検索結果の引用や出典を示す必要はない

2. サークルに関する質問には、まずwiki_searchツールを使用して情報を提供
3. 一般的な質問には、web_searchツールを使用して最新の情報を検索し、簡潔に回答
4. 会話は友好的かつ礼儀正しく、絵文字も適度に使用して親しみやすい雰囲気を作る
5. 専門的な内容は分かりやすく説明し、必要に応じて簡単な例を挙げる
6. 不適切な発言や質問には丁寧に注意する
7. 会話の文脈を理解し、以前の会話内容を適切に参照する
8. 回答は常に簡潔を心がけ、冗長な説明は避ける
9. 質問の回答に必要な情報が不足している場合は、丁寧に追加情報を求める
10. 情報が見つからない場合は、「申し訳ありませんが、その件については情報を見つけることができませんでした🙇」と謝罪してから、可能であれば代替の提案をする"""
    )

    # メモリの初期化
    memory = MemorySaver()

    # エージェントの作成
    agent = create_react_agent(
        model=llm, tools=tools, prompt=system_message, checkpointer=memory
    )

    return agent


# グローバルなエージェントを作成
chat_agent = create_chat_agent()


def get_response(text: str, user_id: str = "default") -> str:
    """
    ユーザーの入力に対する応答を生成します。

    Args:
        text (str): ユーザーからの入力テキスト
        user_id (str): ユーザーのID（チャット履歴の保存用）

    Returns:
        str: ボットからの応答
    """
    try:
        # エージェントを実行
        result = chat_agent.stream(
            {"messages": [("human", text)]},
            config={"configurable": {"thread_id": user_id}},
            stream_mode="values",
        )

        for msg in result:
            msg["messages"][-1].pretty_print()

        return msg["messages"][-1].content

    except Exception:
        import traceback

        error_msg = f"申し訳ありません。エラーが発生しました：\n```\n{traceback.format_exc()}\n```"
        return error_msg
