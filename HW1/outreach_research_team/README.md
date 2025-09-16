# OutreachResearchTeam Crew

Welcome to the OutreachResearchTeam Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

Install python-dotenv in the same environment as your notebook:
```python
from pathlib import Path
from dotenv import load_dotenv

# point to the .env file. Adjust the path if your .env is elsewhere
load_dotenv(dotenv_path=Path.cwd() / ".env")   # loads into os.environ
```