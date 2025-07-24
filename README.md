# Safe Space App

## Overview
Safe Space is a Flask-based web application designed to provide a supportive environment for users seeking mental health assistance. The application integrates OpenAI's chat functionality to offer users a compassionate and responsive chat experience.

## Project Structure
```
safe-space-app
├── app.py                  # Main application file for the Flask app
├── requirements.txt        # Python dependencies required for the project
├── README.md               # Documentation for the project
├── templates               # HTML templates for the application
│   ├── base.html           # Base template with common structure
│   ├── home.html           # Home page template
│   ├── login.html          # Login page template
│   ├── register.html       # Registration page template
│   ├── chat.html           # Chat interface template
│   ├── inbox.html          # Inbox page template
│   ├── admin_panel.html    # Admin panel template
│   └── apply_listener.html  # Listener application page template
├── static                  # Static files (CSS, images, etc.)
│   └── style.css           # CSS styles for the application
└── .env                    # Environment variables (e.g., OpenAI API key)
```

## Setup Instructions
1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd safe-space-app
   ```

2. **Create a virtual environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. **Run the application**:
   ```
   python app.py
   ```

## Usage
- Navigate to `http://127.0.0.1:5000` in your web browser to access the application.
- Users can register, log in, and chat with a bot or listeners.
- Admins can manage listener applications through the admin panel.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License
This project is licensed under the MIT License.