type InputFieldProps = {
    label: string;
    name: string;
    type?: 'text' | 'email' | 'password';
    placeholder: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const InputField = ({ label, name, type = 'text', placeholder, value, onChange }: InputFieldProps) => {
    return <div className="input-field">
        <label htmlFor={name}>{label}</label>
        <input type={type} name={name} placeholder={placeholder} value={value} onChange={onChange} />
    </div>;
}

export default InputField;