"""
OTP model for temporary OTP storage
"""

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class OTP(Base):
    """OTP model for storing temporary OTP codes"""

    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(255), nullable=False)  # Hashed OTP
    purpose = Column(String(50), nullable=False)  # 'registration' or 'login'
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_otp_email", "email"),
        Index("idx_otp_expires_at", "expires_at"),
        Index("idx_otp_email_purpose", "email", "purpose"),
    )

    def __repr__(self):
        return f"<OTP(id={self.id}, email={self.email}, purpose={self.purpose})>"
