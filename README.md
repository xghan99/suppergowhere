# suppergowhere
A web app to help you choose a supper location so that you will not be burdened by surge pricing on your way back!

## How the App Works
We often hesitate about going drinking/having supper till past midnight as there are no public transport options back. Booking a Private Hire Vehicle (GoJek, Grab) is a painful cycle of seeing unreasonable surged prices and being unable to find drivers. This app alleviates your suffering by suggesting locations (based on MRT stations) to indulge in your alcohol/food. The suggestions are ranked based on the **average** number of taxis within a 500m radius. 

All you need to do is input the time and day you are planning to head back home and press 'Go'. The app would then generate the top 5 locations in descending number of taxis within a 500m radius.

*Note: I used the number of taxis as an estimation for the number of Private Hire Vehicles in the area as the live location of Private Hire Vehicles is not publicly available.*

## Website
https://suppergowhere-mvcs7gakxq-as.a.run.app/

## Deployment Instructions
### Prefect Flow
Prerequisites: Created a project and a BigQuery table in Google Cloud. Downloaded Service Account Credentials as a JSON file.
1. Create an account on Prefect Cloud and log in
2. Create a workspace on Prefect Cloud
3. Inside the workspace, go to 'Blocks' > '+' > 'GCP Credentials' > Paste your Service Account Credentials inside and click 'Create' (This step may not be necessary given the way Application Default Credentials work in GCP)
4. Go to your Prefect Cloud Profile > 'Settings' > 'API Keys' > '+' to generate a Prefect Cloud API Key
5. On GCP, create a Cloud VM instance and SSH into it
6. Copy the `flow_script.py` and `requirements.txt` files into the VM instance
7. Run the following commands
```
sudo apt-get update
sudo apt-get install python3.10
pip install -r requirements.txt
```
8. Log onto Prefect Cloud in your VM instance (follow the instructions on screen):
```
prefect cloud login
```
9. Run the following code to build your Prefect Deployment:
```
prefect deployment build -n <DEPLOYMENT NAME> -p default-agent-pool -q default flow_script.py:main_flow
```
10. Run the following code to apply the Deployment
```
prefect deployment apply <DEPLOYMENT NAME>-deployment.yaml
```
11. Go to your Prefect Cloud Dashboard on your main computer and set the schedule for the deployment. You can press 'Quick Run' to test out the flow
12. Run ```nohup prefect agent start --pool default-agent-pool >/dev/null 2>&1``` in your VM instance. This starts the prefect agent which would run the flow code according to the schedule. `nohup` keeps the process running even after you close the SSH instance. `>/dev/null 2>&1` would ensure that the process would not generate `nohup.out` logs


### Dash App


## References
Live Taxi Location Data: https://beta.data.gov.sg/datasets/352/view
MRT Coordinates: https://www.kaggle.com/datasets/yxlee245/singapore-train-station-coordinates

## Acknowledgements
Ivan (https://github.com/ivankqw) for helping out with the front-end design and code organisation.

