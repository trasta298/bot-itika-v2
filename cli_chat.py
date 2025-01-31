#!/usr/bin/env python3

import os
import sys
from chat import get_response


def main():
    print(
        "一華（いちか）とのチャットを開始します。終了するには 'exit' または 'quit' と入力してください。"
    )
    print("=" * 50)
    print(
        "一華: こんにちは！私は一華（いちか）です！どのようなお手伝いができますか？ 💫"
    )

    # デバッグ用のユーザーID
    user_id = os.environ.get("DEBUG_USER_ID", "cli_user")

    while True:
        try:
            # 入力プロンプトを表示
            user_input = input("\nあなた: ").strip()

            # 終了コマンドの確認
            if user_input.lower() in ["exit", "quit"]:
                print("\n一華: お話ありがとうございました！またお話しましょうね！ 👋")
                break

            # 空の入力をスキップ
            if not user_input:
                continue

            # 応答を取得して表示
            response = get_response(user_input, user_id)
            print(f"\n一華: {response}")

        except KeyboardInterrupt:
            print("\n\n一華: 中断されました。お話ありがとうございました！ 👋")
            break
        except Exception as e:
            print(f"\nエラーが発生しました: {str(e)}")
            print("もう一度お試しください。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {str(e)}")
        sys.exit(1)
