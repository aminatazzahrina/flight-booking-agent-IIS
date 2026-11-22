import json

import streamlit as st
from google import genai
from google.genai import types

from flight_search import search_flights


st.set_page_config(page_title="Plan your flight", page_icon="✈️")
st.title("✈️ Plan your flight")
st.write("Tell me where and when you’d like to travel. I’ll help compare options.")

MODEL = "gemini-3.6-flash"
with st.sidebar:
    st.subheader("Offline preview")
    st.caption("Uses sample data only. This does not call Gemini.")

    if st.button("Preview complete request"):
        request = {
            "origin": "Birmingham",
            "destination": "Kuala Lumpur",
            "departure_date": "10 December 2026",
            "return_date": "20 December 2026",
            "budget_gbp": 700,
            "max_stops": 1,
        }
        st.session_state["flight_search_result"] = search_flights(request)
        st.session_state["selected_flight"] = None
        st.session_state["passenger_step"] = False
        st.session_state["passenger_declined"] = False

    if st.button("Preview incomplete request"):
        request = {
            "destination": "Malaysia",
            "departure_date": "sometime in December",
        }
        st.session_state["flight_search_result"] = search_flights(request)
        st.session_state["selected_flight"] = None
        st.session_state["passenger_step"] = False
        st.session_state["passenger_declined"] = False

def search_flights_tool(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    budget_gbp: float,
    max_stops: int,
) -> str:
    """Search sample flights using the user's confirmed trip details."""
    request = {
        "origin": origin,
        "destination": destination,
        "departure_date": departure_date,
        "return_date": return_date,
        "budget_gbp": budget_gbp,
        "max_stops": max_stops,
    }

    result = search_flights(request)
    st.session_state["flight_search_result"] = result
    return json.dumps(result)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "gemini_chat" not in st.session_state:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)

        st.session_state.gemini_chat = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a friendly flight-planning assistant. Collect the "
                    "departure city, specific destination city, exact departure "
                    "and return dates, maximum budget in GBP, and maximum number "
                    "of stops. Never guess missing details. If details are "
                    "missing or vague, ask for only those details in one short, "
                    "natural message. Once all six details are provided, you "
                    "MUST call search_flights_tool before saying whether flights "
                    "are available. After the tool returns, give one short "
                    "sentence saying how many sample options were found. Do not "
                    "list the flights because the app displays them below. Never "
                    "invent confidence percentages or claim sample data is live."
                ),
                tools=[search_flights_tool],
            ),
        )
    except Exception as error:
        st.error(f"Could not connect to Gemini: {error}")
        st.stop()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Where would you like to fly?"):
    # Clear the previous search and choice before handling a new message.
    st.session_state["flight_search_result"] = None
    st.session_state["selected_flight"] = None
    st.session_state["passenger_step"] = False
    st.session_state["passenger_declined"] = False

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Checking your trip details..."):
            try:
                response = st.session_state.gemini_chat.send_message(prompt)
                reply = response.text or "Could you rephrase that for me?"
            except Exception as error:
                reply = f"Gemini request failed: {error}"

        # Use a short, consistent reply when the search tool found options.
        result = st.session_state.get("flight_search_result")

        if result and result.get("status") == "results":
            count = len(result.get("flights", []))
            reply = (
                f"I found {count} sample options. "
                "They’re below, sorted by price."
            )
        elif result and result.get("status") == "no_matches":
            reply = (
                "I couldn’t find a sample option that fits those limits. "
                "You can adjust them and try again."
            )

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})


result = st.session_state.get("flight_search_result")

if result and result.get("status") == "results":
    flights = result.get("flights", [])
    criteria = result.get("criteria", {})

    st.subheader("Your options")
    st.caption(
        f"All options fit your limits · Sorted by price · "
        f"Up to £{criteria.get('budget_gbp', 0):g} · "
        f"Max {criteria.get('max_stops', 0)} stop(s) · Simulated data"
    )

    cheapest = min(flights, key=lambda flight: flight["price_gbp"])
    fastest = min(flights, key=lambda flight: flight["duration_hours"])

    for rank, flight in enumerate(flights, start=1):
        price_difference = flight["price_gbp"] - cheapest["price_gbp"]
        hours_saved = cheapest["duration_hours"] - flight["duration_hours"]

        if (
            flight["option"] == cheapest["option"]
            and flight["option"] == fastest["option"]
        ):
            reason = "Lowest fare and shortest trip."
        elif flight["option"] == cheapest["option"]:
            reason = "Lowest fare among options that meet your limits."
        elif flight["option"] == fastest["option"]:
            reason = (
                f"Shortest trip; £{price_difference} more than the lowest fare, "
                f"saving {hours_saved} hours."
            )
        else:
            reason = (
                f"£{price_difference} more than the lowest fare, "
                f"saving {hours_saved} hours."
            )

        st.markdown(
            f"**{rank}. {flight['label']} — {flight['airline']}**  \n"
            f"£{flight['price_gbp']} · "
            f"{flight['duration_hours']}h · "
            f"{flight['stops']} stop(s)  \n"
            f"_{reason}_"
        )

    st.caption("Choose an option to continue.")

    labels = [
        f"{rank}. {flight['label']} — £{flight['price_gbp']}"
        for rank, flight in enumerate(flights, start=1)
    ]

    selected_label = st.radio(
        "Choose a flight",
        labels,
        label_visibility="collapsed",
    )

    if st.button("Choose this flight"):
        selected_index = labels.index(selected_label)
        st.session_state["selected_flight"] = flights[selected_index]
        st.session_state["passenger_step"] = False
        st.session_state["passenger_declined"] = False

    selected_flight = st.session_state.get("selected_flight")

    if selected_flight:
        st.success(
            f"You chose {selected_flight['label']} "
            f"at £{selected_flight['price_gbp']}."
        )
        st.info("Would you like to continue to the passenger-details step?")

        continue_col, stop_col = st.columns(2)

        with continue_col:
            if st.button("Continue"):
                st.session_state["passenger_step"] = True
                st.session_state["passenger_declined"] = False

        with stop_col:
            if st.button("Stop here"):
                st.session_state["passenger_step"] = False
                st.session_state["passenger_declined"] = True

        if st.session_state.get("passenger_declined"):
            st.caption("Stopped here. No booking or payment has taken place.")

        if st.session_state.get("passenger_step"):
            st.subheader("Passenger details — demo screen")
            st.caption(
                "These are disabled placeholders. The prototype does not "
                "collect passenger information."
            )
            st.text_input(
                "Passenger full name",
                placeholder="Not collected in this prototype",
                disabled=True,
            )
            st.text_input(
                "Passport details",
                placeholder="Not collected in this prototype",
                disabled=True,
            )
            st.caption("Payment would require a separate confirmation.")
elif result and result.get("status") == "needs_clarification":
    missing = ", ".join(result.get("missing", []))
    st.info(f"Before searching, please provide: {missing}.")