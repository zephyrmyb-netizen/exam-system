"""Tests for improved fill_blank and short_answer grading rules."""
from backend.utils import check_fill_blank_answer, check_short_answer_answer


class TestFillBlankGrading:
    def test_single_answer_exact(self):
        assert check_fill_blank_answer("TCP", "TCP") is True
        assert check_fill_blank_answer("TCP", "UDP") is False

    def test_multi_answer_or(self):
        """|| splits into acceptable alternatives."""
        assert check_fill_blank_answer("TCP||传输控制协议", "TCP") is True
        assert check_fill_blank_answer("TCP||传输控制协议", "传输控制协议") is True
        assert check_fill_blank_answer("TCP||传输控制协议", "UDP") is False

    def test_case_insensitive(self):
        assert check_fill_blank_answer("TCP", "tcp") is True
        assert check_fill_blank_answer("Hello", "HELLO") is True

    def test_fullwidth_punctuation(self):
        """Fullwidth commas, spaces, etc. are normalized."""
        assert check_fill_blank_answer("你好，世界", "你好，世界") is True
        assert check_fill_blank_answer("你好，世界", "你好,世界") is True

    def test_whitespace_insensitive(self):
        assert check_fill_blank_answer("  TCP  ", "tcp") is True
        assert check_fill_blank_answer("TCP", "  tcp  ") is True
        assert check_fill_blank_answer("a   b", "a b") is True

    def test_empty_answer(self):
        assert check_fill_blank_answer("", "") is True
        assert check_fill_blank_answer("", "x") is False
        assert check_fill_blank_answer("x", "") is False

    def test_pipe_only_in_correct_answer(self):
        """|| in correct answer is a separator; user answers one alternative."""
        assert check_fill_blank_answer("A||B", "A") is True
        assert check_fill_blank_answer("A||B", "B") is True
        assert check_fill_blank_answer("A||B", "A||B") is False  # user wrote the separator literally


class TestShortAnswerGrading:
    def test_strict_match_legacy(self):
        """Without || or &&, behaves like strict normalized match."""
        assert check_short_answer_answer("hello world", "hello world") is True
        assert check_short_answer_answer("hello world", "hello") is False

    def test_keywords_all_required(self):
        """&& means all keywords must appear."""
        assert check_short_answer_answer("TCP&&连接&&三次握手", "TCP协议通过三次握手建立连接") is True
        assert check_short_answer_answer("TCP&&连接&&三次握手", "TCP连接") is False  # missing 三次握手

    def test_keywords_order_insensitive(self):
        """&& keywords can appear in any order."""
        assert check_short_answer_answer("苹果&&香蕉", "我喜欢香蕉和苹果") is True

    def test_keywords_case_and_fullwidth(self):
        """&& keywords use same normalization."""
        assert check_short_answer_answer("TCP&&握手", "tcp 三次握手过程") is True  # contains tcp and 握手

    def test_alternatives_or(self):
        """|| in short_answer works like fill_blank."""
        assert check_short_answer_answer("方案A||方案B", "方案A") is True
        assert check_short_answer_answer("方案A||方案B", "方案C") is False

    def test_empty_answer(self):
        assert check_short_answer_answer("", "") is True
        assert check_short_answer_answer("", "x") is False
        assert check_short_answer_answer("x", "") is False
