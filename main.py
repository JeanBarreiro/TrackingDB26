from fastapi import FastAPI

from routes.vehicle_routes import router as vehicle_router
from routes.driver_routes import router as driver_router

from etl import ETL_runner

app = FastAPI(title="TrackingDB26 API")
app.include_router(vehicle_router)
app.include_router(driver_router)



#DONT RUN AGAIN -------------------
#if __name__ == "__main__":
    #run_ETL()




