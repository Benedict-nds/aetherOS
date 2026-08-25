from sqlalchemy.orm import Session

from app.modules.dashboard.schemas import DashboardSummary, TodaySalesSummary


def get_dashboard_summary(_db: Session) -> DashboardSummary:
    # Placeholder until inventory, sales, and purchase-order models exist (BE-004+).
    return DashboardSummary(
        today_sales=TodaySalesSummary(amount=0, currency="GHS"),
        low_stock_count=0,
        expiring_soon_count=0,
        open_orders_count=0,
    )
