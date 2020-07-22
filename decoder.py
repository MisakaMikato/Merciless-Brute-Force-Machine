import base64
import hashlib


def encode64(s: bytes):
    return base64.b64encode(s).decode()


def decode64(s):
    return base64.b64decode(s)


def calMD5(s: bytes):
    m = hashlib.md5()
    m.update(s)
    return encode64(m.digest())


def set_passwd(passwd: str, challenge: str):
    challenge = decode64(challenge)
    passwd = b"0" + passwd.encode() + challenge
    return calMD5(passwd)


if __name__ == "__main__":
    print(set_passwd('Admin@123', 'AgAAANMe8jCnAiRLKabObA=='))
