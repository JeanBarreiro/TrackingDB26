from fastapi import HTTPException
from models.driver_dao import DriverDAO

class DriverController:

    @staticmethod
    def get_drivers(conn, limit, offset, name, license_number):

        if limit < 0 or offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameter values."
            )

        return DriverDAO.get_drivers(
            conn,
            limit,
            offset,
            name,
            license_number,
        )

    @staticmethod
    def get_driver(conn, driver_id):

        if driver_id <= 0:
            raise HTTPException(
                status_code=404,
                detail="driver_id does not exist."
            )

        driver = DriverDAO.get_by_id(conn, driver_id)

        if driver is None:
            raise HTTPException(
                status_code=404,
                detail="driver_id does not exist."
            )

        return driver