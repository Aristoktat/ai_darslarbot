from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Subscription, Plan, User
from datetime import datetime, timedelta

async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    stmt = select(Subscription).where(
        Subscription.user_id == user_id,
        Subscription.is_active == True,
        (Subscription.end_date > datetime.utcnow()) | (Subscription.end_date == None)
    ).order_by(Subscription.end_date.desc())
    
    result = await session.execute(stmt)
    return result.scalars().first()

async def create_subscription(session: AsyncSession, user_id: int, plan_id: int) -> Subscription:
    # 1. Get plan details
    plan_stmt = select(Plan).where(Plan.id == plan_id)
    plan_res = await session.execute(plan_stmt)
    plan = plan_res.scalar_one_or_none()
    
    if not plan:
        raise ValueError("Plan not found")

    # 2. Calculate end date
    start_date = datetime.utcnow()
    end_date = None
    if plan.duration_days:
        end_date = start_date + timedelta(days=plan.duration_days)
    
    # 3. Create subscription
    # Deactivate old active subs? Maybe not necessary if logic handles "latest valid".
    # But usually good to close previous ones if they overlap or just extend?
    # For now, let's just create a new one.
    
    new_sub = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    session.add(new_sub)
    await session.commit()
    await session.refresh(new_sub)
    return new_sub

async def disable_expired_subscriptions(session: AsyncSession):
    # Find active subs where end_date < now
    stmt = select(Subscription).where(
        Subscription.is_active == True,
        Subscription.end_date != None,
        Subscription.end_date < datetime.utcnow()
    )
    result = await session.execute(stmt)
    expired_subs = result.scalars().all()
    
    for sub in expired_subs:
        sub.is_active = False
    
    await session.commit()
    return expired_subs
