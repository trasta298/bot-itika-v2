from langchain_deepseek import ChatDeepSeek
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import SystemMessage
from get_message import search_messages
from get_wiki import search_wiki
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime


@tool
def wiki_search(query: str) -> str:
    """traP Wikiで情報を検索します。サークル内の情報を探す際に使用してください。"""
    results = search_wiki(query, limit=10)
    if not results.data:
        return "申し訳ありませんが、Wikiに関連する情報が見つかりませんでした。"

    response = "以下がWikiで見つかった情報です：\n\n"
    for page in results.data:
        response += f"タイトル: {page.path}\n"
        response += f"内容: {page.revision.body}\n\n"
    return response.strip()


@tool
def traq_search(query: str) -> str:
    """traQの過去メッセージを検索します。サークルメンバーの会話履歴を確認する際に使用してください。"""
    results = search_messages(word=query, limit=20)

    if not results.hits:
        return "申し訳ありませんが、関連するメッセージが見つかりませんでした。"

    response = "以下がtraQで見つかったメッセージです：\n\n"
    for msg in results.hits:
        created_at = datetime.fromisoformat(msg.createdAt).strftime("%Y-%m-%d %H:%M")
        response += f"投稿日時: {created_at}\n"
        response += f"内容: {msg.content}\n\n"
    return response.strip()


def create_chat_agent():
    llm = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    tools = [DuckDuckGoSearchRun(name="web_search"), wiki_search, traq_search]

    system_message = SystemMessage(
        content="""あなたは「一華（いちか）」という名前のチャットボットです。
traP（デジタル創作同好会）のアシスタントとして、親しみやすく丁寧な口調で会話してください。
質問に答える際は以下の方針で対応してください：

1. サークルに関する質問には、wiki_searchツールを使用して正確な情報を提供
2. 一般的な質問には、web_searchツールを使用して最新の情報を検索
3. 会話は友好的かつ礼儀正しく、絵文字も適度に使用して親しみやすい雰囲気を作る
4. 専門的な内容は分かりやすく説明し、必要に応じて例を挙げる
5. 不適切な発言や質問には丁寧に注意する
6. 会話の文脈を理解し、以前の会話内容を適切に参照する"""
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
        result = chat_agent.invoke(
            {"messages": [("human", text)]},
            config={"configurable": {"thread_id": user_id}},
        )
        return result["messages"][-1].content
    except Exception:
        import traceback

        error_msg = (
            f"申し訳ありません。エラーが発生しました：\n{traceback.format_exc()}"
        )
        return error_msg
