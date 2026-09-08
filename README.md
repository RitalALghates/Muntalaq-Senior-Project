Muntalaq – AI-Powered Academic Mentorship & Learning Platform
Connecting university students with graduates and AI to create a more personalized academic journey.
Muntalaq is an AI-powered academic mentorship and learning platform developed as a Senior Project in Software Engineering at the University of Jeddah.
The platform aims to help university students access academic guidance, connect with graduates, discover relevant learning resources, and receive personalized recommendations based on their academic needs and interests.
________________________________________
Problem
University students may face difficulties when looking for:
•	Accessible academic guidance
•	Suitable mentors and graduates to connect with
•	Relevant learning resources
•	Personalized academic recommendations
•	A centralized environment for academic communication and support
Muntalaq was designed to bring these services together in one platform.
________________________________________
Solution
Muntalaq combines AI-powered assistance, academic mentorship, interactive learning content, and community features into a single platform.
Students can interact with graduates, receive AI-based academic support, access mini-courses, communicate with other users, and track their academic activities.
________________________________________
Key Features
AI-Powered Features
•	Personalized academic recommendations based on student needs and interests.
•	AI chatbot for academic guidance and assistance.
•	Integration with the OpenAI API.
Mentorship
•	Connect university students with graduates.
•	Support academic guidance and knowledge sharing.
•	Allow students to evaluate their mentors.
Learning
•	Interactive mini-courses.
•	Academic learning resources.
•	Progress dashboard to track academic activities.
Community & Communication
•	Academic community for students and graduates.
•	One-to-one messaging.
•	Group chat functionality.
•	Notifications for relevant activities and interactions.
________________________________________
Technologies
Backend
•	Python
•	Flask
•	SQLite
Frontend
•	HTML5
•	CSS3
•	JavaScript
AI & APIs
•	OpenAI API
•	REST APIs
•	OpenAI SDK
Testing
•	Unit Testing
•	Integration Testing
•	System Testing
•	Acceptance Testing
Development Tools
•	Git
•	GitHub
•	Visual Studio Code
________________________________________
Project Architecture
The application follows a web-based architecture consisting of:
Frontend
HTML5 + CSS3 + JavaScript
          │
          ▼
       Flask
       Backend
          │
    ┌─────┴─────┐
    ▼           ▼
 SQLite      OpenAI API
 Database     AI Services
________________________________________
Project Structure
Muntalaq-Senior-Project/
│
├── static/              # CSS, JavaScript, and static assets
├── templates/           # HTML templates
├── tests/               # Automated tests
├── app.py               # Flask application
├── requirements.txt     # Python dependencies
├── package-lock.json    # Node.js dependency lock file
├── CHANGES.md           # Project changes and updates
├── .gitignore           # Ignored files and sensitive data
└── README.md            # Project documentation
Note: Environment variables such as API keys and secret keys are stored locally in a .env file and are not committed to the repository.
________________________________________
Getting Started
Prerequisites
Make sure you have the following installed:
•	Python 3.x
•	pip
•	Git
1. Clone the repository
git clone https://github.com/YOUR-USERNAME/Muntalaq-Senior-Project.git
cd Muntalaq-Senior-Project
2. Create a virtual environment
python -m venv venv
3. Activate the virtual environment
Windows:
venv\Scripts\activate
4. Install dependencies
pip install -r requirements.txt
5. Configure environment variables
Create a .env file in the project root:
OPENAI_API_KEY=your_openai_api_key_here
FLASK_SECRET_KEY=your_flask_secret_key_here
Replace the placeholder values with your own credentials.
Never commit your .env file or API keys to GitHub.
6. Run the application
python app.py
Then open the local URL displayed in the terminal.
________________________________________
Demo
[View Muntalaq Demo](https://drive.google.com/file/d/1eQa1G0HIGm6MrwtKyTz0KMtT_DYFjYuZ/view?usp=drive_link)  
________________________________________
Testing
The system was tested through multiple levels:
•	Unit Testing – Testing individual components and functions.
•	Integration Testing – Testing interactions between system components.
•	System Testing – Testing the complete application and its major modules.
•	Acceptance Testing – Evaluating the system against the intended requirements and user needs.
Testing covered major platform modules and core functionality to improve reliability and usability.
________________________________________
Development Approach
The project was developed using an Agile development approach.
The development process included:
1.	Requirements gathering
2.	Requirements analysis
3.	System design
4.	Implementation
5.	Testing
6.	Evaluation
Requirements were gathered through surveys involving university students and graduates to better understand their academic support and mentorship needs.
________________________________________
Academic Project
Muntalaq was developed as a Senior Project in Software Engineering at the University of Jeddah.
The project brought together concepts from:
•	Software Engineering
•	Web Development
•	Artificial Intelligence
•	Database Systems
•	Software Testing
•	REST APIs
________________________________________
Authors
Developed as a Senior Project in Software Engineering at the University of Jeddah.
________________________________________
Project Vision
Muntalaq – Connecting Students, Graduates, and AI for a Better Academic Journey.


