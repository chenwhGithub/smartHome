import sys
import base64
import requests


def get_wave(fname):
    with open(fname, "rb") as infile:
        return base64.b64encode(infile.read())


endpoint = "https://snowboy.kitt.ai/api/v1/train/"


############# MODIFY THE FOLLOWING #############
token = "1699772cce0c6eb81e3321fb2fb96b741f0b46fa"
hotword_name = "xiaohong"
language = "zh"
age_group = "20_29"
gender = "M"
microphone = "USB microphone"
############### END OF MODIFY ##################

if __name__ == "__main__":
    try:
        [_, wav1, wav2, wav3, out] = sys.argv
    except ValueError:
        print("Usage: python3 training_service.py xiaohong1.wav xiaohong2.wav xiaohong3.wav xiaohong.pmdl")
        sys.exit()

    data = {
        "name": hotword_name,
        "language": language,
        "age_group": age_group,
        "gender": gender,
        "microphone": microphone,
        "token": token,
        "voice_samples": [
            {"wave": get_wave(wav1)},
            {"wave": get_wave(wav2)},
            {"wave": get_wave(wav3)}
        ]
    }

    response = requests.post(endpoint, json=data)
    if response.ok:
        with open(out, "wb") as outfile:
            outfile.write(response.content)
        print("Saved model to '%s'." % out)
    else:
        print("Request failed.")
        print(response.text)
