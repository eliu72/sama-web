# 💻 Using the Website

URL: https://sama-web-app.uc.r.appspot.com/

# 🛠️ Development

## Requirements

- Install 'Allow CORS: Access-Control-Allow-origin' chrome extension and toggle on to allow CORS for development purposes.
- If testing the backend locally as well, replace 'https://backend-dot-sama-web-app.uc.r.appspot.com/submit' with 'http://localhost:5000/submit' in App.js

## Starting the Local Server: 

Run the command: `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

# 📤 Deployment

## Prepare for Deployment

1. Ensure the axios requests points to the correct backend service ('https://backend-dot-sama-web-app.uc.r.appspot.com/submit')
2. The /deploy directory should contain your app.yaml which specifies the config for App Engine
3. Have the Google Cloud CLI (gcloud) installed on your local device: https://cloud.google.com/sdk/docs/install
4. Delete ALL old Docker images in the Container Registry: https://console.cloud.google.com/gcr/images/sama-web-app?project=sama-web-app (This step is needed because of the rule to delete old artifacts)

## Building the Application

Run the command: `npm run build`

Builds the app for production to the `deploy/build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

## Deploying to App Engine

1. Go to the deploy folder: `cd deploy`
2. Deploy your build to App Engine: `gcloud app deploy`
3. Delete all gcloud storage artifacts to avoid charges: `gcloud storage rm --recursive gs://staging.sama-web-app.appspot.com/ ; gcloud storage rm --recursive gs://sama-web-app.appspot.com/ ;  gcloud storage rm --recursive gs://us.artifacts.sama-web-app.appspot.com`

Note: Built container images are stored in the app-engine folder in Container Registry.\
Once deployment is complete, App Engine no longer needs the container images.\
To avoid reaching your storage quota, you can safely delete any images you don't need. 

Reference: https://cloud.google.com/appengine/docs/standard/testing-and-deploying-your-app#managing_build_images

Google automatically creates multi-region US buckets when artifacts are deployed despite GAE being set up with a single region.\
There is no current solution around this issue besides deleting all artifacts after deployment.

Reference: https://stackoverflow.com/questions/62582129/multi-region-cloud-storage-charges

# ⚙️ Troubleshooting on Production Environment

Visit Google Cloud Logging to see all logs: https://console.cloud.google.com/logs/query?project=sama-web-app

Can add filters to search for specify errors:
- Filter for sama-web-app project applications
- Filter for GAE applications
- Filter for log type (INFO, ERROR, etc)
- Filter for time  period