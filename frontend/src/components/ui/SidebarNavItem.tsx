import { Link } from "react-router-dom";

type SideBarNavItemProps = {
    to: string;
    label: string;
    icon: React.ReactNode;
}

const SideBarNavItem = ({ to, icon, label }: SideBarNavItemProps) => {
    return <Link to={to} className="side-bar-nav-item">
        <div className="side-bar-nav-item-icon">{icon}</div>
        <div className="side-bar-nav-item-label">{label}</div>
    </Link>;
}

export default SideBarNavItem;