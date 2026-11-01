from fastapi import HTTPException
from models.vehicle_dao import VehicleDAO


STATUS_MAP = {
    "active": 1,
    "inactive": 2,
}


class VehicleController:

    @staticmethod
    def get_vehicles(conn, limit=20, offset=0, status=None, plate_number=None):

        status_id = None

        if status is not None:

            normalized_status = status.strip().lower()

            if normalized_status in STATUS_MAP:
                status_id = STATUS_MAP[normalized_status]

            elif normalized_status.isdigit():
                status_id = int(normalized_status)

            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid query parameter values",
                )

        return VehicleDAO.get_all(
            conn,
            limit,
            offset,
            status_id,
            plate_number,
        )


    @staticmethod
    def get_vehicle_by_id(conn, vehicle_id: int):

        if vehicle_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="Vehicle not found",
            )

        vehicle = VehicleDAO.get_by_id(conn, vehicle_id)

        if vehicle is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found",
            )

        return vehicle