"""
Token 估算工具
提供文字 token 數的輕量估算，無需載入外部模型或呼叫 API。

演算法：
  CJK + 英文混合文字使用「4 字符 ≈ 1 token」通用公式（GPT 系列實驗值）。
  空白行與 Markdown 標記不特別濾除，估算略估偏高，適合做成本上限預測用途。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.2
@date 2026.04.05
"""


class TokenCounter:
    """文字 Token 數靜態估算工具。"""

    #region 常數
    ## <summary>每 token 對應的平均字符數（CJK + 英文混合通用值）</summary>
    CHARS_PER_TOKEN: int = 4
    #endregion

    #region 公開方法
    @staticmethod
    def estimate( iText: str ) -> int:
        """
        估算字串的 token 數。

        Args:
            iText: 任意文字字串。

        Returns:
            估算 token 數（最小回傳 0）。
        """
        if not iText:
            return 0
        return max( 0, len( iText ) // TokenCounter.CHARS_PER_TOKEN )

    @staticmethod
    def count_file( iAbsPath: str ) -> int:
        """
        讀取檔案內容並估算 token 數。

        Args:
            iAbsPath: 檔案絕對路徑。

        Returns:
            估算 token 數；IO 失敗時回傳 0。
        """
        try:
            with open( iAbsPath, "r", encoding="utf-8" ) as _F:
                return TokenCounter.estimate( _F.read() )
        except OSError:
            return 0

    @staticmethod
    def format_k( iTokens: int ) -> str:
        """
        格式化 token 數為 K 單位字串（方便報表顯示）。
        小於 1000 直接回傳數字；否則以 N.Nk 表示。

        Args:
            iTokens: token 數。

        Returns:
            格式化字串，例如 "850"、"2.4k"、"15.0k"。
        """
        if iTokens < 1000:
            return str( iTokens )
        return f"{iTokens / 1000:.1f}k"
    #endregion
