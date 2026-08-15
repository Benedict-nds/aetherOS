type StatusBadgeProps = {
    status: 'healthy' | 'low' | 'critical';
    children: React.ReactNode;
}

const StatusBadge = ({ status, children }: StatusBadgeProps) => {
    return <div className={`status-badge ${status}`}>{children}</div>;
}

export default StatusBadge;