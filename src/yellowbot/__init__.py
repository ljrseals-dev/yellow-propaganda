"""The Yellow Press: a mythic-tabloid chatbot with a cited record."""

from .bot import YellowBot, Reply
from .knowledge import KnowledgeBase

__version__ = "0.2.0"
__all__ = ["YellowBot", "Reply", "KnowledgeBase"]
