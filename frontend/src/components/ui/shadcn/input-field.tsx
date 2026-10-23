import type { ComponentProps } from 'react'
import { Field, FieldLabel } from './field'
import { Input } from './input'

type InputFieldProps = {
  label: string
  name: string
  type?: 'text' | 'email' | 'password'
  placeholder?: string
  value?: string
  onChange?: ComponentProps<'input'>['onChange']
}

export function InputField({ label, name, type = 'text', placeholder, value, onChange }: InputFieldProps) {
  return (
    <Field>
      <FieldLabel htmlFor={name}>{label}</FieldLabel>
      <Input
        id={name}
        name={name}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
      />
    </Field>
  )
}
