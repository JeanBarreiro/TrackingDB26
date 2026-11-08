from fastapi import APIRouter, Query
from controllers import vehicle_assignment_controller
from controllers.validation import parse_id

router = APIRouter(
    prefix="/api/v1/vehicle-assignments",
    tags=["Vehicle Assignments"]
)

@router.post("", status_code=201)
def create_vehicle_assignment(payload: dict):
    return vehicle_assignment_controller.create_vehicle_assignment(
        payload
    )

@router.get("")
def get_vehicle_assignments(
    limit: str = Query("20"),
    offset: str = Query("0"),
    vehicle_id: str | None = Query(None),
    driver_id: str | None = Query(None),
    active: str | None = Query(None)
):
    return vehicle_assignment_controller.get_vehicle_assignments(
        limit,
        offset,
        vehicle_id,
        driver_id,
        active
    )


@router.get("/{assignment_id}")
def get_vehicle_assignment(assignment_id: str):
    assignment_id = parse_id(assignment_id, "assignment_id")

    return vehicle_assignment_controller.get_vehicle_assignment(
        assignment_id
    )

@router.put("/{assignment_id}")
def update_vehicle_assignment(
    assignment_id: str,
    payload: dict
):
    assignment_id = parse_id(assignment_id, "assignment_id")

    return vehicle_assignment_controller.update_vehicle_assignment(
        assignment_id,
        payload
    )

@router.delete("/{assignment_id}")
def delete_vehicle_assignment(assignment_id: str):
    assignment_id = parse_id(assignment_id, "assignment_id")

    return vehicle_assignment_controller.delete_vehicle_assignment(
        assignment_id
    )

