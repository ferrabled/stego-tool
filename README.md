# stego-tool

## Installation

1. Clone this repository:
```bash
$> git clone https://github.com/davidmohedanovazquez/stego-tool.git
```

2. Install all the requirements:
```bash
$> pip3 install -r requirements.txt
```


## Usage

- Hide a message on an image:
```bash
$> python3 script.py -e <input_image_filename>.png [-o <output_image_filename>.png] [-p <password>]
```

- Get a message from an image:
```bash
python3 script.py -d <input_image_filename>.png [-n <pixel_number>] [-p <password>]
```

- Create a video from an image and an audio:
```bash
$> python3 create_video.py <input_image_filename>.png <input_audio_filename>.mp3 <output_video_filename>.avi
```

- Get a frame from the video and save it as a PNG image:
```bash
$> python3 get_frames.py <input_video_filename>.avi
```


## Accepted formats

- Image format: PNG
- Audio format: MP3
- Video format: AVI
