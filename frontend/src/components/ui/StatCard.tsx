type StatCardProps = {
    label: string;
    value: string | number;
    hint: string;
}

const StatCard = ({ label, value, hint }: StatCardProps) => {
    return <div className="stat-card">
        <div className="stat-card-label">{label}</div>
        <div className="stat-card-value">{value}</div>
        <div className="stat-card-hint">{hint}</div>
    </div>;
}

export default StatCard;