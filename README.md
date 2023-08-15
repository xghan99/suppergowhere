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
6. Copy the `flow_script.py`, `requirements.txt` and `mrt_lrt_data.csv` files into the VM instance
7. Run the following commands
```
sudo apt-get update
sudo apt-get install python3.10
sudo apt-get install python3-pip
pip install -r requirements.txt
```
7a. Change your PATH variable as required
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


### Deploying Dash App using Google Cloud Run
Prerequisites: 2 Bigquery Tables (one for number of taxis per MRT stations and one for caching supper recommendations), Secret Variable created on Google Cloud for your Maps API Key
1. Ensure that you are in the main directory
2. Run the following Docker commands to build a Docker image and push it onto Google Container Registry: 
```
docker build -f Dockerfile -t gcr.io/{PROJECT_ID}/{IMAGE}:{TAG} .
docker push gcr.io/{PROJECT_ID}/{IMAGE}:{TAG}
```
3.Then run the following command to deploy the web app:
```
gcloud run deploy {name} \
      --image=gcr.io/{PROJECT_ID}/{IMAGE}:{TAG} \
      --platform=managed \
      --region={your_region} \  # GCP region
      --timeout=60 \          # Request timeout (max 900 secs)
      --concurrency=80 \      # Max request concurrency (default 80)
      --cpu=1 \               # Instance number of CPU's (default 1)
      --memory=256Mi \        # Instance memory (default 256Mi)
      --max-instances=10  \   # Max instances
      --allow-unauthenticated \ # Make service publicly available
      --update-secrets=maps_api_key={MAPS_API_KEY_SECRET}:{VERSION} \
      --update-env-vars local_testing=False
```

### Deploying Locally
1. Run the following Docker Commands to build the image and run the container
```
docker build -t <image-name> -f ./Dockerfile-local --build-arg credentials_file_path=<credentials file> .
docker run --env maps_api_key=<maps-api-key> -p 8080:8080 <image-name>
```
2. Go to http://localhost:8080/


## References
<li> Live Taxi Location Data: https://beta.data.gov.sg/datasets/352/view
<li> MRT Coordinates: https://www.kaggle.com/datasets/yxlee245/singapore-train-station-coordinates
<li> Deploying Dash App on Google Cloud Run: https://medium.com/kunder/deploying-dash-to-cloud-run-5-minutes-c026eeea46d4

## Acknowledgements
Ivan (https://github.com/ivankqw) for helping out with the front-end design and code organisation.

