# InspireWorks Plivo IVR Demo

A Flask-based demo IVR system built for the InspireWorks technical assignment. The app uses Plivo's Voice API to place an outbound call, authenticate the receiver with a 4-digit OTP, and then guide them through a two-level IVR menu.

## What This App Demonstrates

- Outbound calling with the Plivo Voice API
- OTP authentication using DTMF keypad input
- Multi-level IVR flow using Plivo XML
- Language selection in English and Spanish
- Branching call logic for audio playback or live associate transfer
- Simple browser UI to trigger outbound calls

## Call Flow

1. Open the web page and enter the receiver phone number.
2. The app places an outbound call from your Plivo number.
3. When the receiver answers, the IVR asks for a 4-digit OTP.
4. The OTP is checked against the hardcoded birthdate value in `VALID_OTP`.
5. If the OTP is wrong, the caller is prompted again.
6. If the OTP is correct, the caller enters the language menu:
   - Press `1` for English
   - Press `2` for Spanish
7. After choosing a language, the caller enters the action menu:
   - Press `1` to play a short audio message
   - Press `2` to connect to the live associate number

## Tech Stack

- Python
- Flask
- Plivo Python SDK
- Plivo XML
- python-dotenv
- HTML, CSS, and JavaScript for the call trigger page

## Project Structure

```txt
.
|-- app.py                 # Flask app, Plivo API call trigger, and IVR routes
|-- requirements.txt       # Python dependencies
|-- .env.example           # Example environment variables
|-- .gitignore             # Files ignored by git
|-- templates/
|   `-- index.html         # Simple frontend for starting outbound calls
`-- check_keys.py          # Local helper script, ignored by git
```

## Prerequisites

Before running the project, make sure you have:

- Python 3.10 or newer
- A Plivo account
- A Plivo voice-enabled phone number
- Plivo Auth ID and Auth Token
- ngrok or another public tunneling service
- A phone number to receive the test call

## Environment Variables

Create a `.env` file in the project root. You can copy the example file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then fill in the values:

```env
PLIVO_AUTH_ID=your_auth_id_here
PLIVO_AUTH_TOKEN=your_auth_token_here
PLIVO_FROM_NUMBER=+1XXXXXXXXXX
VALID_OTP=1503
ASSOCIATE_NUMBER=+91XXXXXXXX12
BASE_URL=https://your-ngrok-url.ngrok.io
```

### Variable Reference

| Variable | Description |
| --- | --- |
| `PLIVO_AUTH_ID` | Your Plivo Auth ID from the Plivo console |
| `PLIVO_AUTH_TOKEN` | Your Plivo Auth Token from the Plivo console |
| `PLIVO_FROM_NUMBER` | Your Plivo phone number in international format |
| `VALID_OTP` | The 4-digit OTP, using birthdate in DDMM format |
| `ASSOCIATE_NUMBER` | Number used for live associate transfer |
| `BASE_URL` | Public HTTPS URL that Plivo can use to reach this Flask app |

Important: Do not commit your `.env` file. It contains private credentials and is already listed in `.gitignore`.

## Setup Instructions

1. Clone or download this project.

2. Create a virtual environment.

```bash
python -m venv .venv
```

3. Activate the virtual environment.

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

4. Install dependencies.

```bash
pip install -r requirements.txt
```

5. Create and configure the `.env` file.

```bash
cp .env.example .env
```

Update the values in `.env` with your Plivo credentials, Plivo number, OTP, associate number, and ngrok URL.

6. Start the Flask app.

```bash
python app.py
```

By default, the app runs at:

```txt
http://127.0.0.1:5000
```

7. Start ngrok in a separate terminal.

```bash
ngrok http 5000
```

8. Copy the HTTPS forwarding URL from ngrok and set it as `BASE_URL` in `.env`.

Example:

```env
BASE_URL=https://abc123.ngrok-free.app
```

9. Restart the Flask app after changing `.env`.

## Running the Demo

1. Open the local web UI:

```txt
http://127.0.0.1:5000
```

2. Enter the receiver phone number with country code.

Example:

```txt
+91XXXXXXXXXX
```

3. Click `Call Now`.

4. Answer the incoming call.

5. Enter a wrong OTP first to demonstrate retry behavior.

6. Enter the correct OTP from `VALID_OTP`.

7. Select a language:

```txt
1 = English
2 = Spanish
```

8. Choose an action:

```txt
1 = Play audio message
2 = Connect to live associate
```

## Routes

| Route | Method | Purpose |
| --- | --- | --- |
| `/` | `GET` | Shows the call trigger web page |
| `/make-call` | `POST` | Starts an outbound call using Plivo |
| `/answer` | `POST` | First webhook after the receiver answers |
| `/verify-otp` | `POST` | Verifies the OTP entered by the caller |
| `/language-menu` | `POST` | Handles language selection |
| `/action-menu` | `GET`, `POST` | Handles the second-level IVR menu |
| `/handle-action` | `GET`, `POST` | Plays audio or dials the associate number |

## Live Associate Number

The provided live associate number is:

```txt
02XXXXXX12
```

For Plivo, configure it in international format:

```env
ASSOCIATE_NUMBER=+91XXXXXXXX12
```

## Audio Playback

When the caller presses `1` in the action menu, the app plays a publicly hosted sample MP3:

```txt
https://s3.amazonaws.com/plivocloud/Trumpet.mp3
```

After the audio plays, the app speaks a goodbye message and hangs up.

## Testing Checklist

Use this checklist for the demo video:

- Start Flask locally.
- Start ngrok and confirm `BASE_URL` is updated.
- Open the browser UI.
- Place an outbound call to the receiver phone number.
- Answer the call.
- Enter an incorrect OTP first.
- Enter the correct OTP.
- Press `1` for English.
- Press `1` to play the audio message.
- Repeat the call.
- Enter the correct OTP.
- Press `1` for English or `2` for Spanish.
- Press `2` to connect to the live associate number.

## Troubleshooting

### The call is not placed

- Confirm `PLIVO_AUTH_ID` and `PLIVO_AUTH_TOKEN` are correct.
- Confirm `PLIVO_FROM_NUMBER` is a valid Plivo number.
- Confirm the receiver number starts with `+` and includes the country code.
- Check the Flask terminal for API errors.

### The call connects but the IVR does not play

- Confirm ngrok is running.
- Confirm `BASE_URL` is the current ngrok HTTPS URL.
- Restart Flask after changing `.env`.
- Make sure Plivo can reach `BASE_URL/answer`.

### OTP keeps failing

- Confirm the value in `.env`:

```env
VALID_OTP=1503
```

- Enter exactly four digits during the call.

### Live associate transfer disconnects

- Confirm `ASSOCIATE_NUMBER` uses international format.
- For the provided number, use `+91XXXXXXXX12`.
- Check whether the destination number is reachable from Plivo.
- Check Plivo logs in the Plivo console for call failure details.

## Security Notes

- Never commit `.env`.
- Use `.env.example` to show required variables without exposing real credentials.
- Rotate Plivo credentials if they are accidentally shared.

## Assignment Deliverables Covered

- Working Flask application to trigger outbound calls
- OTP authentication with DTMF input
- Multi-level IVR menu
- English and Spanish language branches
- Audio playback branch
- Live associate transfer branch
- README setup and demo instructions
