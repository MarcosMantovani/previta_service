def format_cnpj(cnpj):
    # Remove any non-numeric characters from the input string
    cnpj_digits = ''.join(filter(str.isdigit, cnpj))

    # Format the CNPJ with punctuation
    formatted_cnpj = f"{cnpj_digits[:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}/{cnpj_digits[8:12]}-{cnpj_digits[12:]}"

    return formatted_cnpj


def format_cpf(cpf):
    # Remove any non-numeric characters from the input string
    cpf_digits = ''.join(filter(str.isdigit, cpf))

    # Format the CPF with punctuation
    formatted_cpf = f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}"

    return formatted_cpf


def format_phone_number(phone_number):
    return phone_number.as_national if phone_number else None