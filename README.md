# smart_irrg

Setup Instructions:
1. Install Required Packages
Navigate to the project directory and install all required dependencies listed in requirements.txt.
        pip install -r requirements.txt

2. Start Virtual Environment
Activate the virtual environment (make sure you've already created it using python3 -m venv venv if it doesn’t exist yet).
        source venv/bin/activate

3. Start the Project (Run FastAPI Server)
Use Uvicorn to run the FastAPI app. This will start the server with hot-reload enabled.
        uvicorn main:app --reload

Simulate Moisture Data:
4. Run the Simulation Script
This will simulate sending soil moisture readings to the API.
        python3 mois.py
        
Make sure the MAC address used in the script matches the one registered during sign-up. This is crucial for proper identification of the device

Check API Response:
After running the simulation, check the API response in your terminal or API logs. It will show the status, such as whether the pump is turned on or off.

System Concept:
The system uses a switch and a pump to manage irrigation automatically.
If the switch is ON and the pump is in auto mode, the system will stop the pump once the soil has enough moisture.
If the switch is OFF (manual mode), the pump will continue running as long as the moisture level remains low, regardless of auto conditions. 
