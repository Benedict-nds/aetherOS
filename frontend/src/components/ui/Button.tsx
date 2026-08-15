type ButtonProps = {
    children: React.ReactNode;
    onClick?: () => void;
    variant?: 'primary' | 'secondary' | 'ghost';
    type?: 'button' | 'submit';
    disabled?: boolean;
}

const Button = ({ children, onClick, variant = 'primary', type = 'button', disabled = false }: ButtonProps) => {
     return <button className={`button ${variant}`} onClick={onClick} disabled={disabled} type={type}>{children}</button>;
}

export default Button;