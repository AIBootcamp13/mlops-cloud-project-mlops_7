import re


def convert_camel_to_snake(name):
    # 대문자 앞에 언더스코어 추가하고 소문자로 변환
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
    # 앞뒤 공백 제거
    return s2.strip()
