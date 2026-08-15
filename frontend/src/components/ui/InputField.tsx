import type { ChangeEvent } from 'react'

type InputFieldProps = {
  label: string
  name: string
  type?: 'text' | 'email' | 'password'
  placeholder?: string
  value?: string
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void
}

export const InputField = ({
  label,
  name,
  type = 'text',
  placeholder,
  value,
  onChange,
}: InputFieldProps) => {
  return (
    <div className="input-field">
      <label htmlFor={name}>{label}</label>
      <input
        id={name}
        name={name}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
      />
    </div>
  )
}
