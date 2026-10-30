from fastapi import FastAPI

from routes.vehicle_routes import router
from etl import ETL_runner

app = FastAPI(title="TrackingDB26 API")
app.include_router(router)



#DONT RUN AGAIN -------------------
#if __name__ == "__main__":
    #run_ETL()




