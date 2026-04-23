import asyncio
from datetime import date, time

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.chat_message import ChatMessage
from app.models.hcp_interaction import HCPInteraction


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(HCPInteraction).where(HCPInteraction.hcp_name == "Dr. Sharma"))
        if existing.scalar_one_or_none():
            return
        session.add_all(
            [
                HCPInteraction(
                    hcp_name="Dr. Sharma",
                    interaction_type="Meeting",
                    interaction_date=date(2025, 4, 19),
                    interaction_time=time(16, 30),
                    attendees=["Dr. Sharma", "Aivoa Rep"],
                    topics_discussed=["OncBoost Phase III efficacy", "Patient selection"],
                    materials_shared=["OncBoost Phase III PDF"],
                    samples_distributed=[],
                    sentiment="positive",
                    outcomes="Interested in reviewing trial data with oncology team.",
                    follow_up_actions=["Schedule follow-up meeting in 2 weeks"],
                    ai_suggested_followups=["Send OncBoost Phase III PDF", "Invite Dr. Sharma to advisory board list"],
                    status="completed",
                ),
                HCPInteraction(
                    hcp_name="Dr. Sharma",
                    interaction_type="Call",
                    interaction_date=date(2025, 3, 28),
                    interaction_time=time(11, 15),
                    attendees=["Dr. Sharma"],
                    topics_discussed=["Safety profile", "Dosing workflow"],
                    materials_shared=["Safety overview"],
                    samples_distributed=["Starter sample kit"],
                    sentiment="neutral",
                    outcomes="Requested more practical dosing material.",
                    follow_up_actions=["Share dosing guide"],
                    ai_suggested_followups=[],
                    status="completed",
                ),
            ]
        )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
