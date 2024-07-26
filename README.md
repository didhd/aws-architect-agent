# AWS Architect Agent

This project uses LangGraph, ChatGPT, and diagram-as-code to generate AWS architecture diagrams based on user queries. It includes a Streamlit-based frontend for easy interaction.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/aws-architect-agent.git
   cd aws-architect-agent
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key:
   Create a `.env` file in the project root and add your API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

To run the Streamlit app:

```
streamlit run src/app.py
```

Then open your web browser and go to `http://localhost:8501`.

## Running Tests

To run the unit tests:

```
python -m unittest discover tests
```

## License

MIT