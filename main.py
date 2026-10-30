from fastapi import FastAPI

from routes import vehicle_routes
from etl import ETL_runner

app = FastAPI()
app.include_router(vehicle_routes())



#DONT RUN AGAIN -------------------
#if __name__ == "__main__":
    #run_ETL()




