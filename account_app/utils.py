import random
import string

def generate_otp_code():
    return random.randint(100000, 999999)  # تولید کد OTP شش رقمی

def generate_unique_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))  # تولید توکن یکتا 32 کاراکتری



