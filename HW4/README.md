# CrewAI Research Agents with Voice I/O

## Description

This project creates an intelligent crew of AI agents that assists with company research for networking purposes. Users can provide input via **voice or text** and receive comprehensive research results, including **audio output** of the final company rankings.

### Key Features
- **Multi-Agent Research System**: Three specialized agents work together to research companies
- **Voice Input/Output**: Speak your research parameters and hear the results aloud
- **Comprehensive Analysis**: Industry mapping, company discovery, and intelligent ranking
- **Flexible Input Methods**: Voice recording or traditional text input
- **Audio Results**: Final company rankings are spoken aloud and saved as audio files

### How It Works
1. **Input**: Provide industry, region, and time window (via voice or text)
2. **Research**: Three AI agents collaborate to:
   - Map industry sub-sectors
   - Find and analyze companies
   - Rank companies by importance and stage
3. **Output**: Receive ranked company list with audio narration

# AI usage notice
AI tools like ChatGPT and Cursor have been used to produce this work. Specifically, ChatGPT was used to refine descriptions of AI agent crew (configuration, agents and tasks), whereas Cursor was used to debug the code and add certain features

# Learnings and limitations

**Learnings:**
* I have no technical backgrounds whatsoever, so while doing this exercies, I learned how to use GitHub, typical file structures (readme, utils, env, etc.) and how to code with Cursor
* I found the CrewAI course on DeepLearning.ai (https://learn.deeplearning.ai/courses/multi-ai-agent-systems-with-crewai) particularly useful to understand the way CrewAI works
* I was able to autonomously run a crew of agents that helps me to identify importnat companies for networking outreach

**Limitations**
* I found that precision level of Agent/Tasks description significantly affects the output -- to the point that a longer and more detailed descripton can actually make results worse
* Output can be very fuzzy and uncertain -- during industry research the crew ommited important companies or highed unimportant ones higher then needed, sometimes output was completely empty
* I was surprised by how slow the Agent Crew is and how many Serper requests they do -- up to 10 per run
* API usage costs should be closely monitored on OpenAI / Serper dashboards, costs add up pretty quickly (~10 cents per run for in OpenAI costs only) 

# Technical notes

## Installation & Setup

### Prerequisites
- Python >=3.10 <3.14
- OpenAI API key with access to GPT models, Whisper, and TTS APIs
- Serper API key for web search functionality

### Quick Start

1. **Clone or download this project**

2. **Install dependencies**:
```bash
pip install -r Requirements.txt
```

3. **Set up environment variables** (see API Configuration section below)

4. **Run the notebook**:
   - Open `Crewai Research Agents.ipynb` in Jupyter
   - Execute cells in order
   - Use voice input for a hands-free experience!

### Dependencies

The project uses these key libraries:
- `crewai>=0.28.8` - Multi-agent AI framework
- `openai>=1.0.0` - OpenAI API client (GPT, Whisper, TTS)
- `ipywidgets>=8.0.0` - Jupyter notebook widgets
- `pydub>=0.25.1` - Audio processing
- `python-dotenv` - Environment variable management

## API Configuration

### Required API Keys

**OpenAI API Key** (Required for GPT, Whisper, and TTS):
- Go to [OpenAI API Keys](https://platform.openai.com/settings/organization/api-keys)
- Create a new secret key
- **Important**: Add credits to your account (costs ~$0.10 per research run)
- **Required APIs**: GPT models, Whisper (speech-to-text), TTS (text-to-speech)

**Serper API Key** (Required for web search):
- Go to [Serper API Keys](http://serper.dev/api-keys)
- Create a new secret key
- Free tier available with limited requests

### Environment Setup

1. **Create a `.env` file** in the project root:
```bash
# .env file
OPENAI_API_KEY=sk-your-openai-key-here
SERPER_API_KEY=your-serper-key-here
OPENAI_MODEL_NAME=gpt-4o-mini
```

2. **Install python-dotenv** (if not already installed):
```bash
pip install python-dotenv
```

3. **Load environment variables** in your notebook:
```python
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path.cwd() / ".env")
```

## Voice I/O Features

### Voice Input (Speech-to-Text)
- **Supported formats**: MP3, WAV, M4A, OGG, FLAC
- **Language**: English (forced to prevent translation issues)
- **Process**: Record audio → Upload file → Automatic transcription
- **Fallback**: If voice input fails, automatically switches to text input

### Voice Output (Text-to-Speech)
- **Voice**: OpenAI's "alloy" voice (natural-sounding)
- **Auto-play**: Results are spoken aloud immediately
- **File saving**: Audio files saved with timestamps (e.g., `research_results_20241220_143022.mp3`)
- **Smart summarization**: Long results are intelligently summarized for TTS limits

### Usage Example
1. Choose "Voice input" when prompted
2. Record your industry/region/time window on your phone/computer
3. Upload the audio file when prompted
4. Listen to the spoken results and find the saved audio file

## Project Structure

```
HW4/
├── Crewai Research Agents.ipynb    # Main notebook with voice I/O
├── utils.py                        # Voice utilities and API helpers
├── Requirements.txt                # Python dependencies
├── .env                           # API keys (create this)
├── Voice_Implementation_Summary.md # Technical implementation details
└── README.md                      # This file
```

## Troubleshooting

### Common Issues

**Voice input not working**:
- Ensure audio file is in supported format (MP3, WAV, etc.)
- Check that OpenAI API key has Whisper access
- Try text input as fallback

**Audio not playing**:
- Check browser audio permissions
- Verify OpenAI TTS API access
- Audio files are saved locally for manual playback

**API errors**:
- Verify API keys are correct in `.env` file
- Check OpenAI account has sufficient credits
- Ensure Serper API key is valid

**Recursion errors**:
- Use the latest voice input cell (Cell 17)
- Avoid running multiple input cells simultaneously

## Cost Considerations

### API Usage Costs
- **OpenAI**: ~$0.10 per research run (GPT + Whisper + TTS)
- **Serper**: Free tier available, paid plans for heavy usage
- **Monitoring**: Check your API dashboards regularly

### Optimization Tips
- Use `gpt-4o-mini` for lower costs while maintaining quality
- Limit `TOP_N_OVERALL` to reduce processing time
- Consider caching results for repeated queries

## Advanced Configuration

### Customizing Research Parameters
```python
# In the notebook, modify these variables:
TOP_N_OVERALL = 20  # Reduce for faster results
DEFAULT_REGION = "United States"  # Your preferred region
DEFAULT_TIME_WINDOW = "last 12 months"  # Your preferred timeframe
```

### Voice Input Customization
- Modify `utils.py` to change voice settings
- Adjust TTS voice (alloy, echo, fable, onyx, nova, shimmer)
- Customize audio file naming and storage location

## Support & Resources

- **Technical Details**: See `Voice_Implementation_Summary.md` for implementation specifics
- **CrewAI Documentation**: [Official CrewAI Docs](https://docs.crewai.com/)
- **OpenAI API Docs**: [OpenAI Platform](https://platform.openai.com/docs)
- **Issues**: Check troubleshooting section above or create an issue

---

*This project demonstrates the power of multi-agent AI systems combined with voice interfaces for practical business research applications.*
