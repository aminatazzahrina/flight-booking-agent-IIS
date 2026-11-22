# Flight Booking Assistant

Prose word count: 309

## Status
This Streamlit prototype demonstrates a conversational flight-search assistant. Gemini 3.6 Flash asks for missing trip details and calls a local Python search function. The app filters and ranks invented flight offers, explains why each is shown, lets the user choose one, and asks before showing disabled passenger-details placeholders. It does not use live flight data, book flights, collect passenger details, or process payments. Offline preview buttons demonstrate complete and incomplete requests without making Gemini API requests.

## Technology
- Python 3 runs the app and mock search logic.
- Streamlit provides the chat interface and controls.
- Gemini 3.6 Flash through the Google Gen AI Python SDK interprets requests and calls the search function.
- `flight_search.py` contains invented offers, validates details, filters by budget and stops, and ranks by price.

## Run
Install Python 3 and the packages below. A Gemini API key is needed to launch the app. Add your own key to `.streamlit/secrets.toml`. Never commit that file or share the key. Offline preview buttons do not make Gemini API requests.

```powershell
python -m pip install streamlit google-genai
python -m streamlit run app.py

Screenshots
- [Incomplete request](screenshots/incomplete-request.png)
- [Ranked flight options](screenshots/ranked-options.png)
- [Permission and passenger-details placeholder](screenshots/permission-step.png)
Development record
- Created a Streamlit interface and local sample-flight search.
- Added clarification for missing details and vague dates.
- Connected Gemini function calling and added ranked labels, explanations, flight selection, and a consent step.
- Switched to Gemini 3.6 Flash after repeated service-unavailable errors with the earlier model.
- Added offline previews so the interaction can be inspected without Gemini API requests. Checked both example requests, ranking, selection, and consent flow.
AI assistance
ChatGPT helped plan, write, revise, and debug the Python prototype and documentation. Gemini 3.6 Flash is the conversational model used by the app. I reviewed and changed suggested code, checked the complete and incomplete examples, and verified that sample fares and simulated steps are clearly labelled.