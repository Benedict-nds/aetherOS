from sqlalchemy.orm import Session

from app.modules.dashboard.schemas import DashboardSummary, TodaySalesSummary
from app.modules.reports.service import count_expiring_soon, get_low_stock_report
from app.modules.sales.service import sum_today_sales_amount


def get_dashboard_summary(db: Session) -> DashboardSummary:
    low_stock_rows = get_low_stock_report(db)

    return DashboardSummary(
        today_sales=TodaySalesSummary(
            amount=sum_today_sales_amount(db),
            currency="GHS",
        ),
        low_stock_count=len(low_stock_rows),
        expiring_soon_count=count_expiring_soon(db),
        open_orders_count=0,
    )
