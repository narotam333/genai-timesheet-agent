import subprocess

def main():
    """
    Launch the Streamlit app by running the 'streamlit_app.py' script
    located in the 'timesheet_entry' directory using a subprocess call.
    """
    subprocess.run(["streamlit", "run", "timesheet_entry/streamlit_app.py"])

