from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Column, Boolean
from pie.database import database, session

class ProcessedMessage(database.base):
    __tablename__ = "processed_messages"
    message_id = Column(BigInteger, primary_key=True)
    is_sent = Column(Boolean, default=False)

    @staticmethod
    def mark_as_sent(message_id: int) -> ProcessedMessage:
        message = ProcessedMessage(message_id=message_id, is_sent=True)
        session.merge(message)  # This will add or update the entry
        session.commit()
        return message

    @staticmethod
    def is_sent(message_id: int) -> bool:
        exists = session.query(ProcessedMessage).filter_by(message_id=message_id, is_sent=True).scalar()
        return exists is not None